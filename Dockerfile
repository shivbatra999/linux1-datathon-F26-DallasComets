FROM python:3.11-slim-trixie AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cargo pkg-config libssl-dev libffi-dev cmake git gfortran libopenblas-dev liblapack-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch 0.16.0 \
    https://github.com/open-quantum-safe/liboqs.git /src/liboqs \
    && cmake -S /src/liboqs -B /src/liboqs/build \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=ON \
        -DOQS_BUILD_ONLY_LIB=ON \
        -DOQS_MINIMAL_BUILD=KEM_ml_kem_768 \
        -DCMAKE_INSTALL_PREFIX=/opt/liboqs \
        -DCMAKE_INSTALL_LIBDIR=lib \
    && cmake --build /src/liboqs/build --parallel 2 \
    && cmake --install /src/liboqs/build

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim-trixie

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3t64 libffi8 ca-certificates libopenblas0-pthread liblapack3 libgfortran5 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/liboqs /opt/liboqs

ENV OQS_INSTALL_PATH=/opt/liboqs \
    LD_LIBRARY_PATH=/opt/liboqs/lib \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY --from=build /wheels /wheels

RUN pip install --no-cache-dir --no-index /wheels/* \
    && rm -rf /wheels \
    && useradd --create-home --uid 1000 app

COPY backend ./backend
COPY frontend ./frontend

USER app

RUN python -c "import oqs; assert 'ML-KEM-768' in oqs.get_enabled_kem_mechanisms()"

EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
