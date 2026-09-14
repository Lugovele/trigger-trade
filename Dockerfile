FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRIGGERTRADE_DASHBOARD_HOST=0.0.0.0 \
    TRIGGERTRADE_DASHBOARD_PORT=8765 \
    TRIGGERTRADE_RUNTIME_DB_PATH=/app/runtime/triggertrade_paper.sqlite3

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir . \
    && mkdir -p /app/runtime

VOLUME ["/app/runtime"]

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/healthz', timeout=5).read()"

CMD ["python", "-m", "triggertrade.dashboard"]
