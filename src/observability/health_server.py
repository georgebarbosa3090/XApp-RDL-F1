import time
import threading
import uvicorn
from fastapi import FastAPI, Response, status
from enum import Enum
from pydantic import BaseModel

class AppState(str, Enum):
    STARTING = "STARTING"
    RMR_READY = "RMR_READY"
    SDL_READY = "SDL_READY"
    DISCOVERING_E2_NODES = "DISCOVERING_E2_NODES"
    SUBSCRIBING = "SUBSCRIBING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

class HealthServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.app = FastAPI(title="RDL xApp Health Server")
        self.host = host
        self.port = port
        self.state = AppState.STARTING
        self.start_time = time.time()
        self.version = "1.1.0"
        
        # Rotas
        @self.app.get("/health")
        def health():
            return {
                "status": "UP",
                "uptime_seconds": int(time.time() - self.start_time)
            }
            
        @self.app.get("/ready")
        def ready(response: Response):
            if self.state in [AppState.READY, AppState.DEGRADED]:
                return {"status": "READY"}
            else:
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                return {"status": "NOT_READY", "current_state": self.state}
                
        @self.app.get("/status")
        def get_status():
            return {
                "state": self.state,
                "version": self.version,
                "uptime_seconds": int(time.time() - self.start_time)
            }

    def set_state(self, new_state: AppState):
        self.state = new_state

    def run(self):
        # Roda o servidor Uvicorn numa thread separada
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="error")
        server = uvicorn.Server(config)
        self.server_thread = threading.Thread(target=server.run, daemon=True)
        self.server_thread.start()
