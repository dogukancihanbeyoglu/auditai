FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

RUN groupadd --system --gid 10001 auditai \
    && useradd --system --uid 10001 --gid auditai --home-dir /app auditai

COPY requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY --chown=auditai:auditai . .
RUN mkdir -p /app/instance && chown -R auditai:auditai /app/instance

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=2", "--threads=4", "--access-logfile=-", "--error-logfile=-", "production:app"]
