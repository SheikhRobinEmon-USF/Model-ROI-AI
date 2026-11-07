"""Launch a private tester session and print its temporary public URL."""
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import urllib.request
import time

root = Path(__file__).resolve().parents[1]
python = root / ".venv/bin/python"
tunnel = shutil.which("cloudflared")
if not tunnel:
    raise SystemExit("Install the tunnel client first: brew install cloudflared")
if not python.exists():
    raise SystemExit("Run python3 scripts/start_local.py once to install ModelROI.")
env = dict(os.environ, MODELROI_PILOT_CODE=secrets.token_urlsafe(18))
# Select an independent port so the owner's workspace can stay open.
import socket
with socket.socket() as probe:
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
url = f"http://127.0.0.1:{port}"
server = subprocess.Popen([str(python), "-m", "streamlit", "run", "app/ui/Pilot.py",
                           "--server.address=127.0.0.1", f"--server.port={port}",
                           "--server.headless=true"], cwd=root, env=env)
try:
    for _ in range(60):
        if server.poll() is not None:
            raise SystemExit("Tester interface exited during startup.")
        try:
            with urllib.request.urlopen(url + "/_stcore/health", timeout=1) as response:
                if response.read().strip() == b"ok":
                    break
        except OSError:
            pass
        time.sleep(0.5)
    else:
        raise SystemExit("Tester interface did not become ready.")
    print("Tester access code:", env["MODELROI_PILOT_CODE"], flush=True)
    print("Share this code and the trycloudflare.com URL printed below.", flush=True)
    subprocess.run([tunnel, "tunnel", "--url", url], check=True)
except KeyboardInterrupt:
    pass
finally:
    server.terminate()
    server.wait()
