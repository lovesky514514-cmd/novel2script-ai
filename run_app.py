import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
EXPECTED_VERSION = "day2_fullstack_polish"
BACKEND_URL = "http://127.0.0.1:8000/health"
VERSION_URL = "http://127.0.0.1:8000/api/version"
FRONTEND_URL = "http://127.0.0.1:5173/"
IS_WINDOWS = os.name == "nt"


def log(msg):
    print(f"[Novel2Script] {msg}", flush=True)


def run(cmd, cwd=None, check=True):
    log(f"RUN: {' '.join(map(str, cmd))}")
    return subprocess.run(cmd, cwd=cwd, check=check)


def popen(cmd, cwd=None):
    creationflags = subprocess.CREATE_NEW_CONSOLE if IS_WINDOWS else 0
    log(f"START: {' '.join(map(str, cmd))}")
    return subprocess.Popen(cmd, cwd=cwd, creationflags=creationflags)


def kill_port(port):
    if not IS_WINDOWS:
        return
    try:
        output = subprocess.check_output(f'netstat -ano | findstr ":{port}"', shell=True, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return
    pids = set()
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[1].endswith(f":{port}") and parts[-1].isdigit():
            pids.add(parts[-1])
    for pid in sorted(pids):
        log(f"KILL port {port} PID={pid}")
        subprocess.run(["taskkill", "/PID", pid, "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def clean():
    kill_port(8000)
    kill_port(5173)
    cache = FRONTEND / "node_modules" / ".vite"
    if cache.exists():
        log(f"Remove cache: {cache}")
        shutil.rmtree(cache, ignore_errors=True)
    time.sleep(2)


def get_json(url):
    with urllib.request.urlopen(url, timeout=2) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_http(url, timeout=45):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def wait_version(timeout=45):
    start = time.time()
    last = None
    while time.time() - start < timeout:
        try:
            data = get_json(VERSION_URL)
            last = data
            if data.get("version") == EXPECTED_VERSION:
                log(f"Backend version OK: {EXPECTED_VERSION}")
                return
        except Exception as exc:
            last = str(exc)
        time.sleep(1)
    raise RuntimeError(f"Backend version is not {EXPECTED_VERSION}. Last: {last}")


def ensure_env():
    env = BACKEND / ".env"
    example = BACKEND / ".env.example"
    if not env.exists() and example.exists():
        env.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        log("Created backend/.env. Put your key in AI_API_KEY.")


def install_backend():
    venv = BACKEND / ".venv"
    if not venv.exists():
        run([sys.executable, "-m", "venv", str(venv)], cwd=BACKEND)
    python = venv / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
    run([str(python), "-m", "pip", "install", "-r", "requirements.txt"], cwd=BACKEND)
    return python


def install_frontend():
    npm = "npm.cmd" if IS_WINDOWS else "npm"
    if not (FRONTEND / "node_modules").exists():
        run([npm, "install"], cwd=FRONTEND)
    return npm


def main():
    log("Starting accuracy pipeline final...")
    log(f"Expected version: {EXPECTED_VERSION}")
    clean()
    ensure_env()
    python = install_backend()
    npm = install_frontend()

    popen([str(python), "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"], cwd=BACKEND)
    if not wait_http(BACKEND_URL):
        raise RuntimeError("Backend not ready.")
    wait_version()

    popen([npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173", "--force"], cwd=FRONTEND)
    time.sleep(4)
    webbrowser.open(FRONTEND_URL)
    log(f"Opened: {FRONTEND_URL}")
    log(f"Manual open URL: {FRONTEND_URL}")
    log(f"Frontend left top must show: {EXPECTED_VERSION}")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"ERROR: {exc}")
        input("Press Enter to exit...")
