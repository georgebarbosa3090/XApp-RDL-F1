import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import uuid
from src.conflict_types import XAppAction
from src.rdl_xapp import RDLxApp

def test_decision_window():
    print("Iniciando xApp em modo de teste...")
    app = RDLxApp()
    
    # Inicia a thread de decisão manualmente para não depender do framework C/RMR
    import threading
    app.running = True
    threading.Thread(target=app._decision_loop, daemon=True).start()
    
    print("Injetando 3 ações simultâneas...")
    action1 = XAppAction(xapp_id="xapp_drm", node_id="gnb_01", parameter="TX_POWER", value=42.0, priority=50)
    action2 = XAppAction(xapp_id="xapp_ee", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=60)
    action3 = XAppAction(xapp_id="xapp_ho", node_id="gnb_01", parameter="A3_OFFSET", value=-3.0, priority=80)
    
    app.inject_xapp_action(action1)
    app.inject_xapp_action(action2)
    app.inject_xapp_action(action3)
    
    print("Ações injetadas. Aguardando a janela de 200ms fechar...")
    time.sleep(1.0)
    
    app.running = False
    print("Teste concluído.")

if __name__ == "__main__":
    test_decision_window()
