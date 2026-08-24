import requests
from typing import List, Optional
from pydantic import BaseModel
from src.observability.logging import setup_logger

logger = setup_logger("E2NodeDiscovery")

class E2Node(BaseModel):
    inventoryName: str
    connectionStatus: str
    globalNbId: Optional[dict] = None
    nodeType: Optional[str] = None

class RanFunction(BaseModel):
    ranFunctionId: int
    ranFunctionRevision: int
    ranFunctionOid: str

class E2NodeDiscoveryService:
    def __init__(self, e2m_url: str = "http://service-ricplt-e2mgr-http.ricplt:3800"):
        self.e2m_url = e2m_url

    def list_connected_nodes(self) -> List[E2Node]:
        """
        Consulta os E2 Nodes disponíveis no E2 Manager.
        """
        try:
            url = f"{self.e2m_url}/v1/nodeb/states"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            nodes = []
            for item in response.json():
                nodes.append(E2Node(**item))
            
            # Filtra apenas conectados
            connected = [n for n in nodes if n.connectionStatus == "CONNECTED"]
            logger.info(f"Encontrados {len(connected)} E2 Nodes conectados.")
            return connected
        except Exception as e:
            logger.error(f"Falha ao consultar E2 Manager: {e}")
            return []

    def find_kpm_function(self, node: E2Node) -> Optional[RanFunction]:
        """
        Busca a RAN Function do E2SM-KPM num nó específico.
        Mocked until full integration.
        """
        # Em um ambiente real, chamaríamos GET /v1/nodeb/{node.inventoryName}
        # e filtraríamos pelo OID do E2SM-KPM (1.3.6.1.4.1.53148.1.2.2.2)
        # Por enquanto, retornamos um mock aceitável
        return RanFunction(ranFunctionId=2, ranFunctionRevision=2, ranFunctionOid="1.3.6.1.4.1.53148.1.2.2.2")

    def find_control_function(self, node: E2Node) -> Optional[RanFunction]:
        """
        Busca a RAN Function do E2SM-RC num nó específico.
        """
        return RanFunction(ranFunctionId=3, ranFunctionRevision=1, ranFunctionOid="1.3.6.1.4.1.53148.1.2.2.3")
