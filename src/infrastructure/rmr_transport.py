"""
Envio RMR com MEID explícito.

O ``ricxappframe`` (3.2.x) expõe ``rmr_send(payload, mtype, retries=100)``: não há
parâmetro para o MEID, e sem MEID o E2Term não consegue rotear mensagens E2AP
(RIC_CONTROL_REQUEST etc.) ao E2 Node correto. Este módulo aloca o buffer com
``rmr.rmr_alloc_msg(..., meid=...)`` e faz o envio com a mesma política de retry
do framework, liberando o buffer em todos os caminhos.

Clientes em processo (mocks de teste e o ``MockRMRXapp`` offline) implementam
``rmr_send_with_meid(payload, mtype, meid) -> bool``. Um cliente que não ofereça
nenhuma das duas formas é recusado: enviar sem MEID é o defeito que este módulo
existe para evitar.
"""

from typing import Any, Optional

from src.observability.logging import setup_logger

logger = setup_logger("RmrTransport")

try:  # pragma: no cover - depende da biblioteca C librmr_si
    from ricxappframe.rmr import rmr as _rmr
except (ImportError, OSError, Exception):  # pragma: no cover
    _rmr = None

DEFAULT_RETRIES = 100


def send_rmr_message(
    client: Any,
    payload: bytes,
    mtype: int,
    meid: str,
    retries: int = DEFAULT_RETRIES,
    rmr_module: Optional[Any] = None,
) -> bool:
    """Envia ``payload`` com ``mtype`` ao E2 Node identificado por ``meid``."""
    if client is None:
        return False
    if not isinstance(meid, str) or not meid.strip():
        logger.error("Envio RMR recusado: MEID ausente.", mtype=mtype)
        return False
    if not isinstance(payload, (bytes, bytearray)):
        logger.error("Envio RMR recusado: payload deve ser bytes.", mtype=mtype)
        return False

    rmr = rmr_module if rmr_module is not None else _rmr
    mrc = getattr(client, "_mrc", None)
    if mrc is not None and rmr is not None:
        return _send_via_rmr_library(rmr, mrc, bytes(payload), mtype, meid, retries)

    send_with_meid = getattr(client, "rmr_send_with_meid", None)
    if callable(send_with_meid):
        return bool(send_with_meid(bytes(payload), mtype, meid))

    logger.error(
        "Cliente RMR não suporta envio com MEID; mensagem não enviada.",
        mtype=mtype,
        client=type(client).__name__,
    )
    return False


def _send_via_rmr_library(rmr: Any, mrc: Any, payload: bytes, mtype: int, meid: str, retries: int) -> bool:
    sbuf = rmr.rmr_alloc_msg(
        vctx=mrc,
        size=len(payload),
        payload=payload,
        gen_transaction_id=True,
        mtype=mtype,
        meid=meid,
    )
    try:
        for _ in range(max(1, int(retries))):
            sbuf = rmr.rmr_send_msg(mrc, sbuf)
            if sbuf.contents.state == rmr.RMR_OK:
                return True
            if sbuf.contents.state != rmr.RMR_ERR_RETRY:
                logger.error(
                    "RMR rejeitou a mensagem",
                    mtype=mtype,
                    meid=meid,
                    state=sbuf.contents.state,
                )
                return False
        logger.error("RMR esgotou as tentativas de envio", mtype=mtype, meid=meid)
        return False
    finally:
        rmr.rmr_free_msg(sbuf)
