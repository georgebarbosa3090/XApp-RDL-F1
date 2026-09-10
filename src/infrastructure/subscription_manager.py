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

from src.e2.e2ap.subscription import build_ric_subscription_request_payload

class SubscriptionManager:
    def __init__(self, submgr_url: str = "http://service-ricplt-submgr-http.ricplt:8088"):
        self.submgr_url = submgr_url

    def request_kpm_subscription(self, meid: str, ran_function_id: int, period_ms: int = 200) -> Optional[SubscriptionContext]:
        """
        Solicita uma subscrição E2SM-KPM com payloads APER normativos ao Subscription Manager.
        """
        payload = build_ric_subscription_request_payload(
            target_node=meid,
            ran_function_id=ran_function_id,
            report_period_ms=period_ms
        )

        
        try:
            url = f"{self.submgr_url}/ric/v1/subscriptions"
            logger.info(f"Enviando REST SubReq para {url} - MEID: {meid}")
            
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json() if response.content else {}
            sub_id = data.get("SubscriptionId") or data.get("subscription_id") or f"sub-{meid}-{ran_function_id}"
            
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
            logger.error(f"Falha na subscricao do MEID {meid} junto ao SubMgr: {e}")
            return None

