"""Offline decision-processing microbenchmark; this is not a RAN simulation.

The generated action batches are synthetic software workload only. No UEs,
radio channel, ns-3, 5G-LENA, E2, or Near-RT behavior is modeled here.
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
from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.core.refinement import Refinement
from src.conflict_types import XAppAction

LEVEL_CONFIGS = {
    "L0": {"name": "Baixo",     "xapps": 3,  "actions_per_sec": 5,   "duration_s": 10},
    "L1": {"name": "Moderado",  "xapps": 3,  "actions_per_sec": 10,  "duration_s": 10},
    "L2": {"name": "Alto",      "xapps": 5,  "actions_per_sec": 25,  "duration_s": 10},
    "L3": {"name": "Severo",    "xapps": 8,  "actions_per_sec": 50,  "duration_s": 10},
    "L4": {"name": "Extremo",   "xapps": 10, "actions_per_sec": 100, "duration_s": 10},
}

def run_conflict_storm_benchmark(output_dir: str = "results/campaign_s0_s8/storm"):
    os.makedirs(output_dir, exist_ok=True)
    results = []

    print("================================================================================")
    print(" [OFFLINE MICROBENCHMARK] Decision-processing workload; not a RAN experiment.")
    print(f" Destino: {output_dir}")
    print("================================================================================")

    for lvl_key, cfg in LEVEL_CONFIGS.items():
        memory = MemoryModule()
        perception = Perception()
        reasoning = Reasoning(memory, config={})
        refinement = Refinement(memory)

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

        record = {
            "Level": lvl_key,
            "Name": cfg["name"],
            "xApps": cfg["xapps"],
            "Actions_Per_Sec": cfg["actions_per_sec"],
            "Total_Actions": total_actions_to_inject,
            "Total_Conflicts": conflicts_count,
            "Total_Resolutions": resolutions_count,
            "Throughput_Actions_Sec": round(throughput_dec_sec, 2),
            "Latency_Mean_ms": round(mean_lat, 2),
            "Latency_P95_ms": round(p95_lat, 2),
            "Latency_P99_ms": round(p99_lat, 2),
            "Latency_Max_ms": round(max_lat, 2)
        }
        results.append(record)

    df_storm = pd.DataFrame(results)
    csv_path = os.path.join(output_dir, "conflict_storm_scalability.csv")
    df_storm.to_csv(csv_path, index=False)

    json_path = os.path.join(output_dir, "conflict_storm_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n[RESULTADOS S6] Tabela de Escalabilidade Conflict Storm:")
    print(df_storm[["Level", "Name", "xApps", "Throughput_Actions_Sec", "Latency_Mean_ms", "Latency_P95_ms"]].to_string(index=False))
    print(f"\nSalvo em: {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run S6 Conflict Storm Benchmark")
    parser.add_argument("--output-dir", type=str, default="results/campaign_s0_s8/storm", help="Output directory")
    args = parser.parse_args()

    run_conflict_storm_benchmark(output_dir=args.output_dir)
