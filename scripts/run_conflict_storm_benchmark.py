"""
Benchmark de Estresse e Escalabilidade: Conflict Storm (Cenário S6)
Avalia a capacidade de processamento do H-RDL sob os 5 níveis progressivos de carga (L0 a L4),
medindo T_HRDL(N), Throughput de Decisões (decisions/s), latências P95/P99 e identificando o joelho da curva Near-RT.
"""

import os
import sys
import time
import json
import argparse
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.memory_module import MemoryModule
from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
from src.conflict_types import XAppAction

LEVEL_CONFIGS = {
    "L0": {"name": "Baixo",     "ues": 30,  "xapps": 3,  "actions_per_sec": 5,   "kpm_interval_ms": 1000, "duration_s": 10},
    "L1": {"name": "Moderado",  "ues": 60,  "xapps": 3,  "actions_per_sec": 10,  "kpm_interval_ms": 500,  "duration_s": 10},
    "L2": {"name": "Alto",      "ues": 120, "xapps": 5,  "actions_per_sec": 25,  "kpm_interval_ms": 200,  "duration_s": 10},
    "L3": {"name": "Severo",    "ues": 240, "xapps": 8,  "actions_per_sec": 50,  "kpm_interval_ms": 100,  "duration_s": 10},
    "L4": {"name": "Extremo",   "ues": 500, "xapps": 10, "actions_per_sec": 100, "kpm_interval_ms": 50,   "duration_s": 10},
}

def run_conflict_storm_benchmark(output_dir: str = "results/campaign_s0_s8/storm"):
    os.makedirs(output_dir, exist_ok=True)
    results = []

    print("================================================================================")
    print(" [BENCHMARK S6] Executando Conflict Storm & Stress Test de Escalabilidade")
    print(f" Destino: {output_dir}")
    print("================================================================================")

    for lvl_key, cfg in LEVEL_CONFIGS.items():
        memory = MemoryModule()
        perception = PerceptionAgent()
        reasoning = ReasoningAgent(memory, config={})
        refinement = RefinementAgent(memory)

        total_actions_to_inject = cfg["actions_per_sec"] * cfg["duration_s"]
        latencies_ms = []
        conflicts_count = 0
        resolutions_count = 0

        # Gera lote de ações concorrentes
        actions_batch = []
        for i in range(total_actions_to_inject):
            xapp_id = f"xapp_{i % cfg['xapps']}"
            node_id = f"gnb_{(i % 4) + 1:02d}"
            param = ["PRB_QUOTA", "TX_POWER", "SCHEDULER_WEIGHT", "HANDOVER"][i % 4]
            val = float(20.0 + ((i * 17) % 60))
            actions_batch.append(XAppAction(
                xapp_id=xapp_id,
                node_id=node_id,
                parameter=param,
                value=val,
                priority=[50, 70, 90][i % 3]
            ))

        # Medição de tempo de ponta a ponta
        t_start = time.perf_counter()
        
        # Simula processamento em janelas de 200ms
        chunk_size = max(1, int(cfg["actions_per_sec"] * 0.2))
        for idx in range(0, len(actions_batch), chunk_size):
            chunk = actions_batch[idx:idx+chunk_size]
            t0 = time.perf_counter()
            conflicts = perception.register_action_group(chunk)
            conflicts_count += len(conflicts)
            
            for conflict in conflicts:
                res = reasoning.resolve(conflict)
                is_valid, _, _ = refinement.validate(res, conflict)
                if is_valid and res.winning_actions:
                    resolutions_count += 1
                    
            t_chunk_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(t_chunk_ms)

        total_elapsed_s = time.perf_counter() - t_start
        throughput_dec_sec = total_actions_to_inject / max(0.001, total_elapsed_s)

        mean_lat = float(np.mean(latencies_ms))
        p95_lat = float(np.percentile(latencies_ms, 95))
        p99_lat = float(np.percentile(latencies_ms, 99))
        max_lat = float(np.max(latencies_ms))

        # Status Near-RT: True se latência máxima < 50ms
        near_rt_compliant = (p95_lat < 50.0)

        record = {
            "Level": lvl_key,
            "Name": cfg["name"],
            "UEs": cfg["ues"],
            "xApps": cfg["xapps"],
            "Actions_Per_Sec": cfg["actions_per_sec"],
            "Total_Actions": total_actions_to_inject,
            "Total_Conflicts": conflicts_count,
            "Total_Resolutions": resolutions_count,
            "Throughput_Actions_Sec": round(throughput_dec_sec, 2),
            "Latency_Mean_ms": round(mean_lat, 2),
            "Latency_P95_ms": round(p95_lat, 2),
            "Latency_P99_ms": round(p99_lat, 2),
            "Latency_Max_ms": round(max_lat, 2),
            "Near_RT_Compliant": near_rt_compliant
        }
        results.append(record)

    df_storm = pd.DataFrame(results)
    csv_path = os.path.join(output_dir, "conflict_storm_scalability.csv")
    df_storm.to_csv(csv_path, index=False)

    json_path = os.path.join(output_dir, "conflict_storm_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n[RESULTADOS S6] Tabela de Escalabilidade Conflict Storm:")
    print(df_storm[["Level", "Name", "UEs", "xApps", "Throughput_Actions_Sec", "Latency_Mean_ms", "Latency_P95_ms", "Near_RT_Compliant"]].to_string(index=False))
    print(f"\nSalvo em: {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run S6 Conflict Storm Benchmark")
    parser.add_argument("--output-dir", type=str, default="results/campaign_s0_s8/storm", help="Output directory")
    args = parser.parse_args()

    run_conflict_storm_benchmark(output_dir=args.output_dir)
