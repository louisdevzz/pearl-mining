# Pearlhash Miner

Pearl mining with Pearlhash. The original Modal scripts are kept, and the
Docker image is intended for SaladCloud Container Engine.

## Quick Start

```bash
pip install modal
modal token set --token-id YOUR_ID --token-secret YOUR_SECRET

# Pearlhash Pool (H100) — pearl-miner-v11
modal deploy akoya_modal.py
modal run akoya_modal.py

# Stop: modal app stop pearlhash-h100-miner

# Pearlhash Pool (A100, legacy binary v8)
modal deploy pearlhash_modal.py
modal run pearlhash_modal.py
```

**Why "Runner terminated"?** `modal run` without deploy + spawn ties the GPU job to your local CLI session. Closing the terminal, Ctrl-C, or disconnecting from the Modal dashboard stops the runner. Use `modal deploy` then `modal run` (spawns in background), or `modal run --detach ...::train`.

## Files

- `akoya_modal.py` — Pearlhash pool miner (H100, pearl-miner-v11)
- `pearlhash_modal.py` — Pearlhash pool miner (A100, pearl-miner-v8)
- `fix_akoya_modal.py` — Akoya pool miner (optional)
- `Dockerfile` — SaladCloud-ready Pearlhash image
- `docker/entrypoint.sh` — launches `pearl-miner-v11` from environment vars

## Wallet

Change `WALLET` in each script.

For Docker/Salad, prefer environment variables instead:

```bash
PEARLHASH_WALLET=prl1...
PEARLHASH_POOL_HOST=129.226.55.135:9000
PEARLHASH_WORKER=worker2
```

## Build Docker Image for SaladCloud

Build the image for Salad's Linux/NVIDIA hosts. On Apple Silicon, keep
`--platform linux/amd64`.

```bash
docker buildx build --platform linux/amd64 -t YOUR_REGISTRY/pearlhash-miner:latest --load .
```

Smoke-test the image without a GPU by checking the miner binary and linked
runtime libraries:

```bash
docker run --rm --platform linux/amd64 --entrypoint /bin/bash YOUR_REGISTRY/pearlhash-miner:latest \
  -lc 'test -x /opt/pearl-miner && ldd /opt/pearl-miner'
```

Push the image to Docker Hub, GHCR, or another registry Salad can pull from:

```bash
docker push YOUR_REGISTRY/pearlhash-miner:latest
```

## Deploy on SaladCloud

Create a SaladCloud Container Group using the pushed image reference. Configure
one GPU per container, set vCPU/RAM/disk for the selected GPU class, and start
with one replica until logs confirm the miner is connected.

Set environment variables in Salad:

```text
PEARLHASH_WALLET=prl1pw6q2dkd5zdkf3agvfyph6u0acyg7hs7aw9klxcv5ksc5s27r3gmq5yz7yt
PEARLHASH_POOL_HOST=129.226.55.135:9000
PEARLHASH_WORKER=worker2
```

Leave Salad's `Command` field empty so the Dockerfile `ENTRYPOINT` runs. If you
set `Command`, Salad overrides the image entrypoint and the miner will not start
unless you manually include `/usr/local/bin/pearlhash-entrypoint`.

Pearlhash currently exposes `pearl-miner-v11` and the generated launch command
on https://pearlhash.xyz/#config. If the pool region changes, update
`PEARLHASH_POOL_HOST` in Salad rather than rebuilding the image.

## Monitoring

```bash
modal app logs pearlhash-h100-miner
modal app logs pearlhash-miner
tail -f akoya.log
```
