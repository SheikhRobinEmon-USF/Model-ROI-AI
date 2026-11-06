"""Cross-platform launcher. Run from a checkout with Python 3.12+."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.request import build_opener, ProxyHandler

ROOT=Path(__file__).resolve().parents[1]

def main():
    if sys.version_info < (3,12):
        raise SystemExit('Python 3.12 or newer is required.')
    ollama=shutil.which('ollama')
    if not ollama:
        raise SystemExit('Ollama CLI not found. Open/install Ollama, restart your terminal, then retry.')
    try:
        with build_opener(ProxyHandler({})).open('http://127.0.0.1:11434/api/tags',timeout=5) as response:
            models=json.load(response).get('models',[])
    except OSError:
        raise SystemExit('Open the Ollama app, or run ollama serve in another terminal, then retry.')
    if not any(m.get('name')=='qwen3:4b' for m in models):
        print('Qwen3 4B is not installed. Downloading it uses several GB of disk and network data.')
        if input('Download qwen3:4b now? [y/N] ').strip().lower()!='y':
            raise SystemExit('No model downloaded.')
        subprocess.run([ollama,'pull','qwen3:4b'],check=True)
    envdir=ROOT/'.venv'
    executable=envdir/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not executable.exists():
        subprocess.run([sys.executable,'-m','venv',str(envdir)],check=True)
    subprocess.run([str(executable),'-m','pip','install','-e',str(ROOT)],check=True)
    environment=os.environ.copy()
    environment['MODELROI_ENABLE_LOCAL']='true'
    print('Starting local ModelROI at http://localhost:8501. Press Ctrl+C to stop.')
    subprocess.run([str(executable),'-m','streamlit','run',str(ROOT/'app/ui/Home.py'),
                    '--server.address','127.0.0.1'],cwd=ROOT,env=environment,check=True)

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopped.')
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f'Command failed with exit code {exc.returncode}; see output above.')
