# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS dependencies
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY backend/requirements-runtime.txt ./requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

FROM python:3.12-slim-bookworm AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN groupadd --system researchai && useradd --system --gid researchai --create-home researchai
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=researchai:researchai backend/gateway ./backend/gateway
COPY --chown=researchai:researchai backend/shared ./backend/shared
COPY --chown=researchai:researchai backend/services ./backend/services
USER researchai
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).close()"]
CMD ["python", "-m", "uvicorn", "backend.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
