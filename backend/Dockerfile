# Pinned base image; runs as non-root per CLAUDE.md hard requirement 9.
# Build context is the repo root (see docker-compose.yml) so this can also
# pip-install the mlcore package from ml/ — the frozen import seam
# (docs/INTEGRATION.md Seam 1). backend/ never vendors or copies mlcore's
# source directly; it only depends on the installed package.
FROM python:3.12.8-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ml ./ml
RUN pip install --no-cache-dir -r ml/requirements.txt && \
    pip install --no-cache-dir --no-deps -e ./ml

COPY backend/app ./app

RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
