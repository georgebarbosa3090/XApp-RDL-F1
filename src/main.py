import os
import sys
import time
import logging

from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "reference-xapps" / "qos-xslice"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "energy-saving"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "traffic-steering"))

from src.rdl_xapp import RDLxApp

logger = logging.getLogger("xapp_entrypoint")

if __name__ == '__main__':
    role = os.getenv("XAPP_ROLE", os.getenv("XAPP_TYPE", "rdl")).lower()
    
    if role in ("xslice", "qos", "qos-xslice"):
        from xslice_xapp import XSliceXApp
        logger.info("Iniciando Reference xApp: xSlice (QoS / Slicing Optimizer)...")
        app = XSliceXApp()
        app.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            app.stop()

    elif role in ("energy_saving", "es", "energy-saving"):
        from energy_saving_xapp import EnergySavingXApp
        logger.info("Iniciando Reference xApp: Energy Saving (Orange / FlexRIC)...")
        app = EnergySavingXApp()
        app.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            app.stop()

    elif role in ("traffic_steering", "ts", "traffic-steering"):
        from traffic_steering_xapp import TrafficSteeringXApp
        logger.info("Iniciando Reference xApp: Traffic Steering (O-RAN SC)...")
        app = TrafficSteeringXApp()
        app.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            app.stop()

    else:
        logger.info("Iniciando xApp RDL (Resource and Decision Layer - Fase 1: H-RDL)...")
        app = RDLxApp()
        app.start()

