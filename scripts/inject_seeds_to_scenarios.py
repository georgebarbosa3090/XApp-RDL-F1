#!/usr/bin/env python3
"""
Adiciona suporte a --seed e --run com SeedManager em todos os cenários C++ do ns-3.
"""

from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent.parent / "simulations" / "ns3"

for p in sorted(SIM_DIR.glob("*.cc")):
    content = p.read_text(encoding="utf-8")
    if "SeedManager::SetSeed" not in content and "cmd.Parse (argc, argv);" in content:
        print(f"Atualizando cenário: {p.name}")
        old_str = "cmd.Parse (argc, argv);"
        new_str = (
            "uint32_t randomSeed = 1001;\n"
            "    uint32_t runIndex = 1;\n"
            "    cmd.AddValue (\"seed\", \"Semente pseudoaleatoria do gerador ns-3\", randomSeed);\n"
            "    cmd.AddValue (\"run\", \"Indice da repeticao estocastica ns-3\", runIndex);\n"
            "    cmd.Parse (argc, argv);\n\n"
            "    SeedManager::SetSeed (randomSeed);\n"
            "    SeedManager::SetRun (runIndex);"
        )
        content = content.replace(old_str, new_str, 1)
        p.write_text(content, encoding="utf-8")
        print(f"  [OK] {p.name} atualizado com sucesso!")
    else:
        print(f"  [SKIP] {p.name} ja possui SeedManager ou nao possui cmd.Parse.")
