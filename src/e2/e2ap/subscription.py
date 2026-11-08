from dataclasses import dataclass, field
import os
import time
from typing import Optional, Dict, Any, List
from src.e2.kpm.event_trigger import build_kpm_event_trigger
from src.e2.kpm.action_definition import build_kpm_action_definition
from src.observability.logging import setup_logger

logger = setup_logger("E2APSubscription")

DEFAULT_CLIENT_HOST = "service-ricxapp-iqos-xapp-rdl-http.ricxapp"
DEFAULT_CLIENT_HTTP_PORT = 8080
DEFAULT_CLIENT_RMR_PORT = 4560

# Valores aceitos pelo modelo SubsequentAction da API REST do SubMgr (O-RAN SC).
TIME_TO_WAIT_VALUES = (
    "zero", "w1ms", "w2ms", "w5ms", "w10ms", "w20ms", "w30ms", "w40ms", "w50ms",
    "w100ms", "w200ms", "w500ms", "w1s", "w2s", "w5s", "w10s", "w20s", "w60s",
)


@dataclass
class SubscriptionDetails:
    subscription_id: str
    target_node: str
    ran_function_id: int
    report_period_ms: int
    event_trigger_aper_hex: str
    action_definition_aper_hex: str
    status: str = "PENDING"
    created_at: float = field(default_factory=time.time)


def _octets(data: bytes) -> List[int]:
    """OctetString da API REST do SubMgr: lista de inteiros 0..255."""
    return list(bytes(data))


def build_ric_subscription_request_payload(
    target_node: str = "gnb_01",
    ran_function_id: int = 2,
    report_period_ms: int = 200,
    metric_names: Optional[List[str]] = None,
    xapp_event_instance_id: int = 1,
    client_host: Optional[str] = None,
    client_http_port: Optional[int] = None,
    client_rmr_port: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Constrói o corpo ``SubscriptionParams`` do ``POST /ric/v1/subscriptions`` do
    Subscription Manager (O-RAN SC, API REST de xApps).

    Event Trigger e Action Definition são produzidos pelos codecs E2SM-KPM locais;
    a conformidade desses bytes com o ASN.1 oficial do E2SM-KPM ainda não foi
    validada contra uma implementação independente.
    """
    if not 0 <= int(ran_function_id) <= 4095:
        raise ValueError("RANFunctionID must be in [0, 4095]")
    if not 0 <= int(xapp_event_instance_id) <= 65535:
        raise ValueError("XappEventInstanceId must be in [0, 65535]")

    trigger_bytes = build_kpm_event_trigger(report_period_ms=report_period_ms)
    action_def_bytes = build_kpm_action_definition(
        style_type=1,
        granularity_period_ms=report_period_ms,
        metric_names=metric_names
    )

    payload = {
        "ClientEndpoint": {
            "Host": client_host or os.getenv("XAPP_HTTP_HOST", DEFAULT_CLIENT_HOST),
            "HTTPPort": int(client_http_port or os.getenv("XAPP_HTTP_PORT", DEFAULT_CLIENT_HTTP_PORT)),
            "RMRPort": int(client_rmr_port or os.getenv("XAPP_RMR_PORT", DEFAULT_CLIENT_RMR_PORT)),
        },
        "Meid": target_node,
        "RANFunctionID": int(ran_function_id),
        "SubscriptionDetails": [
            {
                "XappEventInstanceId": int(xapp_event_instance_id),
                "EventTriggers": _octets(trigger_bytes),
                "ActionToBeSetupList": [
                    {
                        "ActionID": 1,
                        "ActionType": "report",
                        "ActionDefinition": _octets(action_def_bytes),
                        "SubsequentAction": {
                            "SubsequentActionType": "continue",
                            "TimeToWait": "zero"
                        }
                    }
                ]
            }
        ]
    }

    logger.info(
        f"SubscriptionParams estruturado para {target_node} "
        f"(RANFunctionID {ran_function_id}, Trigger {len(trigger_bytes)}B)"
    )
    return payload
