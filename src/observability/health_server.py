import time
import threading
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

try:
    import uvicorn
    from fastapi import FastAPI, Response, status
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    class Response:
        def __init__(self, *args, **kwargs):
            self.status_code = kwargs.get("status_code", 200)
    class status:
        HTTP_200_OK = 200
        HTTP_503_SERVICE_UNAVAILABLE = 503

class HealthServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.state = AppState.STARTING
        self.start_time = time.time()
        self.version = "1.1.0"
        self.server_thread = None
        
        if HAS_FASTAPI:
            self.app = FastAPI(title="RDL xApp Health Server")
            
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
        else:
            self.app = None

    def set_state(self, new_state: AppState):
        self.state = new_state

    def run(self):
        if HAS_FASTAPI and self.app is not None:
            try:
                config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="error")
                server = uvicorn.Server(config)
                self.server_thread = threading.Thread(target=server.run, daemon=True)
                self.server_thread.start()
            except Exception:
                pass
