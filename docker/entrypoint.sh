#!/usr/bin/env bash
set -Eeuo pipefail

miner_path="${MINER_PATH:-/opt/pearl-miner}"
pool_host="${PEARLHASH_POOL_HOST:-${POOL_HOST:-}}"
wallet="${PEARLHASH_WALLET:-${WALLET:-}}"
worker="${PEARLHASH_WORKER:-${WORKER:-}}"

if [[ ! -x "$miner_path" ]]; then
  echo "[Pearlhash] Miner binary is missing or not executable: $miner_path" >&2
  exit 1
fi

if [[ -z "$pool_host" ]]; then
  echo "[Pearlhash] Missing PEARLHASH_POOL_HOST" >&2
  exit 64
fi

if [[ -z "$wallet" ]]; then
  echo "[Pearlhash] Missing PEARLHASH_WALLET" >&2
  exit 64
fi

echo "[Pearlhash] Starting miner"
echo "[Pearlhash] Pool: $pool_host"
echo "[Pearlhash] Wallet: $wallet"
if [[ -n "$worker" ]]; then
  echo "[Pearlhash] Worker: $worker"
fi

args=("$miner_path" "--host" "$pool_host" "--user" "$wallet")
if [[ -n "$worker" ]]; then
  args+=("--worker" "$worker")
fi

exec "${args[@]}"
