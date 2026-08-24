import json
import os
from pydantic import BaseModel
from typing import List

class XAppConfig(BaseModel):
    name: str
    version: str

class RMRConfig(BaseModel):
    port: int
    max_message_size: int
    wait_for_ready: bool

class HttpConfig(BaseModel):
    host: str
    port: int

class MetricsConfig(BaseModel):
    port: int

class SDLConfig(BaseModel):
    use_fake: bool
    namespace: str

class E2Config(BaseModel):
    subscription_period_ms: int
    retry_interval_seconds: int
    maximum_retries: int

class KpmConfig(BaseModel):
    service_model_versions: List[str]
    measurements: List[str]

class ControlConfig(BaseModel):
    enabled: bool
    dry_run: bool
    service_model: str

class AppConfig(BaseModel):
    xapp: XAppConfig
    rmr: RMRConfig
    http: HttpConfig
    metrics: MetricsConfig
    sdl: SDLConfig
    e2: E2Config
    kpm: KpmConfig
    control: ControlConfig

class ConfigManager:
    @staticmethod
    def load_config(filepath: str = "configs/config-file.json") -> AppConfig:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return AppConfig(**data)
