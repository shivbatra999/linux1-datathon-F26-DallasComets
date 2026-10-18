FROM python:3.11-slim-trixie AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cargo pkg-config libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim-trixie
RUN apt-get update && apt-get install -y --no-install-recommends libssl3t64 libffi8 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir --no-index /wheels/* \
    && rm -rf /wheels \
    && useradd --create-home app && mkdir /data && chown app:app /data
COPY backend ./backend
COPY frontend ./frontend
USER app
ENV SIMPLECATER_DB=/data/simplecater.db
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
