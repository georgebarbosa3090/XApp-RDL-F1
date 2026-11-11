"""
Interceptação por rota (nível 2 da governança).

Uma xApp de terceiros que não pode ser alterada continua enviando RIC Control Request (RMR 12040).
Uma entrada de rota com remetente (``mse|12040,<origem da xApp>|-1|<RDL>``) entrega essa mensagem à
RDL em vez do E2Term. A RDL:

1. decodifica o E2AP e o E2SM-RC (``decode_intercepted_control``);
2. transforma o controle em proposta com a identidade e a prioridade do registro
   (``intercept_requestor_ids``);
3. arbitra como qualquer proposta; se a ação vencer, a RDL a envia ao nó com o seu próprio
   RICrequestID;
4. responde à xApp de origem com RIC Control Acknowledge ou Failure (RMR 12041/12042, por
   *return to sender*), com o RICrequestID e o RANfunctionID que ela usou.

Formatos de E2SM-RC entendidos:

- E2SM-RC v03.01 do NORI, Style 2 / Action 6 (cotas de PRB por fatia): vira ``PRB_QUOTA`` com o teto
  da fatia SST 1 (a convenção da RDL: eMBB recebe ``v``, URLLC ``100 − v``); exige o ASN.1 do NORI
  em cache (``src/e2/v3/codec.py``);
- o perfil simplificado da própria RDL (``src/e2/rc_encoder.py``): um parâmetro por mensagem.

Outros formatos são recusados com Failure; o controle não chega ao nó.
"""

from dataclasses import dataclass
from typing import Optional

from src.e2.v3 import codec as v3

# Cause ::= CHOICE { ricRequest CauseRICrequest, ... } (E2AP v03.01, 6 alternativas na raiz)
# CauseRICrequest ::= ENUMERATED { ..., control-failed-to-execute (11), ..., unspecified (13), ... }
CAUSE_RIC_REQUEST = 0
CAUSE_CONTROL_FAILED_TO_EXECUTE = 11
CAUSE_UNSPECIFIED = 13


class InterceptionError(ValueError):
    pass


@dataclass
class InterceptedControl:
    requestor_id: int
    instance_id: int
    ran_function_id: int
    parameter: str
    value: float
    encoding: str          # "E2SM-RC-v03.01-slice-quota" ou "RDL-RC-profile"


_E2SM_CODEC = None


def _nori_codec():
    """Codec E2SM do NORI, se o ASN.1 estiver em cache (sem baixar nada em tempo de execução)."""
    global _E2SM_CODEC
    if _E2SM_CODEC is None:
        try:
            _E2SM_CODEC = v3.E2smCodec(download=False)
        except Exception:
            _E2SM_CODEC = False
    return _E2SM_CODEC or None


def _decode_rc_message(message: bytes):
    codec = _nori_codec()
    if codec is not None:
        try:
            quotas = codec.rc_decode_slice_quotas(message)
        except Exception:
            quotas = []
        if quotas:
            embb = next((q for q in quotas if q.sst == 1), quotas[0])
            return "PRB_QUOTA", float(embb.max_prb_ratio), "E2SM-RC-v03.01-slice-quota"
    try:
        from src.e2.rc_encoder import PARAM_PROFILES, RCEncoder
        params = RCEncoder().decode_control_message(message)["ricControlActionParameters"]
        item = params[0]
        by_id = {p["id"]: name for name, p in PARAM_PROFILES.items()}
        name = item.get("ranParameterName") or by_id.get(item["ranParameterID"])
        if name not in PARAM_PROFILES:
            raise InterceptionError(f"parâmetro E2SM-RC desconhecido: {item.get('ranParameterID')}")
        return name, float(item["ranParameterValue"]) / float(PARAM_PROFILES[name]["scale"]), "RDL-RC-profile"
    except InterceptionError:
        raise
    except Exception as exc:
        raise InterceptionError(f"E2SM-RC não reconhecido: {exc}") from exc


def decode_intercepted_control(payload: bytes) -> InterceptedControl:
    try:
        pdu = v3.decode_e2ap_pdu(payload)
    except Exception as exc:
        raise InterceptionError(f"E2AP inválido: {exc}") from exc
    if pdu.get("pdu_type") != "initiatingMessage" or pdu.get("procedure_code") != v3.PROC_RIC_CONTROL:
        raise InterceptionError(f"não é RIC Control Request: {pdu.get('pdu_type')} {pdu.get('procedure_code')}")
    if "control_message" not in pdu or "ric_requestor_id" not in pdu:
        raise InterceptionError("RIC Control Request sem mensagem ou sem RICrequestID")
    parameter, value, encoding = _decode_rc_message(pdu["control_message"])
    return InterceptedControl(requestor_id=pdu["ric_requestor_id"], instance_id=pdu["ric_instance_id"],
                              ran_function_id=pdu.get("ran_function_id", 0), parameter=parameter,
                              value=value, encoding=encoding)


def _ids(requestor_id: int, instance_id: int, ran_function_id: int):
    return [(v3.IE_RIC_REQUEST_ID, v3.CRIT_REJECT, v3._ric_request_id(requestor_id, instance_id)),
            (v3.IE_RAN_FUNCTION_ID, v3.CRIT_REJECT, v3.AperWriter().constrained(ran_function_id, 0, 4095).to_bytes())]


def build_control_ack(requestor_id: int, instance_id: int, ran_function_id: int) -> bytes:
    """RICcontrolAcknowledge (successfulOutcome) com os IDs da xApp de origem."""
    return v3.encode_e2ap_pdu(v3.PDU_SUCCESSFUL, v3.PROC_RIC_CONTROL, v3.CRIT_REJECT,
                              _ids(requestor_id, instance_id, ran_function_id))


def build_control_failure(requestor_id: int, instance_id: int, ran_function_id: int,
                          cause: int = CAUSE_CONTROL_FAILED_TO_EXECUTE) -> bytes:
    """RICcontrolFailure (unsuccessfulOutcome) com Cause ricRequest."""
    cause_bytes = (v3.AperWriter().bits(0, 1).constrained(CAUSE_RIC_REQUEST, 0, 5)
                   .bits(0, 1).constrained(cause, 0, 13).to_bytes())
    ies = _ids(requestor_id, instance_id, ran_function_id) + [(v3.IE_CAUSE, v3.CRIT_IGNORE, cause_bytes)]
    return v3.encode_e2ap_pdu(v3.PDU_UNSUCCESSFUL, v3.PROC_RIC_CONTROL, v3.CRIT_REJECT, ies)


def cause_of(failure_pdu: bytes) -> Optional[int]:
    """Valor de CauseRICrequest de um Failure montado por ``build_control_failure`` (para testes e logs)."""
    raw = v3.decode_e2ap_pdu(failure_pdu).get("cause_raw")
    if not raw:
        return None
    r = v3.AperReader(bytes.fromhex(raw))
    r.bits(1)
    if r.constrained(0, 5) != CAUSE_RIC_REQUEST:
        return None
    r.bits(1)
    return r.constrained(0, 13)
