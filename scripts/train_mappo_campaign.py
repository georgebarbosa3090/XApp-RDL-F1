#!/usr/bin/env python3
"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 2 (CA-RDL)
Orquestrador de Campanha de Treinamento MARL MAPPO (scripts/train_mappo_campaign.py)

Executa campanhas de treinamento multi-semente reproduzíveis com exportação de:
  [OK] convergence.csv (Recompensa, Custo, Multiplicador de Lagrange)
  [OK] training_manifest.json (Metadados e hashes de configuração)
========================================================================================
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.agents.marl.mappo_trainer import MAPPOTrainer

def main():
    print("=" * 80)
    print(" CAMPANHA DE TREINAMENTO MARL MAPPO / SAFE-RL (CA-RDL FASE 2)")
    print("=" * 80)
    
    seeds = [42, 100, 2026]
    episodes = 20
    
    trainer = MAPPOTrainer(
        n_agents=6,
        obs_dim=60,
        action_dim=7,
        lr=3e-4,
        cost_limit=0.05
    )
    
    for seed in seeds:
        out_dir = BASE_DIR / "experiments" / "training" / f"seed_{seed:03d}"
        manifest = trainer.train_campaign(
            episodes=episodes,
            steps_per_episode=50,
            seed=seed,
            output_dir=str(out_dir)
        )
        print(f"[OK] Semente {seed} finalizada: Recompensa={manifest['final_reward']} | Custo={manifest['final_cost']}")

    print("\n" + "=" * 80)
    print(" [SUCESSO] CAMPANHA DE TREINAMENTO MARL MAPPO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
