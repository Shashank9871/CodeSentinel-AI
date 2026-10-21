"""
CodeSentinel AI Launcher Script
Starts the server and automatically opens your browser.
"""
import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

def open_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n[CodeSentinel AI] Opening web browser at {url} ...")
    webbrowser.open(url)

if __name__ == "__main__":
    # Add backend directory to python path
    backend_dir = Path(__file__).parent / "backend"
    sys.path.insert(0, str(backend_dir))

    banner = r"""
   _____          _       _____            _   _            _ 
  / ____|        | |     / ____|          | | (_)          | |
 | |     ___   __| | ___| (___   ___ _ __ | |_ _ _ __   ___| |
 | |    / _ \ / _` |/ _ \\___ \ / _ \ '_ \| __| | '_ \ / _ \ |
 | |___| (_) | (_| |  __/____) |  __/ | | | |_| | | | |  __/ |
  \_____\___/ \__,_|\___|_____/ \___|_| |_|\__|_|_| |_|\___|_|
                                               AI Platform v1.0
    """
    print(banner)
    print("🚀 Initializing CodeSentinel AI Code Review Platform...")
    print("📍 Platform running at: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server anytime.\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, app_dir=str(backend_dir), reload=False)

