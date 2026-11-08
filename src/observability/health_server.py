import time
import threading
import logging
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

SUBSCRIPTION_NOTIFICATION_PATH = "/ric/v1/subscriptions/response"

try:
    import uvicorn
    from fastapi import FastAPI, Request, Response, status
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
        # Callback(body) -> bool | None para notificações assíncronas do SubMgr.
        self.subscription_callback = None

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
                # Somente READY: em SUBSCRIBING a subscrição E2 ainda não foi confirmada.
                if self.state == AppState.READY:
                    return {"status": "READY", "state": self.state}
                else:
                    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                    return {"status": "NOT_READY", "current_state": self.state}

            @self.app.post(SUBSCRIPTION_NOTIFICATION_PATH)
            async def subscription_notification(request: Request, response: Response):
                try:
                    body = await request.json()
                except Exception:
                    response.status_code = 400
                    return {"error": "invalid JSON"}
                callback = self.subscription_callback
                if callback is None or callback(body) is None:
                    response.status_code = 404
                    return {"error": "unknown subscription"}
                return {}

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
        if self.server_thread is not None:
            return
        if HAS_FASTAPI and self.app is not None:
            try:
                config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="error")
                server = uvicorn.Server(config)
                def serve():
                    try:
                        server.run()
                    except OSError:
                        logging.getLogger(__name__).exception(
                            "Health server failed to bind on %s:%s", self.host, self.port
                        )
                    except SystemExit as exc:
                        logging.getLogger(__name__).error(
                            "Health server stopped during startup on %s:%s (exit code %s)",
                            self.host,
                            self.port,
                            exc.code,
                        )

                self.server_thread = threading.Thread(target=serve, daemon=True)
                self.server_thread.start()
            except (OSError, RuntimeError):
                self.server_thread = None
                logging.getLogger(__name__).exception("Unable to start health server")
