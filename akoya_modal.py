"""
Pearlhash miner on Modal.com — H100
Pool: https://pearlhash.xyz/#start-mining

  modal deploy akoya_modal.py
  modal run akoya_modal.py
  modal app stop pearlhash-h100-miner
"""

import modal

app = modal.App("pearlhash-h100-miner")

WALLET = "prl1pw6q2dkd5zdkf3agvfyph6u0acyg7hs7aw9klxcv5ksc5s27r3gmq5yz7yt"
POOL_HOST = "129.226.55.135:9000"
WORKER = "worker2"
GPU = "H100"
TIMEOUT = 86400
MINER_PATH = "/opt/pearl-miner"

pearlhash_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.0-runtime-ubuntu22.04",
        add_python="3.11",
    )
    .apt_install("curl", "libgomp1")
    .run_commands(
        "curl -fsSL https://pearlhash.xyz/downloads/pearl-miner-v11 "
        f"-o {MINER_PATH} && chmod +x {MINER_PATH}"
    )
)


@app.function(
    gpu=GPU,
    image=pearlhash_image,
    timeout=TIMEOUT,
    scaledown_window=300,
)
def mine():
    import signal
    import subprocess
    import time

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    print(f"[Modal] Pearlhash miner v11 on {GPU}", flush=True)
    print(f"[Modal] Pool: {POOL_HOST}", flush=True)
    print(f"[Modal] Wallet: {WALLET}", flush=True)
    print(f"[Modal] Worker: {WORKER}", flush=True)

    proc = subprocess.Popen(
        [
            MINER_PATH,
            "--host",
            POOL_HOST,
            "--user",
            WALLET,
            "--worker",
            WORKER,
        ],
        stdin=subprocess.DEVNULL,
        stdout=None,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(f"[Modal] Miner PID: {proc.pid}", flush=True)

    while True:
        rc = proc.poll()
        if rc is not None:
            return rc
        time.sleep(60)
        print("[Modal] miner still running", flush=True)


@app.local_entrypoint()
def main(background: bool = False):
    if background:
        fc = mine.spawn()
        print(f"[Modal] Background: {fc.object_id}")
        print("[Modal] Logs: modal app logs pearlhash-h100-miner")
        return

    print(f"[Modal] Starting Pearlhash {GPU} miner...", flush=True)
    mine.remote()
