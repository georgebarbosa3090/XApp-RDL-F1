import threading
import requests
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from src.observability.logging import setup_logger
from src.e2.e2ap.subscription import build_ric_subscription_request_payload

logger = setup_logger("SubscriptionManager")

# Caminho em que o SubMgr (O-RAN SC) entrega o resultado assíncrono da subscrição.
SUBSCRIPTION_NOTIFICATION_PATH = "/ric/v1/subscriptions/response"


@dataclass
class SubscriptionContext:
    subscription_id: str
    ran_function_id: int
    meid: str
    status: str
    created_at: datetime
    xapp_event_instance_id: int = 1
    e2_event_instance_id: Optional[int] = None
    error_cause: Optional[str] = None


class SubscriptionManager:
    """
    Cliente da API REST de subscrição do SubMgr.

    O ``POST /ric/v1/subscriptions`` apenas aceita o pedido (``SubscriptionResponse``
    com ``SubscriptionId``); o resultado E2 chega depois, por ``POST`` do SubMgr em
    ``SUBSCRIPTION_NOTIFICATION_PATH`` no endpoint HTTP da xApp. Até lá a subscrição
    fica ``PENDING`` e não deve ser tratada como ativa.
    """

    def __init__(self, submgr_url: str = "http://service-ricplt-submgr-http.ricplt:8088", timeout_s: float = 5.0):
        self.submgr_url = submgr_url.rstrip("/")
        self.timeout_s = timeout_s
        self.active_subscriptions: Dict[str, SubscriptionContext] = {}
        self._by_subscription_id: Dict[str, SubscriptionContext] = {}
        self._next_event_instance_id = 1
        self._lock = threading.Lock()

    def request_kpm_subscription(self, meid: str, ran_function_id: int, period_ms: int = 200) -> Optional[SubscriptionContext]:
        """Solicita uma subscrição E2SM-KPM ao SubMgr; retorna o contexto ``PENDING`` ou ``None``."""
        with self._lock:
            event_instance_id = self._next_event_instance_id
            self._next_event_instance_id = 1 if event_instance_id >= 65535 else event_instance_id + 1

        try:
            payload = build_ric_subscription_request_payload(
                target_node=meid,
                ran_function_id=ran_function_id,
                report_period_ms=period_ms,
                xapp_event_instance_id=event_instance_id,
            )
            url = f"{self.submgr_url}/ric/v1/subscriptions"
            logger.info(f"Enviando REST SubReq para {url} - MEID: {meid}")

            response = requests.post(url, json=payload, timeout=self.timeout_s)
            response.raise_for_status()
            data = response.json() if response.content else {}
            sub_id = data.get("SubscriptionId") if isinstance(data, dict) else None
            if not isinstance(sub_id, str) or not sub_id:
                logger.error("SubMgr aceitou o pedido sem SubscriptionId; subscrição não rastreável.", meid=meid)
                return None
        except Exception as e:
            logger.error(f"Falha na subscricao do MEID {meid} junto ao SubMgr: {e}")
            return None

        ctx = SubscriptionContext(
            subscription_id=sub_id,
            ran_function_id=int(ran_function_id),
            meid=meid,
            status="PENDING",
            created_at=datetime.now(),
            xapp_event_instance_id=event_instance_id,
        )
        with self._lock:
            self.active_subscriptions[meid] = ctx
            self._by_subscription_id[sub_id] = ctx
        return ctx

    def handle_notification(self, body: Any) -> Optional[Tuple[SubscriptionContext, bool]]:
        """
        Processa o ``SubscriptionResponse`` assíncrono enviado pelo SubMgr.

        Retorna ``(contexto, sucesso)``; ``None`` se a notificação não corresponde a
        nenhuma subscrição pendente. Sucesso exige ``E2EventInstanceId`` positivo e
        ausência de ``ErrorCause`` em todas as instâncias.
        """
        if not isinstance(body, dict):
            return None
        sub_id = body.get("SubscriptionId")
        instances = body.get("SubscriptionInstances")
        with self._lock:
            ctx = self._by_subscription_id.get(sub_id) if isinstance(sub_id, str) else None
        if ctx is None:
            logger.warning("Notificação de subscrição sem correspondência local", subscription_id=sub_id)
            return None
        if not isinstance(instances, list) or not instances:
            ctx.status = "FAILED"
            ctx.error_cause = "missing SubscriptionInstances"
            return ctx, False

        success = True
        for instance in instances:
            if not isinstance(instance, dict):
                success = False
                ctx.error_cause = "malformed SubscriptionInstance"
                continue
            e2_id = instance.get("E2EventInstanceId")
            error_cause = instance.get("ErrorCause")
            if error_cause or isinstance(e2_id, bool) or not isinstance(e2_id, int) or e2_id <= 0:
                success = False
                ctx.error_cause = str(error_cause or "invalid E2EventInstanceId")
            else:
                ctx.e2_event_instance_id = e2_id
        ctx.status = "ACTIVE" if success else "FAILED"
        if not success:
            with self._lock:
                self.active_subscriptions.pop(ctx.meid, None)
                self._by_subscription_id.pop(ctx.subscription_id, None)
        return ctx, success

    def delete_subscription(self, meid: str) -> bool:
        """
        Encerra uma subscrição no Subscription Manager (REST DELETE).
        """
        ctx = self.active_subscriptions.get(meid)
        if not ctx:
            return False
        try:
            url = f"{self.submgr_url}/ric/v1/subscriptions/{ctx.subscription_id}"
            response = requests.delete(url, timeout=self.timeout_s)
            if response.status_code in (200, 204, 404):
                with self._lock:
                    self.active_subscriptions.pop(meid, None)
                    self._by_subscription_id.pop(ctx.subscription_id, None)
                logger.info(f"Subscricao {ctx.subscription_id} encerrada para MEID {meid}")
                return True
        except Exception as e:
            logger.warning(f"Falha ao encerrar subscricao {ctx.subscription_id} do MEID {meid}: {e}")
        return False

    def teardown_all(self) -> int:
        """Encerra todas as subscrições ativas durante o desligamento gracioso."""
        closed = 0
        for meid in list(self.active_subscriptions.keys()):
            if self.delete_subscription(meid):
                closed += 1
        return closed
