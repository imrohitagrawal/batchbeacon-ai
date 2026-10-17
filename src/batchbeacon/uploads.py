"""Bounded still-image decoding; output bytes are the retained model input."""

from io import BytesIO
from typing import Annotated, Literal, Self

from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import Field, model_validator

from batchbeacon.contracts import Record

Positive = Annotated[int, Field(gt=0)]


class UploadPolicy(Record):
    max_images: Annotated[int, Field(ge=1, le=2)] = 2
    max_image_bytes: Annotated[int, Field(gt=0, le=5 * 1024 * 1024)] = 5 * 1024 * 1024
    max_image_pixels: Annotated[int, Field(gt=0, le=20_000_000)] = 20_000_000
    max_combined_pixels: Annotated[int, Field(gt=0, le=24_000_000)] = 24_000_000
    multipart_overhead_bytes: Positive = 64 * 1024
    spool_bytes: Positive = 1024 * 1024
    read_deadline_seconds: Positive = 30
    # PNG preserves label text without another lossy JPEG generation.
    output_format: Literal["PNG"] = "PNG"
    png_compress_level: Annotated[int, Field(ge=0, le=9)] = 6
    alpha_matte: tuple[
        Annotated[int, Field(ge=0, le=255)],
        Annotated[int, Field(ge=0, le=255)],
        Annotated[int, Field(ge=0, le=255)],
    ] = (255, 255, 255)

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.max_combined_pixels < self.max_image_pixels:
            raise ValueError("combined pixel allowance must accommodate one image")
        if self.spool_bytes > self.max_image_bytes:
            raise ValueError("spool threshold must fit the image byte allowance")
        return self

    @property
    def max_request_bytes(self) -> int:
        return self.max_images * self.max_image_bytes + self.multipart_overhead_bytes


class InvalidUpload(ValueError):
    pass


class SanitizedImage(Record):
    data: bytes = Field(repr=False)
    width: Positive
    height: Positive
    mime_type: Literal["image/png"] = "image/png"


class _BoundedOutput(BytesIO):
    def __init__(self, limit: int):
        super().__init__()
        self.limit = limit

    def write(self, data: bytes) -> int:
        if self.tell() + len(data) > self.limit:
            raise InvalidUpload("sanitized image exceeds byte allowance")
        return super().write(data)


def sanitize_images(inputs: tuple[bytes, ...], policy: UploadPolicy) -> tuple[SanitizedImage, ...]:
    if not 1 <= len(inputs) <= policy.max_images:
        raise InvalidUpload("choose one or two supported synthetic images")
    dimensions = []
    try:
        # Inspect ALL dimensions before any full decode; never trust MIME or filename.
        for data in inputs:
            if not data or len(data) > policy.max_image_bytes:
                raise InvalidUpload("image exceeds byte allowance or is empty")
            with Image.open(BytesIO(data), formats=("JPEG", "PNG", "WEBP")) as source:
                width, height = source.size
                if width * height > policy.max_image_pixels:
                    raise InvalidUpload("image exceeds pixel allowance")
                if getattr(source, "n_frames", 1) != 1:
                    raise InvalidUpload("only still images are supported")
                dimensions.append((width, height))
                source.verify()
        if sum(w * h for w, h in dimensions) > policy.max_combined_pixels:
            raise InvalidUpload("images exceed combined pixel allowance")
        outputs = []
        for data in inputs:
            with Image.open(BytesIO(data), formats=("JPEG", "PNG", "WEBP")) as source:
                source.load()  # Truncated data fails; global permissive flags are never changed.
                with ImageOps.exif_transpose(source) as oriented:
                    with oriented.convert("RGBA") as rgba:
                        # New pixel-only canvas drops metadata; composite alpha so transparent
                        # black backgrounds cannot obscure otherwise visible black label marks.
                        with Image.new("RGB", rgba.size, policy.alpha_matte) as clean:
                            with rgba.getchannel("A") as alpha:
                                clean.paste(rgba, mask=alpha)
                            with _BoundedOutput(policy.max_image_bytes) as stream:
                                clean.save(
                                    stream,
                                    format=policy.output_format,
                                    compress_level=policy.png_compress_level,
                                )
                                outputs.append(
                                    SanitizedImage(
                                        data=stream.getvalue(),
                                        width=clean.width,
                                        height=clean.height,
                                    )
                                )
        return tuple(outputs)
    except (OSError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise InvalidUpload("image could not be decoded") from exc
