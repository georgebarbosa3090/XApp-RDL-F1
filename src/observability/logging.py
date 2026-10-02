import logging
import sys
import time

try:
    import structlog
    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False

def now_ts() -> float:
    """Retorna timestamp float com precisão de microssegundos."""
    return time.time()

class _FallbackLogger:
    """Logger wrapper compatível com chamadas de chave-valor do structlog."""
    def __init__(self, std_logger: logging.Logger):
        self._logger = std_logger

    def info(self, event: str, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
        self._logger.info(f"{event} {extra}".strip())

    def warning(self, event: str, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
        self._logger.warning(f"{event} {extra}".strip())

    def error(self, event: str, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
        self._logger.error(f"{event} {extra}".strip())

    def debug(self, event: str, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
        self._logger.debug(f"{event} {extra}".strip())

def setup_logger(name: str, level: str = "INFO"):
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if _HAS_STRUCTLOG:
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        formatter = logging.Formatter("%(message)s")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        
        root_logger = logging.getLogger(name)
        if not root_logger.handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(log_level)
        
        return structlog.get_logger(name)
    else:
        root_logger = logging.getLogger(name)
        if not root_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)
        root_logger.setLevel(log_level)
        return _FallbackLogger(root_logger)
