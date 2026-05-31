# Modal Pearl Miner

Serverless Pearl mining on Modal.com (H100/A100).

## Quick Start

```bash
pip install modal
modal token set --token-id YOUR_ID --token-secret YOUR_SECRET

# Akoya Pool (H100) — deploy once, then spawn (survives terminal close)
modal deploy akoya_modal.py
modal run akoya_modal.py

# Ephemeral one-liner (no deploy): must use --detach or Modal kills the GPU when you disconnect
modal run --detach akoya_modal.py::train

# Pearlhash Pool (A100)
modal deploy pearlhash_modal.py
modal run pearlhash_modal.py
```

**Why "Runner terminated"?** `modal run` without deploy + spawn ties the GPU job to your local CLI session. Closing the terminal, Ctrl-C, or disconnecting from the Modal dashboard stops the runner. Use `modal deploy` then `modal run` (spawns in background), or `modal run --detach ...::train`.

## Files

- `akoya_modal.py` — Akoya pool miner (H100, ~600 TH/s)
- `pearlhash_modal.py` — Pearlhash pool miner (A100, ~150 TH/s)

## Wallet

Change `WALLET` in each script.

## Monitoring

```bash
modal app logs akoya-pearl-miner
modal app logs pearlhash-miner
tail -f akoya.log
```
