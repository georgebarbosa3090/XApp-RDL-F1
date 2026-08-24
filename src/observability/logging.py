import structlog
import logging
import sys
import time

def now_ts() -> float:
    """Retorna timestamp float com precisão de microssegundos."""
    return time.time()

def setup_logger(name: str, level: str = "INFO"):
    log_level = getattr(logging, level.upper(), logging.INFO)
    
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
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    return structlog.get_logger(name)
