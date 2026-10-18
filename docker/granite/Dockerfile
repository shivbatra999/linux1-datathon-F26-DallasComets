FROM ubuntu:24.04 AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git cmake pkg-config build-essential libopenblas-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp.git /src
WORKDIR /src
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    -DGGML_NATIVE=OFF -DCMAKE_C_FLAGS=-march=z15 -DCMAKE_CXX_FLAGS=-march=z15 \
    -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS \
    -DBUILD_SHARED_LIBS=OFF -DLLAMA_BUILD_TESTS=OFF \
    && cmake --build build --target llama-server -j 2

FROM ubuntu:26.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl libssl3t64 libopenblas0-pthread libgomp1 \
    python3 python3-numpy python3-tqdm python3-yaml python3-requests \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bin/llama-server /usr/local/bin/llama-server
COPY --from=build /src/gguf-py /opt/gguf-py
ENTRYPOINT ["llama-server"]
