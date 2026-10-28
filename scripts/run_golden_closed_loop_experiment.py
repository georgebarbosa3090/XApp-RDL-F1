#!/usr/bin/env python3
"""Retired synthetic golden-run generator.

This script used to fabricate KPI values, E2-like byte strings, ACKs, and PCAP
frames while labeling the result as NORI/ns-3. It is intentionally disabled:
fixtures and local generators cannot produce experimental evidence.
"""

import sys


def main() -> int:
    print(
        "ERROR: synthetic golden-run generation is disabled. "
        "Use a completed ns-3 + 5G-LENA run and capture evidence from the "
        "configured NORI/RIC stack; this script cannot generate it.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
