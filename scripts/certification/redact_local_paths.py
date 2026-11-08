#!/usr/bin/env python3
"""
Remove identificações locais (diretório do usuário, caminho do clone, HOME do WSL) de evidências e relatórios.

Placeholders:
    <repo>         raiz do clone do repositório
    <repo-antigo>  clones anteriores do projeto (iqos-xapp-rdl-phase1)
    ~              HOME (WSL ou Windows)
    <home>         outro diretório de usuário

Uso:
    python scripts/certification/redact_local_paths.py --check            # falha (código 1) se houver caminho local
    python scripts/certification/redact_local_paths.py --apply            # redige os arquivos versionados, propaga
                                                                         # os sha256 e grava o log da redação
    python scripts/certification/redact_local_paths.py --in-place A B ... # redige arquivos (geradores)

Biblioteca: ``redact_text(texto)`` devolve o texto sem caminhos locais; os geradores (executor ns-3, dissecador,
relatório da campanha) a usam antes de gravar comandos e logs.

No --apply, cada arquivo redigido muda de sha256. O sha256 antigo é trocado pelo novo em todo arquivo de texto
versionado que o cite (hashes.sha256, calibrações, slice_effect.json...), repetindo até não haver mais trocas.
O log (reports/redaction/redacao_caminhos_locais_<UTC>.json) guarda, por arquivo, o sha256 antes e depois e as
regras aplicadas, sem os caminhos em si.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SHA_RE = re.compile(rb"\b[0-9a-f]{64}\b")
SEP = r"(?:\\\\|\\|/)+"   # separador de caminho: "/", "\" ou "\\" (JSON)


def _path_pattern(path: str) -> str:
    """Regex de um caminho absoluto em qualquer grafia: C:\\x, C:/x, c:\\\\x (JSON), /mnt/c/x, file:///c:/x."""
    p = path.replace("\\", "/").rstrip("/")
    m = re.match(r"^([A-Za-z]):/(.*)$", p) or re.match(r"^/mnt/([a-z])/(.*)$", p)
    if m:
        drive, rest = m.group(1), m.group(2)
        parts = SEP.join(re.escape(x) for x in rest.split("/") if x)
        return rf"(?i:(?:file:///)?(?:{drive}:|/mnt/{drive}){SEP}{parts})(?![\w.-])"
    return re.escape(p) + r"(?![\w.-])"


def _dynamic_rules() -> List[Tuple[str, str, str]]:
    """Raiz do clone e HOME da máquina atual (os geradores usam estas)."""
    rules = [("repo", _path_pattern(str(ROOT)), "<repo>")]
    home = os.path.expanduser("~")
    if home and home not in ("/", "~"):
        rules.append(("home", _path_pattern(home), "~"))
    return rules


# Identificações já gravadas em evidências antigas (máquinas e clones anteriores). A ordem importa.
STATIC_RULES: List[Tuple[str, str, str]] = [
    ("repo-windows", _path_pattern("C:/Users/georg/.antigravity-ide/XApp-RDL-F1"), "<repo>"),
    ("repo-antigo", _path_pattern("C:/Users/georg/.antigravity-ide/iqos-xapp-rdl-phase1"), "<repo-antigo>"),
    ("repo-antigo", _path_pattern("C:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase1"),
     "<repo-antigo>"),
    ("usuario-wsl", r"`george` / `/home/george`", "`<usuário>` / `~`"),
    ("home-wsl", r"/home/george(?![\w.-])", "~"),
]

# Restos genéricos: qualquer diretório de usuário do Windows ou HOME do WSL.
GENERIC_RULES: List[Tuple[str, str, str]] = [
    ("home-windows", rf"(?i:(?:file:///)?(?:\b[a-z]:|/mnt/[a-z]){SEP}users{SEP}(?!<)[\w.-]+)", "<home>"),
    ("home-linux", r"(?<![\w.~-])/home/(?!<)[a-z][\w.-]*", "~"),
]

_COMPILED: List[Tuple[str, "re.Pattern[str]", str]] = []


def _rules() -> List[Tuple[str, "re.Pattern[str]", str]]:
    if not _COMPILED:
        for name, pattern, repl in _dynamic_rules() + STATIC_RULES + GENERIC_RULES:
            _COMPILED.append((name, re.compile(pattern), repl))
    return _COMPILED


def redact_text(text: str) -> str:
    return redact_with_counts(text)[0]


def redact_with_counts(text: str) -> Tuple[str, Dict[str, int]]:
    counts: Dict[str, int] = {}
    for name, rx, repl in _rules():
        text, n = rx.subn(lambda _m, r=repl: r, text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text, counts


def find_local(text: str) -> List[str]:
    """Trechos com identificação local (para --check)."""
    hits = []
    for _name, rx, _repl in _rules():
        hits += [m.group(0) for m in rx.finditer(text)]
    return hits


# ---------------------------------------------------------------------------

def tracked_files() -> List[Path]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True).stdout
    return [ROOT / p for p in out.decode("utf-8").split("\0") if p]


