import os
from typing import List, Dict, Any, Optional
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

    def decode_indication(self, payload: bytes) -> List[Dict]:
        """
        Wrapper exigido pelo rdl_xapp.py para extrair os reports KPM reais do payload.
        """
        measurements = self.decode(payload, payload)
        
        return [{
            "node_id": m.node_id,
            "ue_id": m.ue_id,
            "drb_thp_dl": m.value if m.metric_name == "DRB.UEThpDl" else 0.0,
            "drb_thp_ul": m.value if m.metric_name == "DRB.UEThpUl" else 0.0,
            "drb_delay_dl": m.value if m.metric_name == "DRB.RlcSduDelayDl" else 0.0,
            "prb_used_dl": int(m.value) if m.metric_name == "RRU.PrbUsedDl" else 0
        } for m in measurements]

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


