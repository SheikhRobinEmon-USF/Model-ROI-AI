"""Cross-platform launcher. Run from a checkout with Python 3.12+."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import socket
import threading
import time
import webbrowser
from urllib.request import build_opener, ProxyHandler

ROOT=Path(__file__).resolve().parents[1]

def main():
    if sys.version_info < (3,12):
        raise SystemExit('Python 3.12 or newer is required.')
    if "--hosted" not in sys.argv:
        ollama=shutil.which('ollama')
        if not ollama:
            raise SystemExit('Ollama CLI not found. Open/install Ollama, restart your terminal, then retry.')
        try:
            with build_opener(ProxyHandler({})).open('http://127.0.0.1:11434/api/tags',timeout=5) as response:
                models=json.load(response).get('models',[])
        except OSError:
            raise SystemExit('Open the Ollama app, or run ollama serve in another terminal, then retry.')
        if not models:
            print('No Ollama models are installed. Downloading Qwen3 4B uses several GB of disk and network data.')
            if input('Download qwen3:4b now? [y/N] ').strip().lower()!='y':
                raise SystemExit('No model downloaded.')
            subprocess.run([ollama,'pull','qwen3:4b'],check=True)
    envdir=ROOT/'.venv'
    executable=envdir/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not executable.exists():
        subprocess.run([sys.executable,'-m','venv',str(envdir)],check=True)
    signature = hashlib.sha256((ROOT/"pyproject.toml").read_bytes() + str(ROOT).encode() +
                               sys.version.encode()).hexdigest()
    marker = envdir / "modelroi-installed"
    if not marker.exists() or marker.read_text() != signature:
        subprocess.run([str(executable), "-m", "pip", "install", "-e", str(ROOT)], check=True)
        marker.write_text(signature)
    environment=os.environ.copy()
    environment['MODELROI_ENABLE_LOCAL']='true'
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", 8501))
        except OSError:
            probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    def open_studio():
        for _ in range(60):
            try:
                with build_opener(ProxyHandler({})).open(url+"/health", timeout=1):
                    webbrowser.open(url)
                    return
            except OSError:
                time.sleep(0.5)
    threading.Thread(target=open_studio, daemon=True).start()
    print(f"Starting ModelROI at {url}. Press Control+C to stop.", flush=True)
    subprocess.run([str(executable), "-m", "uvicorn", "app.api.main:app",
                    "--host", "127.0.0.1", "--port", str(port)],
                   cwd=ROOT, env=environment, check=True)

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopped.')
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f'Command failed with exit code {exc.returncode}; see output above.')
