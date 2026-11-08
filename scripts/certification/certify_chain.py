#!/usr/bin/env python3
"""
Certificador de evidências experimentais ns-3.48 / 5G-LENA v5.1 / NORI (H-RDL Fase 1).

Avalia cada execução em ``experiments/runs/`` contra a política de proveniência
(``reproducibility/provenance_policy.yaml``) e o lock de versões
(``reproducibility/versions.lock``) e emite um veredito por gate G0–G6:

    CERTIFIED      todos os critérios verificáveis foram atendidos por evidência elegível
    NOT_CERTIFIED  há evidência, mas ao menos um critério falhou (motivos listados)
    BLOCKED        depende de gates anteriores não certificados

Princípios (fail-closed):
- Ausência de evidência é reprovação, nunca aprovação.
- Hash gerado pelo próprio pipeline prova integridade, não execução.
- Decodificar bytes com o codec local prova só autoconsistência: o codec do projeto
  ainda não foi validado contra o ASN.1 oficial nem contra implementação independente.
- Logs de console impressos pelo código do cenário não são evidência de protocolo E2.
- Execuções cujo identificador corresponde a um gerador estatístico (np.random etc.)
  são classificadas como sintéticas, independentemente do que o manifesto declare.

Uso:
    python scripts/certification/certify_chain.py                 # todas as execuções
    python scripts/certification/certify_chain.py --run S1_B3_seed1001
    python scripts/certification/certify_chain.py --out reports/certification
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PASS, FAIL, WARN, NA = "PASS", "FAIL", "WARN", "NOT_CHECKED"
CERTIFIED, NOT_CERTIFIED, BLOCKED = "CERTIFIED", "NOT_CERTIFIED", "BLOCKED"

E2_RAW_ROLES = {
    "e2_setup": ("e2_setup_request", "e2_setup_response"),
    "subscription": ("subscription_request", "subscription_response"),
    "kpm_t0": ("kpm_t0", "indication_t0"),
    "control_request": ("ric_control_request", "control_request"),
    "control_ack": ("ric_control_ack", "control_ack"),
    "kpm_t1": ("kpm_t1", "indication_t1"),
}
RANDOM_CALL = re.compile(r"\b(np\.random|numpy\.random|random\.(gauss|uniform|random|randint|normalvariate)|RandomState|default_rng|rng\.(normal|uniform|integers|random))\b")


@dataclass
class Check:
    rule: str
    status: str
    detail: str = ""


@dataclass
class RunReport:
    run_id: str
    path: str
    kind: str  # "run" ou "chain"
    classification: str = "UNKNOWN"
    publication_eligible: bool = False
    checks: List[Check] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)

    def add(self, rule: str, status: str, detail: str = "") -> None:
        self.checks.append(Check(rule, status, detail))

    def failed(self) -> List[Check]:
        return [c for c in self.checks if c.status == FAIL]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def load_policy() -> Dict[str, Any]:
    path = ROOT / "reproducibility" / "provenance_policy.yaml"
    if yaml is None or not path.exists():
        raise SystemExit(f"Política de proveniência indisponível: {path} (PyYAML necessário)")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_versions_lock() -> Dict[str, Dict[str, str]]:
    path = ROOT / "reproducibility" / "versions.lock"
    sections: Dict[str, Dict[str, str]] = {}
    current = None
    if not path.exists():
        return sections
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections[current] = {}
        elif "=" in line and current:
            key, value = line.split("=", 1)
            sections[current][key.strip()] = value.strip().strip('"')
    return sections


def norm_version(value: Any) -> str:
    return str(value or "").strip().lower().lstrip("v")


def select_lock_profile(backend: str, lock: Dict[str, Dict[str, str]]) -> Tuple[str, Dict[str, str]]:
    """Perfil do versions.lock correspondente ao backend declarado no manifesto."""
    for name, section in lock.items():
        if name.startswith("profile.") and section.get("backend", "").upper() == backend.upper():
            return name, section
    if backend.upper().startswith("NORI_NS3"):
        return "profile.nori", lock.get("profile.nori", {})
    return "", {}


def compare_with_lock(manifest: Dict[str, Any], profile: Dict[str, str], profile_name: str) -> Tuple[str, str]:
    """Compara commits (preferencialmente) e versões do manifesto com o perfil do lock."""
    if not profile:
        return FAIL, f"nenhum perfil do versions.lock para backend {manifest.get('backend')!r}"
    mismatches = []
    commit_fields = (("ns3_commit", "ns3"), ("nr_commit", "5G-LENA"), ("nori_commit", "NORI"), ("e2sim_commit", "e2sim"))
    for field_name, label in commit_fields:
        expected = profile.get(field_name)
        if not expected:
            continue
        got = str(manifest.get(field_name) or "")
        if not got or not expected.startswith(got[:7]) or len(got) < 7:
            mismatches.append(f"{label} {got or '?'} != {expected[:12]}")
    version_fields = (("ns3_version", "ns3", "ns-3"), ("fiveg_lena_version", "fiveg_lena", "5G-LENA"))
    for field_name, lock_key, label in version_fields:
        expected = profile.get(lock_key)
        if expected and norm_version(manifest.get(field_name)).split("-")[0] != norm_version(expected):
            mismatches.append(f"{label} {manifest.get(field_name)} != {expected}")
    if mismatches:
        return FAIL, f"[{profile_name}] " + "; ".join(mismatches)
    return PASS, f"[{profile_name}] versões e commits conferem"


def synthetic_run_id_patterns() -> List[Tuple[str, re.Pattern]]:
    """Extrai dos scripts geradores com RNG os moldes de run_id (f-strings) que eles produzem."""
    patterns: List[Tuple[str, re.Pattern]] = []
    for script in sorted((ROOT / "scripts").rglob("*.py")):
        if script.parent.name == "certification":
            continue
        try:
            source = script.read_text(encoding="utf-8")
        except OSError:
            continue
        if not RANDOM_CALL.search(source) or "run" not in source:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.JoinedStr):
                continue
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if not any("run_id" in n or n == "run_name" for n in names):
                continue
            regex = ""
            for part in node.value.values:
                if isinstance(part, ast.Constant):
                    regex += re.escape(str(part.value))
                else:
                    regex += r"[A-Za-z0-9.\-]+"
            if regex:
                patterns.append((str(script.relative_to(ROOT)), re.compile(f"^{regex}$")))
    return patterns


def find_role_file(run_dir: Path, aliases: Tuple[str, ...]) -> Optional[Path]:
    for candidate in run_dir.rglob("*.raw"):
        stem = candidate.stem.lower()
        if any(stem == a or stem.endswith(a) for a in aliases):
            return candidate
    return None


# ---------------------------------------------------------------------------
# Verificação de uma execução
# ---------------------------------------------------------------------------

def certify_run(run_dir: Path, policy: Dict[str, Any], lock: Dict[str, Dict[str, str]],
                synthetic_patterns: List[Tuple[str, re.Pattern]]) -> RunReport:
    manifest_path = run_dir / "execution_manifest.json"
    chain_path = run_dir / "chain_manifest.json"
    kind = "chain" if chain_path.exists() and not manifest_path.exists() else "run"
    rel = run_dir.relative_to(ROOT) if run_dir.is_relative_to(ROOT) else run_dir
    report = RunReport(run_id=run_dir.name, path=str(rel), kind=kind)
    manifest = load_json(manifest_path if kind == "run" else chain_path)

    if manifest is None:
        report.add("R1.manifest", FAIL, "manifesto ausente ou ilegível")
        report.classification = "NO_MANIFEST"
        return report
    report.add("R1.manifest", PASS)

    eligible = set(policy.get("publication_eligible_sources", []))
    restricted = set(policy.get("non_publication_sources", []))

    # R2 — origem explícita e elegível
    source = manifest.get("source") or manifest.get("provenance_category")
    sources = source if isinstance(source, list) else ([source] if source else [])
    if not sources:
        report.add("R2.source", FAIL, "campo 'source'/'provenance_category' ausente")
    elif any(s in restricted for s in sources):
        report.add("R2.source", FAIL, f"origem restrita (não publicável): {sources}")
        report.classification = "NON_PUBLICATION_SOURCE"
    elif all(s in eligible for s in sources):
        report.add("R2.source", PASS, f"{sources}")
    else:
        report.add("R2.source", FAIL, f"origem desconhecida na política: {sources}")

    # R3 — gerador sintético
    for script, pattern in synthetic_patterns:
        if pattern.match(run_dir.name):
            report.add("R3.synthetic_generator", FAIL,
                       f"run_id corresponde ao molde de {script}, que gera valores com RNG estatístico")
            report.classification = "SYNTHETIC_SUSPECT"
            break
    else:
        report.add("R3.synthetic_generator", PASS, "nenhum gerador estatístico produz este run_id")

    if kind == "chain":
        _certify_chain_specific(run_dir, manifest, report)
    else:
        _certify_run_specific(run_dir, manifest, policy, lock, report)

    if report.classification == "UNKNOWN":
        report.classification = "ELIGIBLE" if not report.failed() else "INCOMPLETE_EVIDENCE"
    report.publication_eligible = report.classification == "ELIGIBLE"
    return report


def _certify_run_specific(run_dir: Path, manifest: Dict[str, Any], policy: Dict[str, Any],
                          lock: Dict[str, Dict[str, str]], report: RunReport) -> None:
    backend = str(manifest.get("backend", ""))
    report.facts["backend"] = backend
    report.facts["scenario"] = manifest.get("scenario")
    report.facts["baseline"] = manifest.get("baseline")
    report.facts["seed"] = manifest.get("seed")

    rules = policy.get("backend_evidence_rules", {})
    rule_key = next((k for k in rules if backend.upper().startswith(k)), None)
    required = rules.get(rule_key, {}).get("required_manifest_fields", []) if rule_key else []
    if not rule_key:
        report.add("R4.manifest_fields", FAIL, f"backend '{backend}' sem regra na política")
    else:
        missing = [f for f in required if manifest.get(f) in (None, "")]
        report.add("R4.manifest_fields", FAIL if missing else PASS,
                   f"ausentes: {missing}" if missing else f"{len(required)} campos")

    status_ok = manifest.get("run_status") == "SUCCESS" and manifest.get("exit_code") == 0
    report.add("R5.run_status", PASS if status_ok else FAIL,
               f"run_status={manifest.get('run_status')!r}, exit_code={manifest.get('exit_code')!r}")

    profile_name, profile = select_lock_profile(backend, lock)
    report.facts["lock_profile"] = profile_name
    report.add("R6.versions_lock", *compare_with_lock(manifest, profile, profile_name))

    env = manifest.get("environment") or {}
    lock_os = lock.get("infrastructure", {}).get("os", "")
    env_os = str(env.get("os", "")) if isinstance(env, dict) else ""
    if env_os and lock_os and lock_os.split(" (")[0] not in env_os:
        report.add("R7.environment", WARN, f"SO do manifesto '{env_os}' difere do lock '{lock_os}'")
    elif not env_os:
        report.add("R7.environment", WARN, "ambiente de execução não registrado")
    else:
        report.add("R7.environment", PASS, env_os)

    # R8 — manifesto de hashes completo e conferido
    hash_file = run_dir / "hashes.sha256"
    files = sorted(p for p in run_dir.rglob("*") if p.is_file() and p.name != "hashes.sha256")
    if not hash_file.exists() or hash_file.stat().st_size == 0:
        report.add("R8.hashes", FAIL, "hashes.sha256 ausente ou vazio")
    else:
        listed: Dict[str, str] = {}
        for line in hash_file.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                listed[parts[1].lstrip("*").replace("\\", "/")] = parts[0].lower()
        rels = {p.relative_to(run_dir).as_posix(): p for p in files}
        unhashed = [r for r in rels if r not in listed]
        mismatched = [r for r, h in listed.items() if r in rels and sha256_file(rels[r]) != h]
        missing = [r for r in listed if r not in rels]
        problems = []
        if unhashed:
            problems.append(f"{len(unhashed)} arquivo(s) sem hash (ex.: {unhashed[:3]})")
        if mismatched:
            problems.append(f"hash divergente: {mismatched[:3]}")
        if missing:
            problems.append(f"listado mas ausente: {missing[:3]}")
        report.add("R8.hashes", FAIL if problems else PASS,
                   "; ".join(problems) or f"{len(listed)} arquivos conferidos (integridade, não prova de execução)")

    # R9 — grupos de evidência bruta exigidos pela política (cada grupo: qualquer extensão)
    xmls = [p for p in files if p.suffix.lower() == ".xml"]
    groups = rules.get(rule_key, {}).get("required_raw_groups", [[".xml"], [".raw"]]) if rule_key else [[".xml"], [".raw"]]
    suffixes = {p.suffix.lower() for p in files}
    unmet = [g for g in groups if not any(ext in suffixes for ext in g)]
    report.add("R9.raw_groups", FAIL if unmet else PASS,
               f"grupos não atendidos: {unmet}" if unmet else f"grupos atendidos: {groups}")

    # R10 — FlowMonitor válido
    flows_ok = 0
    for xml_path in xmls:
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        if root.tag == "FlowMonitor":
            flows_ok += sum(1 for fl in root.iter("Flow") if int(fl.get("rxPackets", "0") or 0) > 0)
    report.add("R10.flowmonitor", PASS if flows_ok else FAIL,
               f"{flows_ok} fluxo(s) com rxPackets > 0" if xmls else "nenhum FlowMonitor XML")
    report.facts["flows_with_rx"] = flows_ok

    if backend.upper().startswith("NS3_5GLENA"):
        _check_timeline(manifest, report)
        for rule in ("R11.e2_artifacts", "R12.rc_correlation", "R14.pcap"):
            report.add(rule, NA, "pilha nativa ns-3 + 5G-LENA sem NORI: não há E2 (só FlowMonitor)")
        return

    _check_timeline(manifest, report)
    pcaps = [p for p in files if p.suffix.lower() in (".pcap", ".pcapng")]
    report.add("R14.pcap", NA if pcaps else FAIL,
               f"{len(pcaps)} PCAP(s); dissecação E2AP independente (tshark) não executada" if pcaps else "nenhum PCAP E2")

    # R11 — artefatos E2 por papel no protocolo
    roles = {role: find_role_file(run_dir, aliases) for role, aliases in E2_RAW_ROLES.items()}
    report.facts["e2_roles"] = {r: (str(p.relative_to(run_dir)) if p else None) for r, p in roles.items()}
    if pcaps and all(p is None for p in roles.values()):
        # NORI grava o E2 como tráfego SCTP: separar as mensagens exige dissecção do PCAP.
        report.add("R11.e2_artifacts", NA, "E2 apenas em PCAP; extração por mensagem ainda não realizada")
        report.add("R12.rc_correlation", NA, "depende da extração das mensagens E2 do PCAP")
        return
    missing_roles = [r for r, p in roles.items() if p is None]
    empty_roles = [r for r, p in roles.items() if p is not None and p.stat().st_size == 0]
    report.add("R11.e2_artifacts", FAIL if missing_roles or empty_roles else PASS,
               f"ausentes: {missing_roles}; vazios: {empty_roles}" if missing_roles or empty_roles else "6 papéis E2 presentes")

    # R12 — correlação RC request/ACK (autoconsistência do codec local)
    req, ack = roles.get("control_request"), roles.get("control_ack")
    if req and ack and req.stat().st_size and ack.stat().st_size:
        try:
            from src.e2.e2ap.control import RICcontrolRequest, parse_ric_control_ack
            from src.e2.e2ap.pdu import unwrap_e2ap_pdu
            _, _, _, inner = unwrap_e2ap_pdu(req.read_bytes())
            request = RICcontrolRequest()
            request.from_aper(inner)
            r = request()
            a = parse_ric_control_ack(ack.read_bytes())
            same = (r["ricRequestID"]["ricRequestorID"] == a["requestor_id"]
                    and r["ricRequestID"]["ricInstanceID"] == a["instance_id"]
                    and r["ranFunctionID"] == a["ran_function_id"])
            report.add("R12.rc_correlation", PASS if same else FAIL,
                       "RICrequestID/RANFunctionID pareados (codec local: autoconsistência, sem validação independente)"
                       if same else "RICrequestID/RANFunctionID do ACK não correspondem ao Control Request")
        except Exception as exc:  # noqa: BLE001 - qualquer falha de decodificação reprova
            report.add("R12.rc_correlation", FAIL, f"falha ao decodificar com o codec local: {exc}")
    else:
        report.add("R12.rc_correlation", FAIL, "Control Request/ACK ausentes ou vazios")



def _check_timeline(manifest: Dict[str, Any], report: RunReport) -> None:
    """R13 — início e fim registrados, em ordem."""
    started, finished = manifest.get("started_at_utc"), manifest.get("finished_at_utc")
    try:
        ok = datetime.fromisoformat(str(started).replace("Z", "+00:00")) <= datetime.fromisoformat(str(finished).replace("Z", "+00:00"))
        report.add("R13.timeline", PASS if ok else FAIL, f"{started} -> {finished}")
    except ValueError:
        report.add("R13.timeline", FAIL, "started_at_utc/finished_at_utc ausentes ou inválidos")


def _certify_chain_specific(run_dir: Path, manifest: Dict[str, Any], report: RunReport) -> None:
    links = manifest.get("causal_links") or []
    names = [l.get("name") for l in links if isinstance(l, dict)]
    expected = ["indication_t0", "rdl_decision", "control_request", "control_ack", "ran_mac_transition", "indication_t1"]
    complete = all(any(e in (n or "") for n in names) for e in expected)
    report.add("C1.links", PASS if complete else FAIL, f"elos: {names}")
    bad = []
    for link in links:
        raw_hash = link.get("raw_sha256")
        if not raw_hash:
            continue
        raw_path = run_dir / f"{link.get('name')}.raw"
        if not raw_path.exists() or sha256_file(raw_path) != raw_hash:
            bad.append(link.get("name"))
    report.add("C2.raw_hashes", FAIL if bad else PASS, f"divergentes/ausentes: {bad}" if bad else "hashes dos elos brutos conferem")
    external = manifest.get("external_evidence") is True and manifest.get("publication_eligible") is True
    report.add("C3.external_evidence", PASS if external else FAIL,
               f"status={manifest.get('status')!r}, external_evidence={manifest.get('external_evidence')!r}")


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def scenario_console_traces() -> List[str]:
    """Cenários C++ que imprimem mensagens de protocolo E2 fixas (não são evidência)."""
    findings = []
    for cc in sorted((ROOT / "simulations").rglob("*.cc")):
        text = cc.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'std::cout\s*<<\s*"[^"]*(E2_SETUP|RIC_SUBSCRIPTION|RIC_CONTROL|SCTP)', text):
            findings.append(str(cc.relative_to(ROOT)))
    return findings


def evaluate_gates(reports: List[RunReport], lock: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    eligible_all = [r for r in reports if r.kind == "run" and r.publication_eligible]
    # Somente a pilha NORI produz E2; execuções nativas contam apenas para G0.
    eligible = [r for r in eligible_all if str(r.facts.get("backend", "")).upper().startswith("NORI_NS3")]

    def rule_pass(r: RunReport, rule: str) -> bool:
        return any(c.rule.startswith(rule) and c.status == PASS for c in r.checks)

    gates: Dict[str, Dict[str, Any]] = {}
    g0_runs = [r for r in reports if r.kind == "run" and rule_pass(r, "R6") and rule_pass(r, "R4")]
    gates["G0"] = {
        "verdict": CERTIFIED if lock.get("profile.nori") and g0_runs else NOT_CERTIFIED,
        "reason": f"{len(g0_runs)} execução(ões) com manifesto completo e versões do lock" if g0_runs
                  else "nenhuma execução registra todas as versões/campos exigidos",
    }
    g1 = [r for r in eligible if r.facts.get("e2_roles", {}).get("kpm_t0") and r.facts.get("e2_roles", {}).get("subscription")]
    gates["G1"] = {"verdict": CERTIFIED if g1 else NOT_CERTIFIED,
                   "reason": f"{len(g1)} execução(ões) elegíveis com KPM e subscrição" if g1
                             else "nenhuma execução elegível com Indication KPM e subscrição E2 externas"}
    gates["G2"] = {"verdict": "LOCAL_ONLY",
                   "reason": "decisão determinística coberta por testes unitários; não certifica interoperabilidade"}
    g3 = [r for r in eligible if rule_pass(r, "R12")]
    gates["G3"] = {"verdict": (CERTIFIED if g3 else NOT_CERTIFIED) if gates["G1"]["verdict"] == CERTIFIED else BLOCKED,
                   "reason": f"{len(g3)} execução(ões) com RC request/ACK correlacionados" if g3
                             else "sem RIC Control + ACK externos correlacionados em execução elegível"}
    g4 = [r for r in eligible if all(r.facts.get("e2_roles", {}).get(k) for k in ("kpm_t0", "control_request", "control_ack", "kpm_t1"))]
    chains_ok = [r for r in reports if r.kind == "chain" and not r.failed()]
    g4_ok = bool(g4 or chains_ok)
    gates["G4"] = {"verdict": (CERTIFIED if g4_ok else NOT_CERTIFIED) if gates["G3"]["verdict"] == CERTIFIED else BLOCKED,
                   "reason": "cadeia KPM_t0 -> decisão -> RC -> ACK -> KPM_t1 elegível encontrada" if g4_ok
                             else "nenhuma cadeia closed-loop elegível (fixtures e execuções sintéticas não contam)"}
    per_baseline: Dict[str, set] = {}
    for r in eligible:
        per_baseline.setdefault(str(r.facts.get("baseline")), set()).add(r.facts.get("seed"))
    paired = all(len(per_baseline.get(b, set())) >= 30 for b in ("B0", "B1", "B2", "B3"))
    gates["G5"] = {"verdict": (CERTIFIED if paired else NOT_CERTIFIED) if gates["G4"]["verdict"] == CERTIFIED else BLOCKED,
                   "reason": f"sementes elegíveis por baseline: { {b: len(s) for b, s in sorted(per_baseline.items())} }"}
    gates["G6"] = {"verdict": BLOCKED if CERTIFIED not in (gates["G4"]["verdict"], gates["G5"]["verdict"]) or
                   gates["G5"]["verdict"] != CERTIFIED else NOT_CERTIFIED,
                   "reason": "requer G4 e G5 certificados e reprodução independente"}
    return gates


# ---------------------------------------------------------------------------
# Relatórios
# ---------------------------------------------------------------------------

def render_markdown(reports: List[RunReport], gates: Dict[str, Dict[str, Any]], traces: List[str], generated_at: str) -> str:
    by_class: Dict[str, int] = {}
    for r in reports:
        by_class[r.classification] = by_class.get(r.classification, 0) + 1
    chain_validated = gates["G4"]["verdict"] == CERTIFIED
    lines = [
        "# Certificado de Evidências — ns-3.48 / 5G-LENA v5.1 / NORI",
        "",
        f"Gerado em {generated_at} por `scripts/certification/certify_chain.py`.",
        "",
        f"**Cadeia closed-loop validada:** {'SIM' if chain_validated else 'NÃO'}",
        "",
        "## Gates",
        "",
        "| Gate | Veredito | Motivo |",
        "| :---: | :---: | :--- |",
    ]
    for gate, info in gates.items():
        lines.append(f"| {gate} | {info['verdict']} | {info['reason']} |")
    lines += ["", "## Classificação das execuções", "", "| Classe | Execuções |", "| :--- | ---: |"]
    for cls, n in sorted(by_class.items()):
        lines.append(f"| {cls} | {n} |")
    if traces:
        lines += ["", "## Alertas", "",
                  "Cenários que imprimem mensagens de protocolo E2 fixas no console (não são evidência de E2):", ""]
        lines += [f"- `{t}`" for t in traces]
    failures: Dict[str, int] = {}
    for r in reports:
        for c in r.failed():
            failures[c.rule] = failures.get(c.rule, 0) + 1
    if failures:
        lines += ["", "## Critérios reprovados (contagem)", "", "| Regra | Execuções |", "| :--- | ---: |"]
        for rule, n in sorted(failures.items()):
            lines.append(f"| {rule} | {n} |")
    lines += ["", "## Detalhe por execução", ""]
    for r in reports:
        lines.append(f"### {r.run_id} — {r.classification}")
        for c in r.checks:
            lines.append(f"- `{c.rule}` **{c.status}** {c.detail}")
        lines.append("")
    lines += [
        "## Limites desta certificação",
        "",
        "- Hashes gerados pelo próprio pipeline comprovam integridade, não execução.",
        "- A correlação RC usa o codec local, que ainda não segue o ASN.1 oficial do E2SM-RC v1.03.",
        "- PCAPs não são dissecados por implementação independente (tshark ausente).",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-dir", default=str(ROOT / "experiments" / "runs"))
    parser.add_argument("--run", action="append", default=[], help="restringe a execuções específicas")
    parser.add_argument("--out", default=str(ROOT / "reports" / "certification"))
    parser.add_argument("--no-write", action="store_true", help="apenas imprime o resumo")
    args = parser.parse_args(argv)

    policy = load_policy()
    lock = load_versions_lock()
    patterns = synthetic_run_id_patterns()
    runs_dir = Path(args.runs_dir)
    candidates = sorted(p for p in runs_dir.iterdir() if p.is_dir()) if runs_dir.exists() else []
    if args.run:
        candidates = [p for p in candidates if p.name in set(args.run)]
    reports = [certify_run(p, policy, lock, patterns) for p in candidates]
    gates = evaluate_gates(reports, lock)
    traces = scenario_console_traces()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    summary = {
        "generated_at_utc": generated_at,
        "runs_evaluated": len(reports),
        "closed_loop_chain_validated": gates["G4"]["verdict"] == CERTIFIED,
        "gates": gates,
        "scenario_console_trace_alerts": traces,
        "synthetic_generators": sorted({s for s, _ in patterns}),
        "runs": [
            {
                "run_id": r.run_id, "path": r.path, "kind": r.kind,
                "classification": r.classification, "publication_eligible": r.publication_eligible,
                "facts": r.facts, "checks": [c.__dict__ for c in r.checks],
            }
            for r in reports
        ],
    }

    for gate, info in gates.items():
        print(f"{gate}: {info['verdict']:<14} {info['reason']}")
    print(f"Cadeia closed-loop validada: {'SIM' if summary['closed_loop_chain_validated'] else 'NÃO'}")

    if not args.no_write:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        stamp = generated_at.replace(":", "").replace("-", "")
        json_path = out / f"certificate_{stamp}.json"
        md_path = out / f"certificate_{stamp}.md"
        json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        md_path.write_text(render_markdown(reports, gates, traces, generated_at), encoding="utf-8")
        print(f"Relatórios: {json_path.relative_to(ROOT) if json_path.is_relative_to(ROOT) else json_path}")
        print(f"            {md_path.relative_to(ROOT) if md_path.is_relative_to(ROOT) else md_path}")

    return 0 if gates["G4"]["verdict"] == CERTIFIED else 2


if __name__ == "__main__":
    sys.exit(main())
