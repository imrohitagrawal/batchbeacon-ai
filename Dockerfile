FROM ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 AS uv
FROM python:3.15.0-slim-bookworm@sha256:0e019bbdfb5d9874cb2389f1c2884b64aa2ac97c99960b5bc521cef978c0617d
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA=true
COPY pyproject.toml uv.lock ./
RUN python -c "import subprocess, sys; assert sys.version_info[:3] == (3, 12, 13); assert subprocess.check_output(['uv', '--version'], text=True).split()[:2] == ['uv', '0.11.18']" && uv sync --frozen --no-dev --no-build --no-install-project --python /usr/local/bin/python
COPY src ./src
COPY prototypes/refined/style.css prototypes/refined/mark.svg ./prototypes/refined/
COPY fixtures/synthetic ./fixtures/synthetic
COPY fixtures/sources/sfa-reviewed.json ./fixtures/sources/
COPY fixtures/learning ./fixtures/learning
COPY runtime-assets ./runtime-assets
USER 65532:65532
CMD ["sh", "-c", "exec .venv/bin/uvicorn batchbeacon.runtime:create_app --factory --app-dir src --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-proxy-headers"]
