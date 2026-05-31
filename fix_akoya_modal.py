"""
Akoya Pearl Miner on Modal.com — Serverless H100 Mining
Deploy: modal deploy akoya_modal.py
Run:    modal run akoya_modal.py
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
    import subprocess
    import os

    os.environ["AKOYA_POOL_WALLET"]    = WALLET
    os.environ["AKOYA_POOL_WORKER"]    = WORKER
    os.environ["AKOYA_POOL_HOST"]      = "pool-v2.akoyapool.com"
    os.environ["AKOYA_POOL_PORT"]      = "443"
    os.environ["AKOYA_POOL_USE_TLS"]   = "1"
    os.environ["AKOYA_GPU_INDICES"]    = "all"
    os.environ["AKOYA_METRICS_PORT"]   = "9100"
    os.environ["AKOYA_PEARL_GEMM_LIB"] = "/app/lib/libpearl_gemm_capi.so"
    os.environ["AKOYA_PEARL_MINING_LIB"] = "/app/lib/libpearl_mining_capi.so"

    # GPU kernel selection
    cc = subprocess.run(
        ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
        capture_output=True, text=True
    ).stdout.strip().split("\n")[0]
    major, minor = cc.split(".")
    print(f"[Modal] GPU compute: {major}.{minor}")

    lib_dir = "/app/lib"
    target = f"{lib_dir}/libpearl_gemm_capi.so"
    if int(major) == 12: src = "blackwell"
    elif int(major) == 9: src = "h100"
    elif int(major) == 8 and int(minor) == 9: src = "ada"
    else: src = "portable"

    lib_file = f"{lib_dir}/libpearl_gemm_capi_{src}.so"
    if os.path.lexists(target): os.unlink(target)
    os.symlink(lib_file, target)
    print(f"[Modal] Kernel: {src}")

    os.makedirs("/var/lib/akoya-miner", exist_ok=True)

    # Keep the Modal Python worker alive for heartbeats. os.execv replaces this
    # process and causes heartbeat timeout (~900s) or early SIGINT on modal run.
    proc = subprocess.Popen(
        ["/app/akoya-miner", "mine-blocks"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=os.environ,
    )
    print(f"[Modal] Miner PID: {proc.pid}", flush=True)
    for line in iter(proc.stdout.readline, b""):
        if not line:
            break
        print(line.decode(errors="replace").rstrip(), flush=True)
    return proc.wait()


@app.local_entrypoint()
def main():
    train.remote()
