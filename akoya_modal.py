"""
Akoya Pearl Miner on Modal.com — H100 via Modal Sandbox

  modal deploy akoya_modal.py
  modal run akoya_modal.py
"""

import shlex
import textwrap

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


def _miner_bash() -> str:
    w, k = shlex.quote(WALLET), shlex.quote(WORKER)
    return textwrap.dedent(
        f"""
        set -euo pipefail
        export AKOYA_POOL_WALLET={w}
        export AKOYA_POOL_WORKER={k}
        export AKOYA_POOL_HOST=pool-v2.akoyapool.com
        export AKOYA_POOL_PORT=443
        export AKOYA_POOL_USE_TLS=1
        export AKOYA_GPU_INDICES=all
        export AKOYA_METRICS_PORT=9100
        export AKOYA_PEARL_GEMM_LIB=/app/lib/libpearl_gemm_capi.so
        export AKOYA_PEARL_MINING_LIB=/app/lib/libpearl_mining_capi.so

        CC=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1)
        MAJOR=${{CC%%.*}} MINOR=${{CC#*.}}
        echo "[Modal] GPU compute: $MAJOR.$MINOR"
        LIB=/app/lib
        TARGET="$LIB/libpearl_gemm_capi.so"
        if [ "$MAJOR" = "12" ]; then SRC=blackwell
        elif [ "$MAJOR" = "9" ]; then SRC=h100
        elif [ "$MAJOR" = "8" ] && [ "$MINOR" = "9" ]; then SRC=ada
        else SRC=portable; fi
        rm -f "$TARGET"
        ln -s "$LIB/libpearl_gemm_capi_$SRC.so" "$TARGET"
        echo "[Modal] Kernel: $SRC"
        mkdir -p /var/lib/akoya-miner
        exec /app/akoya-miner mine-blocks
        """
    ).strip()


@app.function(image=akoya_image, timeout=300)
def train():
    import time

    sb = modal.Sandbox.create(
        app=app,
        image=akoya_image,
        gpu=GPU,
        timeout=TIMEOUT,
        idle_timeout=TIMEOUT,
    )
    proc = sb.exec("bash", "-lc", _miner_bash())
    print(f"[Modal] Sandbox id: {sb.object_id}", flush=True)

    deadline = time.time() + 90
    while time.time() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            raise RuntimeError(
                f"Miner exited early (code={proc.returncode}). Output:\n{out}"
            )
        time.sleep(5)

    print("[Modal] Miner passed startup checks — detaching Sandbox", flush=True)
    sb.detach()
    return sb.object_id


@app.local_entrypoint()
def main():
    try:
        fn = modal.Function.from_name("akoya-pearl-miner", "train")
    except modal.exception.NotFoundError:
        print(
            "[Modal] Deploy first:\n"
            "  modal deploy akoya_modal.py\n"
            "  modal run akoya_modal.py"
        )
        raise SystemExit(1) from None

    fc = fn.spawn()
    print(f"[Modal] Launching miner sandbox (call_id={fc.object_id})")
    print("[Modal] Logs: modal app logs akoya-pearl-miner")
    print("[Modal] Stop: Modal dashboard → Sandboxes → terminate")
