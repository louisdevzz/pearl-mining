"""
Akoya Pearl Miner on Modal.com — H100 (direct Function, no Sandbox)

  modal deploy fix_akoya_modal.py
  modal run fix_akoya_modal.py          # blocks, shows logs, Dashboard shows H100

  modal app logs akoya-pearl-miner
  modal app stop akoya-pearl-miner
"""

import modal

app = modal.App("akoya-pearl-miner")

WALLET = "prl1pw6q2dkd5zdkf3agvfyph6u0acyg7hs7aw9klxcv5ksc5s27r3gmq5yz7yt"
WORKER = "worker3"
GPU = "H100"
TIMEOUT = 86400

akoya_image = (
    modal.Image.from_registry(
        "registry.akoyapool.com/akoya-miner:latest",
        add_python="3.11",
    )
    .dockerfile_commands([
        "ENTRYPOINT []",
        "CMD []",
    ])
)


@app.function(
    gpu=GPU,
    image=akoya_image,
    timeout=TIMEOUT,
    scaledown_window=300,
)
def train():
    import os
    import signal
    import subprocess
    import time

    # Modal may SIGINT the worker on client disconnect; don't forward to miner.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    os.environ["AKOYA_POOL_WALLET"] = WALLET
    os.environ["AKOYA_POOL_WORKER"] = WORKER
    os.environ["AKOYA_POOL_HOST"] = "pool-v2.akoyapool.com"
    os.environ["AKOYA_POOL_PORT"] = "443"
    os.environ["AKOYA_POOL_USE_TLS"] = "1"
    os.environ["AKOYA_GPU_INDICES"] = "all"
    os.environ["AKOYA_METRICS_PORT"] = "9100"
    os.environ["AKOYA_PEARL_GEMM_LIB"] = "/app/lib/libpearl_gemm_capi.so"
    os.environ["AKOYA_PEARL_MINING_LIB"] = "/app/lib/libpearl_mining_capi.so"

    cc = subprocess.run(
        ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip().split("\n")[0]
    major, minor = cc.split(".")
    print(f"[Modal] GPU compute: {major}.{minor}", flush=True)

    lib_dir = "/app/lib"
    target = f"{lib_dir}/libpearl_gemm_capi.so"
    if int(major) == 12:
        src = "blackwell"
    elif int(major) == 9:
        src = "h100"
    elif int(major) == 8 and int(minor) == 9:
        src = "ada"
    else:
        src = "portable"

    lib_file = f"{lib_dir}/libpearl_gemm_capi_{src}.so"
    if os.path.lexists(target):
        os.unlink(target)
    os.symlink(lib_file, target)
    print(f"[Modal] Kernel: {src}", flush=True)

    os.makedirs("/var/lib/akoya-miner", exist_ok=True)

    proc = subprocess.Popen(
        ["/app/akoya-miner", "mine-blocks"],
        env=os.environ.copy(),
        stdin=subprocess.DEVNULL,
        stdout=None,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(f"[Modal] Miner PID: {proc.pid} on {GPU}", flush=True)

    while True:
        rc = proc.poll()
        if rc is not None:
            return rc
        time.sleep(60)
        print("[Modal] miner still running", flush=True)


@app.local_entrypoint()
def main(background: bool = False):
    try:
        fn = modal.Function.from_name("akoya-pearl-miner", "train")
    except modal.exception.NotFoundError:
        print(
            "[Modal] Deploy first:\n"
            "  modal deploy fix_akoya_modal.py\n"
            "  modal run fix_akoya_modal.py"
        )
        raise SystemExit(1) from None

    if background:
        fc = fn.spawn()
        print(f"[Modal] Background (call_id={fc.object_id})")
        print("[Modal] Logs: modal app logs akoya-pearl-miner")
        return

    print(f"[Modal] Starting {GPU} miner (logs below, keep deploy app running)...", flush=True)
    fn.remote()
