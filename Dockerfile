FROM ghcr.io/astral-sh/uv:0.11.18@sha256:917bfe182a68b43bfe73ad69ae013a1259aef1b5b46cef1815419c5b05d7accb AS uv
FROM python:3.12.13-slim-bookworm@sha256:6e13e65c55e33adf203d77ee371cf8bf5d81bd4902ef07565721f46bf44917af
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
