#!/usr/bin/env python3
"""
Campanha de experimentos de conflito: cenários × baselines × sementes, com evidência certificada.

- Compila uma vez os cenários envolvidos (cópia para scratch/ só do que mudou) e roda as
  execuções com --no-build, o que permite paralelismo seguro (--jobs).
- Retomável: execuções que já existem em experiments/runs/ são puladas.
- Ordem por semente: cada semente concluída forma um conjunto pareado completo.
- Ao vivo: as linhas [RDL-ACT]/[RDL-KPI] de cada execução são mostradas com o run_id;
  a saída completa de cada execução fica em logs/stdout.log da própria evidência.
- Ao final, roda a análise (reports/conflicts/) e o certificador (reports/certification/).

Uso:
  python scripts/certification/run_conflict_campaign.py --seeds 1001-1005 --jobs 2
  python scripts/certification/run_conflict_campaign.py --scenarios S1 S7 --baselines B0 B3 --seeds 1001
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "certification"))
import run_conflict_experiment as driver  # noqa: E402

PRINT_LOCK = threading.Lock()


def say(msg: str) -> None:
    with PRINT_LOCK:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_state(run_dir: Path) -> str:
    """MISSING, INCOMPLETE (interrompida), FAILED ou SUCCESS."""
    if not run_dir.exists():
        return "MISSING"
    if not (run_dir / "hashes.sha256").exists():
        return "INCOMPLETE"
    try:
        status = json.loads((run_dir / "execution_manifest.json").read_text(encoding="utf-8")).get("run_status")
    except (OSError, ValueError):
        return "FAILED"
    return "SUCCESS" if status == "SUCCESS" else "FAILED"


def parse_seeds(items: List[str]) -> List[int]:
    seeds: List[int] = []
    for item in items:
        if "-" in item:
            a, b = item.split("-", 1)
            seeds += list(range(int(a), int(b) + 1))
        else:
            seeds.append(int(item))
    return sorted(set(seeds))


def wsl_cmd(args: List[str]) -> List[str]:
    return ["wsl", "-d", "Ubuntu", "--", *args] if os.name == "nt" else args


def prebuild(ns3_names: List[str], work_dir: Path) -> int:
    """Copia para scratch/ só os arquivos alterados e compila os cenários da campanha."""
    repo = driver.to_wsl(ROOT)
    sources = " ".join([f"{repo}/simulations/ns3/*.h"] + [f"{repo}/simulations/ns3/{n}.cc" for n in ns3_names])
    script = (
        "#!/usr/bin/env bash\nset -e\n"
        'NS3="${NS3_DIR:-$HOME/ns3-oran-workspace/ns-3-oran}"\ncd "$NS3"\n'
        f'for f in {sources}; do cmp -s "$f" "scratch/$(basename "$f")" || cp -f "$f" scratch/; done\n'
        f"./ns3 build {' '.join(ns3_names)}\n"
    )
    # Gravado em arquivo: `wsl -- bash -c` perderia as variáveis do script.
    script_path = work_dir / "prebuild.sh"
    script_path.write_text(script, encoding="utf-8", newline="\n")
    say(f"Compilando {len(ns3_names)} cenário(s) uma única vez...")
    return subprocess.call(wsl_cmd(["bash", driver.to_wsl(script_path)]))


MIN_FREE_BYTES = 1024 ** 3  # 1 GB
STOP = threading.Event()


def disk_ok() -> bool:
    import shutil
    free = shutil.disk_usage(ROOT).free
    if free < MIN_FREE_BYTES:
        STOP.set()
        say(f"ERRO: só {free / 1024 ** 3:.2f} GB livres no disco do repositório; campanha interrompida "
            "(libere espaço e rode de novo: execuções concluídas são puladas).")
        return False
    return True


def run_one(scenario: str, baseline: str, seed: int, log_dir: Path) -> tuple:
    run_id = f"nr_{scenario}_{baseline}_seed{seed}"
    if STOP.is_set() or not disk_ok():
        return run_id, 75, 0.0
    cmd = [sys.executable, str(ROOT / "scripts" / "certification" / "run_conflict_experiment.py"),
           "--scenario", scenario, "--baseline", baseline, "--seed", str(seed), "--no-build"]
    started = time.monotonic()
    say(f"INÍCIO {run_id}")
    log_path = log_dir / f"{run_id}.log"
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", env=env)
        for line in proc.stdout:
            line = line.replace("\0", "").rstrip("\r\n")
            log.write(line + "\n")
            if "[RDL-ACT] t=" in line or "[RDL-KPI]" in line or "rror" in line or "Origem" in line:
                say(f"{run_id} {line.strip()}")
        code = proc.wait()
    elapsed = time.monotonic() - started
    say(f"FIM    {run_id} exit={code} em {elapsed / 60:.1f} min")
    return run_id, code, elapsed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    catalog = driver.load_catalog()
    parser.add_argument("--scenarios", nargs="+", default=sorted(catalog["scenarios"]))
    parser.add_argument("--baselines", nargs="+", default=list(driver.BASELINES))
    parser.add_argument("--seeds", nargs="+", required=True, help="ex.: 1001-1005 ou 1001 1002")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--log-dir", default=None, help="logs da campanha (padrão: diretório temporário)")
    parser.add_argument("--skip-analysis", action="store_true")
    parser.add_argument("--retry-failed", action="store_true",
                        help="move execuções com run_status != SUCCESS para experiments/runs_failed/ e as refaz")
    args = parser.parse_args(argv)

    seeds = parse_seeds(args.seeds)
    unknown = [s for s in args.scenarios if s not in catalog["scenarios"]]
    if unknown:
        parser.error(f"cenários desconhecidos: {unknown}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir = Path(args.log_dir) if args.log_dir else Path(os.environ.get("TEMP", "/tmp")) / f"rdl_campaign_{stamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    for sd in seeds:
        for sc in args.scenarios:
            for bl in args.baselines:
                run_dir = ROOT / "experiments" / "runs" / f"nr_{sc}_{bl}_seed{sd}"
                state = run_state(run_dir)
                if state == "INCOMPLETE":
                    # Sem hashes.sha256 a execução foi interrompida antes de terminar: não é evidência.
                    shutil.rmtree(run_dir)
                    say(f"Removida execução interrompida {run_dir.name}")
                elif state == "FAILED" and args.retry_failed:
                    target = ROOT / "experiments" / "runs_failed" / f"{run_dir.name}__{stamp}"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(run_dir), str(target))
                    say(f"Execução com falha preservada em {target.relative_to(ROOT)}; será refeita")
                    state = "MISSING"
                if state == "MISSING":
                    jobs.append((sc, bl, sd))
    total = len(seeds) * len(args.scenarios) * len(args.baselines)
    say(f"Campanha: {len(args.scenarios)} cenário(s) × {len(args.baselines)} baseline(s) × {len(seeds)} semente(s) "
        f"= {total} execuções; {total - len(jobs)} já existem; {len(jobs)} a rodar com {args.jobs} em paralelo.")
    say(f"Logs da campanha em {log_dir}")
    if jobs:
        ns3_names = sorted({catalog["scenarios"][sc]["ns3"] for sc, _, _ in jobs})
        if prebuild(ns3_names, log_dir) != 0:
            say("ERRO: compilação falhou; campanha abortada.")
            return 1

    failures = []
    started = time.monotonic()
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(run_one, sc, bl, sd, log_dir) for sc, bl, sd in jobs]
        for future in as_completed(futures):
            run_id, code, _ = future.result()
            done += 1
            if code != 0:
                failures.append((run_id, code))
            elapsed = time.monotonic() - started
            eta = elapsed / done * (len(jobs) - done)
            say(f"Progresso {done}/{len(jobs)}; falhas {len(failures)}; restante estimado {eta / 60:.0f} min")

    for run_id, code in failures:
        say(f"FALHA {run_id} (exit {code}); log em {log_dir / (run_id + '.log')}")
    if not args.skip_analysis:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        subprocess.call([sys.executable, str(ROOT / "scripts" / "certification" / "analyze_conflict_runs.py")], env=env)
        subprocess.call([sys.executable, str(ROOT / "scripts" / "certification" / "certify_chain.py")], env=env)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
