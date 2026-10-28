#!/usr/bin/env python3
"""
Iniciador do Dashboard Web 6-Janelas O-RAN em Malha Fechada.
Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist
"""

import sys
import os
import webbrowser
import threading
import time

workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from src.observability.live_6pane_server import start_server

HOST = "127.0.0.1"
PORT = 8888


def open_browser():
    time.sleep(1.2)
    url = f"http://{HOST}:{PORT}"
    print(f"\n[INFO] Abrindo Dashboard 6-Janelas no navegador: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[WARN] Não foi possível abrir o navegador automaticamente: {e}")


if __name__ == "__main__":
    print("=" * 75)
    print("  🌐 O-RAN COGNITIVE TWIN — DASHBOARD LIVE 6-JANELAS NA MESMA TELA")
    print("=" * 75)
    print(f"  • Servidor HTTP & SSE: http://{HOST}:{PORT}")
    print("  • Pressione Ctrl+C para encerrar o servidor.")
    print("=" * 75)

    if "--no-browser" not in sys.argv:
        threading.Thread(target=open_browser, daemon=True).start()

    start_server(host=HOST, port=PORT)
