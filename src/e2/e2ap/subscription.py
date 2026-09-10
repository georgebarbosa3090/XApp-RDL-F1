from dataclasses import dataclass, field
import uuid
import time
from typing import Optional, Dict, Any, List
from src.e2.kpm.event_trigger import build_kpm_event_trigger
from src.e2.kpm.action_definition import build_kpm_action_definition
from src.observability.logging import setup_logger

logger = setup_logger("E2APSubscription")

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

def build_ric_subscription_request_payload(
    target_node: str = "gnb_01",
    ran_function_id: int = 2,
    report_period_ms: int = 200,
    metric_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Constrói a estrutura padronizada da requisição de subscrição E2 (RIC Subscription Request)
    com payloads APER genuínos para Event Trigger e Action Definition.
    Compatível com o Subscription Manager (SubMgr) do O-RAN SC e NORI.
    """
    # 1. Gera Event Trigger APER real
    trigger_bytes = build_kpm_event_trigger(report_period_ms=report_period_ms)
    
    # 2. Gera Action Definition APER real
    action_def_bytes = build_kpm_action_definition(
        style_type=1,
        granularity_period_ms=report_period_ms,
        metric_names=metric_names
    )
    
    sub_id = f"sub-kpm-{target_node}-{ran_function_id}"
    
    payload = {
        "SubscriptionId": sub_id,
        "ClientEndpoint": ["service-ricxapp-iqos-xapp-rdl-http.ricxapp:8080"],
        "Meid": target_node,
        "RANFunctionID": int(ran_function_id),
        "SubscriptionDetails": [
            {
                "XappEventInstanceId": 1,
                "EventTriggers": [
                    trigger_bytes.hex()
                ],
                "ActionToBeSetupList": [
                    {
                        "ActionID": 1,
                        "ActionType": "report",
                        "ActionDefinition": [
                            action_def_bytes.hex()
                        ],
                        "SubsequentAction": {
                            "SubsequentActionType": "continue",
                            "TimeToWait": "zero"
                        }
                    }
                ]
            }
        ]
    }
    
    logger.info(f"RIC Subscription Request estruturado para {target_node} (KPM OID 2, Trigger: {len(trigger_bytes)}B APER)")
    return payload
