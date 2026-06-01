FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

ARG MINER_URL=https://pearlhash.xyz/downloads/pearl-miner-v11

ENV DEBIAN_FRONTEND=noninteractive \
    MINER_PATH=/opt/pearl-miner \
    PEARLHASH_POOL_HOST=129.226.55.135:9000 \
    PEARLHASH_WALLET=prl1pw6q2dkd5zdkf3agvfyph6u0acyg7hs7aw9klxcv5ksc5s27r3gmq5yz7yt \
    PEARLHASH_WORKER=worker2

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libgomp1 \
        tini && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "$MINER_URL" -o "$MINER_PATH" && \
    chmod +x "$MINER_PATH"

COPY docker/entrypoint.sh /usr/local/bin/pearlhash-entrypoint
RUN chmod +x /usr/local/bin/pearlhash-entrypoint

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/pearlhash-entrypoint"]
