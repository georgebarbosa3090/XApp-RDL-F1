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
  python scripts/certification/run_conflict_campaign.py --scenarios G1 --baselines B0 B3 --seeds 13001       --sim-arg=--powerAllocation=used --run-suffix U       # run_id nr_G1_B3U_seed13001 (docs/17)
"""

from __future__ import annotations

import argparse
import json
import os
import re
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


def run_id_of(scenario: str, baseline: str, seed: int, suffix: str = "") -> str:
    """run_id da execução; o sufixo (uma letra) distingue variantes de configuração, como o modo de potência."""
    return f"nr_{scenario}_{baseline}{suffix}_seed{seed}"


def run_one(scenario: str, baseline: str, seed: int, log_dir: Path, sim_args: List[str] = (), suffix: str = "") -> tuple:
    run_id = run_id_of(scenario, baseline, seed, suffix)
    if STOP.is_set() or not disk_ok():
        return run_id, 75, 0.0
    cmd = [sys.executable, str(ROOT / "scripts" / "certification" / "run_conflict_experiment.py"),
           "--scenario", scenario, "--baseline", baseline, "--seed", str(seed), "--no-build", "--run-id", run_id]
    # "--sim-arg=valor": o valor começa com "--" e o argparse do executor o leria como opção
    cmd += [f"--sim-arg={a}" for a in sim_args]
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


def select_jobs(seeds: List[int], scenarios: List[str], baselines: List[str], experiments_dir: Path,
                retry_failed: bool, stamp: str, suffix: str = "") -> List[tuple]:
    """Execuções a rodar, em ordem de semente. Remove as interrompidas e, com retry_failed,
    move as que falharam para runs_failed/; em ambos os casos elas voltam para a fila."""
    jobs = []
    for sd in seeds:
        for sc in scenarios:
            for bl in baselines:
                run_dir = experiments_dir / "runs" / run_id_of(sc, bl, sd, suffix)
                state = run_state(run_dir)
                if state == "INCOMPLETE":
                    # Sem hashes.sha256 a execução foi interrompida antes de terminar: não é evidência.
                    shutil.rmtree(run_dir)
                    say(f"Removida execução interrompida {run_dir.name}; será refeita")
                    state = "MISSING"
                elif state == "FAILED" and retry_failed:
                    target = experiments_dir / "runs_failed" / f"{run_dir.name}__{stamp}"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(run_dir), str(target))
                    say(f"Execução com falha preservada em {target}; será refeita")
                    state = "MISSING"
                if state == "MISSING":
                    jobs.append((sc, bl, sd))
    return jobs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    catalog = driver.load_catalog()
    # Só cenários com binário ns-3.48 (o S8 é do NORI: scripts/run_nori_campaign.sh)
    native = sorted(s for s, spec in catalog["scenarios"].items() if spec.get("ns3"))
    parser.add_argument("--scenarios", nargs="+", default=native)
    # B3A (apelido do B3, pré-registro 09) e B3M (EEVS por média, campanhas antigas) só rodam quando pedidos
    parser.add_argument("--baselines", nargs="+", default=["B0", "B1", "B2", "B3"], choices=list(driver.BASELINES))
    parser.add_argument("--seeds", nargs="+", required=True, help="ex.: 1001-1005 ou 1001 1002")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--log-dir", default=None, help="logs da campanha (padrão: diretório temporário)")
    parser.add_argument("--skip-analysis", action="store_true")
    parser.add_argument("--retry-failed", action="store_true",
                        help="move execuções com run_status != SUCCESS para experiments/runs_failed/ e as refaz")
    parser.add_argument("--sim-arg", action="append", default=[],
                        help="argumento extra do cenário ns-3, repetível; use --sim-arg=--opcao=valor "
                             "(ex.: --sim-arg=--powerAllocation=bw; fica no command do manifesto)")
    parser.add_argument("--run-suffix", default="",
                        help="uma letra maiúscula acrescentada ao baseline no run_id (ex.: U -> nr_G1_B3U_seed13001)")
    args = parser.parse_args(argv)
    if args.run_suffix and not re.fullmatch(r"[A-Z]", args.run_suffix):
        parser.error("--run-suffix deve ser uma letra maiúscula")
    bad = [b for b in args.baselines if not re.fullmatch(r"B\d[A-Z]?", b + args.run_suffix)]
    if bad:
        parser.error(f"baseline(s) {bad} com o sufixo {args.run_suffix!r} não formam um run_id que o analisador reconheça")

    seeds = parse_seeds(args.seeds)
    nori_only = [s for s in args.scenarios if s in catalog["scenarios"] and not catalog["scenarios"][s].get("ns3")]
    if nori_only:
        parser.error(f"cenário(s) só da bancada NORI, sem binário ns-3.48: {nori_only} (use scripts/run_nori_campaign.sh)")
    unknown = [s for s in args.scenarios if s not in catalog["scenarios"]]
    if unknown:
        parser.error(f"cenários desconhecidos: {unknown}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir = Path(args.log_dir) if args.log_dir else Path(os.environ.get("TEMP", "/tmp")) / f"rdl_campaign_{stamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    jobs = select_jobs(seeds, args.scenarios, args.baselines, ROOT / "experiments", args.retry_failed, stamp,
                       args.run_suffix)
    total = len(seeds) * len(args.scenarios) * len(args.baselines)
    say(f"Campanha: {len(args.scenarios)} cenário(s) × {len(args.baselines)} baseline(s) × {len(seeds)} semente(s) "
        f"= {total} execuções; {total - len(jobs)} já existem; {len(jobs)} a rodar com {args.jobs} em paralelo.")
    say(f"Logs da campanha em {log_dir}")
    if args.sim_arg or args.run_suffix:
        say(f"Argumentos extras do cenário: {args.sim_arg or '-'}; sufixo do run_id: {args.run_suffix or '-'}")
    if jobs:
        ns3_names = sorted({catalog["scenarios"][sc]["ns3"] for sc, _, _ in jobs})
        if prebuild(ns3_names, log_dir) != 0:
            say("ERRO: compilação falhou; campanha abortada.")
            return 1

    failures = []
    started = time.monotonic()
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(run_one, sc, bl, sd, log_dir, args.sim_arg, args.run_suffix) for sc, bl, sd in jobs]
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
