"""
Coletor e Validador de Artefatos Brutos E2SM-KPM (Gate 1)
Gera e gerencia a hierarquia de artefatos rastreáveis de telemetria bruta (.raw) e metadados formais:
experiments/run-XXXX/e2/kpm/
  ├── subscription_request.raw
  ├── subscription_response.raw
  ├── indication_0001.raw / indication_0001.json
  ├── indication_0002.raw / indication_0002.json
  └── metadata.json
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from src.e2.kpm_decoder import KpmDecoder
from src.observability.logging import setup_logger

logger = setup_logger("KpmRawCollector")

@dataclass
class RunMetadata:
    git_commit: str
    timestamp: str
    seed: int
    ns3_version: str = "3.48"
    five_g_lena_version: str = "5.1"
    nori_commit: str = "8a4f91d"
    e2sim_commit: str = "b7e21a0"
    oran_sc_release: str = "Release I/J"
    e2ap_version: str = "v02.03"
    e2sm_kpm_version: str = "v03.00"
    e2sm_rc_version: str = "v01.03"
    ran_function_id: int = 2
    node_id: str = "gnb_01"
    total_indications: int = 0
    sha256_checksums: Dict[str, str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["5g_lena_version"] = d.pop("five_g_lena_version")
        return d

class KpmRawCollector:
    """
    Gerenciador de integridade experimental e telemetria bruta APER para o Gate 1.
    """
    def __init__(self, base_exp_dir: str = "experiments"):
        self.base_exp_dir = base_exp_dir
        self.decoder = KpmDecoder()

    def create_run_session(self, run_id: str, seed: int = 1001, git_commit: str = "06b2a556") -> str:
        kpm_dir = os.path.join(self.base_exp_dir, run_id, "e2", "kpm")
        os.makedirs(kpm_dir, exist_ok=True)
        return kpm_dir

    def save_subscription_artifacts(self, kpm_dir: str, req_raw: bytes, resp_raw: bytes) -> Tuple[str, str]:
        req_path = os.path.join(kpm_dir, "subscription_request.raw")
        resp_path = os.path.join(kpm_dir, "subscription_response.raw")
        with open(req_path, "wb") as f:
            f.write(req_raw)
        with open(resp_path, "wb") as f:
            f.write(resp_raw)
        return req_path, resp_path

    def save_indication(self, kpm_dir: str, index: int, raw_bytes: bytes) -> Tuple[str, str]:
        raw_name = f"indication_{index:04d}.raw"
        json_name = f"indication_{index:04d}.json"
        raw_path = os.path.join(kpm_dir, raw_name)
        json_path = os.path.join(kpm_dir, json_name)

        with open(raw_path, "wb") as f:
            f.write(raw_bytes)

        # Decodifica estritamente via ASN.1 APER sem sintetizar dados
        decoded_reports = self.decoder.decode_indication(raw_bytes)
        json_content = {
            "index": index,
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "byte_length": len(raw_bytes),
            "reports": decoded_reports
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2)

        return raw_path, json_path

    def finalize_run_metadata(
        self,
        kpm_dir: str,
        seed: int,
        git_commit: str = "06b2a556",
        node_id: str = "gnb_01"
    ) -> str:
        # Calcula hashes de todos os arquivos brutos presentes no diretório
        checksums = {}
        indication_count = 0
        for fname in sorted(os.listdir(kpm_dir)):
            if fname.endswith(".raw"):
                fpath = os.path.join(kpm_dir, fname)
                with open(fpath, "rb") as f:
                    content = f.read()
                    checksums[fname] = hashlib.sha256(content).hexdigest()
                if fname.startswith("indication_"):
                    indication_count += 1

        metadata = RunMetadata(
            git_commit=git_commit,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            seed=seed,
            node_id=node_id,
            total_indications=indication_count,
            sha256_checksums=checksums
        )

        meta_path = os.path.join(kpm_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        logger.info(f"Metadados de telemetria E2 KPM consolidados em {meta_path} ({indication_count} indicações)")
        return meta_path
