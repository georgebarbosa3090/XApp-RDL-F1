#!/usr/bin/env python3
"""
Scientific Repository Emoji & Icon Sanitizer
Permanently strips all decorative emojis, icons, and non-academic unicode pictographs
from all Markdown (.md), Python (.py), Shell (.sh), JSON (.json), and YAML (.yaml)
files across Phase 1 and Phase 2.
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Semantic replacements for status indicators and icons
STATUS_REPLACEMENTS = {
    "[CONFORME]": "[CONFORME]",
    "[EM VALIDACAO]": "[EM VALIDACAO]",
    "[NAO CONFORME]": "[NAO CONFORME]",
    "[OK]": "[OK]",
    "[OK]": "[OK]",
    "[FALHA]": "[FALHA]",
    "[ALERTA]": "[ALERTA]",
    "[ALERTA]": "[ALERTA]",
    "[METRICA]": "[METRICA]",
    "[SEGURANCA]": "[SEGURANCA]",
    "[SEGURANCA]": "[SEGURANCA]",
    "vs": "vs",
    "vs": "vs",
    "[INSPECAO]": "[INSPECAO]",
    "[COGNITIVO]": "[COGNITIVO]",
    "[RADIO]": "[RADIO]",
    "[CONFIG]": "[CONFIG]",
    "[CONFIG]": "[CONFIG]",
    "[TESTE]": "[TESTE]",
    "[EXEC]": "[EXEC]",
    "[INFO]": "[INFO]",
    "[TEMPO]": "[TEMPO]",
    "[TEMPO]": "[TEMPO]",
    "[GRAFICO]": "[GRAFICO]",
    "[GRAFICO]": "[GRAFICO]",
    "[CRITICO]": "[CRITICO]",
    "*": "*",
    "*": "*",
}

# Regex pattern matching emoji / pictograph unicode blocks
EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff"
    r"\u2600-\u26ff"
    r"\u2700-\u27bf"
    r"\u2300-\u23ff"
    r"\u2b00-\u2bff"
    r"\ufe00-\ufe0f"
    r"\u200d\u200b"
    r"\u25aa\u25ab\u25fe\u25fd\u25fb\u25fc\u25b6\u25c0\u3030\u303d\u3297\u3299"
    r"]",
    flags=re.UNICODE,
)

TARGET_EXTENSIONS = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".rst"}


def process_file(filepath: Path) -> int:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
            original = fp.read()
    except Exception:
        return 0

    lines = original.splitlines(keepends=True)
    new_lines = []
    emojis_removed = 0

    for line in lines:
        mod_line = line
        for sym, repl in STATUS_REPLACEMENTS.items():
            if sym in mod_line:
                mod_line = mod_line.replace(sym, repl)
                emojis_removed += 1

        matches = EMOJI_PATTERN.findall(mod_line)
        if matches:
            emojis_removed += len(matches)
            mod_line = EMOJI_PATTERN.sub("", mod_line)

        # Fix markdown headings spacing if applicable
        if filepath.suffix == ".md":
            mod_line = re.sub(r"^(#+\s+)\s+", r"\1", mod_line)
            mod_line = re.sub(r"^(\s*[\*\-]\s+)\s+", r"\1", mod_line)

        new_lines.append(mod_line)

    sanitized = "".join(new_lines)
    if emojis_removed > 0:
        with open(filepath, "w", encoding="utf-8") as fp:
            fp.write(sanitized)
    return emojis_removed


def main():
    total_files = 0
    modified_files = 0
    total_emojis = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [
            d
            for d in dirs
            if d
            not in (
                ".git",
                ".venv",
                "venv",
                ".venv-rdl",
                "node_modules",
                ".pytest_cache",
                ".idea",
                ".vscode",
                ".system_generated",
            )
        ]
        for f in files:
            filepath = Path(root) / f
            if filepath.suffix in TARGET_EXTENSIONS:
                total_files += 1
                cnt = process_file(filepath)
                if cnt > 0:
                    modified_files += 1
                    total_emojis += cnt
                    print(f"[REMOVIDO {cnt:>2} ICONES] {filepath.relative_to(PROJECT_ROOT)}")

    print("=" * 70)
    print("Sanitizacao Concluida:")
    print(f"  * Total de arquivos examinados: {total_files}")
    print(f"  * Total de arquivos modificados: {modified_files}")
    print(f"  * Total de icones/emojis removidos: {total_emojis}")
    print("=" * 70)


if __name__ == "__main__":
    main()

