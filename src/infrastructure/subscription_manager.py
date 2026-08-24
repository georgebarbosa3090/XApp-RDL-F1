import requests
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from src.observability.logging import setup_logger

logger = setup_logger("SubscriptionManager")

@dataclass
class SubscriptionContext:
    subscription_id: str
    request_id: int
    instance_id: int
    ran_function_id: int
    meid: str
    status: str
    created_at: datetime

class SubscriptionManager:
    def __init__(self, submgr_url: str = "http://service-ricplt-submgr-http.ricplt:8088"):
        self.submgr_url = submgr_url

    def request_kpm_subscription(self, meid: str, ran_function_id: int, period_ms: int = 1000) -> Optional[SubscriptionContext]:
        """
        Solicita uma subscrição E2SM-KPM para um nó E2 específico (via MEID).
        """
        payload = {
            "SubscriptionId": "",
            "ClientEndpoint": ["service-ricxapp-iqos-xapp-rdl-http.ricxapp:8080"],
            "Meid": meid,
            "RANFunctionID": ran_function_id,
            "SubscriptionDetails": [
                {
                    "XappEventInstanceId": 1,
                    "EventTriggers": [
                        # Formato real E2SM-KPM Event Trigger Definition (octets em hexa)
                        # Este é um mockup do payload de Event Trigger (Reporting Period)
                        "00000000"
                    ],
                    "ActionToBeSetupList": [
                        {
                            "ActionID": 1,
                            "ActionType": "report",
                            "ActionDefinition": [
                                # Formato real E2SM-KPM Action Definition
                                "00000000"
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
        
        try:
            url = f"{self.submgr_url}/ric/v1/subscriptions"
            logger.info(f"Enviando REST SubReq para {url} - MEID: {meid}")
            
            # Na integração real, descomentar a chamada:
            # response = requests.post(url, json=payload, timeout=5)
            # response.raise_for_status()
            # data = response.json()
            # sub_id = data.get("SubscriptionId", "sim_sub_01")
            
            sub_id = "sim_sub_01"  # Mock para teste sem RIC real
            
            ctx = SubscriptionContext(
                subscription_id=sub_id,
                request_id=1,
                instance_id=1,
                ran_function_id=ran_function_id,
                meid=meid,
                status="ACTIVE",
                created_at=datetime.now()
            )
            return ctx
        except Exception as e:
            logger.error(f"Falha na subscrição do MEID {meid}: {e}")
            return None
