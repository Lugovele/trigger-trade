FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRIGGERTRADE_DASHBOARD_HOST=0.0.0.0 \
    TRIGGERTRADE_DASHBOARD_PORT=8765

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir .
RUN groupadd --system triggertrade \
    && useradd --system --gid triggertrade --home-dir /app --shell /usr/sbin/nologin triggertrade \
    && mkdir -p /app/runtime \
    && chown -R triggertrade:triggertrade /app

USER triggertrade

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -m triggertrade.services.container_health

CMD ["python", "-m", "triggertrade.services.runtime"]