def read_text(path: Path):
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


SELF = {"scripts/certification/redact_local_paths.py", "tests/unit/test_redact_local_paths.py"}


def check(files: Iterable[Path]) -> int:
    bad = 0
    for path in files:
        if rel(path) in SELF:
            continue
        text = read_text(path)
        if text is None:
            continue
        hits = find_local(text)
        if hits:
            bad += 1
            print(f"{rel(path)}: {len(hits)} ocorrência(s), ex.: {redact_text(hits[0])!r} (redigido)")
    print(f"{bad} arquivo(s) com identificação local" if bad else "nenhuma identificação local nos arquivos versionados")
    return 1 if bad else 0


def apply(files: List[Path], log_dir: Path) -> Path:
    texts = {}
    for p in files:
        if rel(p) in SELF:
            continue
        t = read_text(p)
        if t is not None:
            texts[p] = t
    changed: Dict[Path, Dict] = {}
    # 1) redação dos caminhos
    for p, text in texts.items():
        new, counts = redact_with_counts(text)
        if counts:
            old_b = p.read_bytes()
            new_b = new.encode("utf-8")
            p.write_bytes(new_b)
            texts[p] = new
            changed[p] = {"file": rel(p), "sha256_before": sha(old_b), "sha256_after": sha(new_b),
                          "rules": counts, "sha256_references_updated": 0}
    # 2) propagação dos sha256 antigos -> novos, até estabilizar
    pending = {v["sha256_before"]: v["sha256_after"] for v in changed.values()}
    collisions = []
    for _round in range(20):
        if not pending:
            break
        current = {sha(p.read_bytes()): p for p in texts}
        for old in list(pending):
            if old in current:            # outro arquivo, não redigido, tem esse conteúdo: não troca
                collisions.append({"sha256": old, "file": rel(current[old])})
                pending.pop(old)
        new_pending = {}
        for p in texts:
            data = p.read_bytes()
            found = [m.group(0).decode() for m in SHA_RE.finditer(data) if m.group(0).decode() in pending]
            if not found:
                continue
            before = sha(data)
            for old in set(found):
                data = data.replace(old.encode(), pending[old].encode())
            p.write_bytes(data)
            after = sha(data)
            entry = changed.setdefault(p, {"file": rel(p), "sha256_before": before, "sha256_after": after,
                                           "rules": {}, "sha256_references_updated": 0})
            entry["sha256_after"] = after
            entry["sha256_references_updated"] += len(found)
            new_pending[before] = after
        pending = new_pending
    # 3) conferência dos hashes.sha256
    mismatches = []
    for p in texts:
        if p.name != "hashes.sha256":
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            target = p.parent / name.strip()
            if digest and target.is_file() and sha(target.read_bytes()) != digest:
                mismatches.append(f"{rel(p)}: {name.strip()}")
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log = {
        "schema": "xapp-rdl/redaction-log/v1",
        "generated_at_utc": stamp,
        "generator": "scripts/certification/redact_local_paths.py --apply",
        "placeholders": {"<repo>": "raiz do clone do repositório", "<repo-antigo>": "clone anterior do projeto",
                         "~": "HOME do usuário (WSL ou Windows)", "<home>": "outro diretório de usuário"},
        "note": ("Redação textual de caminhos locais; nenhum dado medido foi alterado. Os sha256 citados em outros "
                 "arquivos foram trocados pelos novos. Para conferir um arquivo contra a versão anterior, use o git "
                 "(o commit anterior a esta redação guarda o original)."),
        "files_changed": len(changed),
        "sha256_collisions_not_replaced": collisions,
        "hashes_sha256_mismatches_after": mismatches,
        "files": sorted(changed.values(), key=lambda e: e["file"]),
    }
    out = log_dir / f"redacao_caminhos_locais_{stamp}.json"
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(changed)} arquivo(s) alterado(s); colisões não trocadas: {len(collisions)}; "
          f"hashes.sha256 divergentes depois: {len(mismatches)}")
    print(f"log: {rel(out)}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--in-place", nargs="+", metavar="ARQUIVO")
    args = ap.parse_args(argv)
    if args.in_place:
        for name in args.in_place:
            p = Path(name)
            text = read_text(p)
            if text is not None:
                new = redact_text(text)
                if new != text:
                    p.write_bytes(new.encode("utf-8"))
        return 0
    files = tracked_files()
    if args.check:
        return check(files)
    apply(files, ROOT / "reports" / "redaction")
    return check(tracked_files())


if __name__ == "__main__":
    sys.exit(main())
