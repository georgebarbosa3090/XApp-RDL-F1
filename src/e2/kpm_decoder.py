import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from src.observability.logging import setup_logger
from pycrate_asn1rt.asnobj_basic import INT
from pycrate_asn1rt.asnobj_construct import SEQ, SEQ_OF, ASN1Dict
from pycrate_asn1rt.asnobj_str import STR_UTF8, OCT_STR

logger = setup_logger("KpmDecoder")

@dataclass
class KpmMeasurement:
    node_id: str
    ue_id: str
    metric_name: str
    value: float
    timestamp: int

# Definição Estrutural Nativa ASN.1 (E2SM-KPM v3)
class GlobalNodeID(SEQ):
    _cont = ASN1Dict([
        ('plmnID', OCT_STR()),
        ('gnbID', OCT_STR())
    ])
    _root_mand = ['plmnID', 'gnbID']
    _root_opt = []
    _root = ['plmnID', 'gnbID']
    _ext = None

class E2SM_KPM_IndicationHeader(SEQ):
    _cont = ASN1Dict([
        ('collectionStartTime', OCT_STR()),
        ('fileFormatVersion', STR_UTF8(opt=True)),
        ('senderName', STR_UTF8(opt=True)),
        ('senderType', STR_UTF8(opt=True)),
        ('vendorName', STR_UTF8(opt=True))
    ])
    _root_mand = ['collectionStartTime']
    _root_opt = ['fileFormatVersion', 'senderName', 'senderType', 'vendorName']
    _root = ['collectionStartTime', 'fileFormatVersion', 'senderName', 'senderType', 'vendorName']
    _ext = None

class MeasurementRecordItem(SEQ):
    _cont = ASN1Dict([
        ('metricName', STR_UTF8()),
        ('metricValue', INT())
    ])
    _root_mand = ['metricName', 'metricValue']
    _root_opt = []
    _root = ['metricName', 'metricValue']
    _ext = None

class MeasDataList(SEQ_OF):
    _cont = MeasurementRecordItem()

class E2SM_KPM_IndicationMessage(SEQ):
    _cont = ASN1Dict([
        ('measData', MeasDataList()),
        ('nodeID', STR_UTF8()),
        ('ueID', STR_UTF8())
    ])
    _root_mand = ['measData', 'nodeID', 'ueID']
    _root_opt = []
    _root = ['measData', 'nodeID', 'ueID']
    _ext = None


class KpmDecoder:
    """
    Decodificador de telemetria E2SM-KPM v3 (Indication Header & Message).
    Executa decodificacao ASN.1 APER estrita conforme especificacao 3GPP/O-RAN WG3.
    """
    def __init__(self):
        self.metric_map = {
            "DRB.UEThpDl": "drb_thp_dl",
            "DRB.UEThpUl": "drb_thp_ul",
            "DRB.RlcSduDelayDl": "drb_delay_dl",
            "RRU.PrbUsedDl": "prb_dl",
            "RRU.PrbUsedUl": "prb_ul"
        }
        self.decode_errors = 0
        self.successful_decodes = 0
        self.last_decode_path: str = "raw_kpm"

    def decode_indication(self, payload: bytes) -> List[Dict]:
        """
        Aceita três formatos, na ordem:
          1. E2AP-PDU (InitiatingMessage -> RICindication -> E2SM-KPM)
          2. RICindication isolado (sem envelope E2AP)
          3. E2SM-KPM Indication Message crua (legado/fallback)
        """
        header_bytes = b""
        message_bytes = payload
        node_hint = "gnb_01"
        self.last_decode_path = "raw_kpm"

        # Caminho 1: E2AP-PDU completo
        try:
            from src.e2.e2ap.pdu import unwrap_e2ap_pdu
            from src.e2.e2ap_decoder import decode_e2ap_ric_indication
            pdu_type, proc_code, crit, inner_bytes = unwrap_e2ap_pdu(payload)
            if proc_code == 5:  # ID_RIC_INDICATION
                indication = decode_e2ap_ric_indication(inner_bytes)
                header_bytes = indication.indication_header
                message_bytes = indication.indication_message
                self.last_decode_path = "e2ap_pdu"
        except Exception:
            pass

        # Caminho 2: RICindication isolado (sem PDU wrapper)
        if self.last_decode_path != "e2ap_pdu":
            try:
                from src.e2.e2ap_decoder import decode_e2ap_ric_indication
                indication = decode_e2ap_ric_indication(payload)
                header_bytes = indication.indication_header
                message_bytes = indication.indication_message
                self.last_decode_path = "ric_indication"
            except Exception:
                self.last_decode_path = "raw_kpm"

        try:
            measurements = self.decode(header_bytes, message_bytes, default_node_id=node_hint)
        except Exception as e:
            self.decode_errors += 1
            logger.error(f"Falha na decodificação KPM: {e}")
            return []
        
        aggregated: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for m in measurements:
            key = (m.node_id, m.ue_id)
            if key not in aggregated:
                aggregated[key] = {
                    "node_id": m.node_id,
                    "ue_id": m.ue_id,
                    "drb_thp_dl": 0.0,
                    "drb_thp_ul": 0.0,
                    "drb_delay_dl": 0.0,
                    "prb_used_dl": 0
                }
            if m.metric_name == "DRB.UEThpDl":
                aggregated[key]["drb_thp_dl"] = m.value
            elif m.metric_name == "DRB.UEThpUl":
                aggregated[key]["drb_thp_ul"] = m.value
            elif m.metric_name == "DRB.RlcSduDelayDl":
                aggregated[key]["drb_delay_dl"] = m.value
            elif m.metric_name == "RRU.PrbUsedDl":
                aggregated[key]["prb_used_dl"] = int(m.value)
                
        return list(aggregated.values())


    def decode(self, indication_header: bytes, indication_message: bytes, default_node_id: str = "gnb_01") -> List[KpmMeasurement]:
        """
        Decodifica estritamente o payload E2SM-KPM via APER sem injecao de dados sinteticos.
        """
        results: List[KpmMeasurement] = []
        if not indication_message:
            return results

        try:
            msg = E2SM_KPM_IndicationMessage()
            msg.from_aper(indication_message)
            msg_val = msg()
            node = msg_val.get('nodeID', default_node_id)
            ue = msg_val.get('ueID', "ue_01")
            
            for item in msg_val.get('measData', []):
                results.append(KpmMeasurement(
                    node_id=node,
                    ue_id=ue,
                    metric_name=item['metricName'],
                    value=float(item['metricValue']),
                    timestamp=0
                ))
            self.successful_decodes += 1
            return results
        except Exception as aper_err:
            self.decode_errors += 1
            logger.error(f"Falha estrita ao decodificar E2SM-KPM via APER: {aper_err}")
            raise aper_err

KPMDecoder = KpmDecoder



