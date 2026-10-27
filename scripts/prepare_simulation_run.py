#!/usr/bin/env python3
"""Retired evidence-preparation entry point.

Experimental evidence must be produced by ns-3 with the pinned 5G-LENA stack
and mapped to claims through an explicit per-claim manifest. This legacy
utility ran a disabled Python simulator and assigned one artifact hash to every
claim, so it must not be used to create or authenticate evidence.
"""

def main():
    raise SystemExit(
        "Evidence preparation is disabled. Use an eligible ns-3/5G-LENA run and "
        "a reviewed per-claim evidence manifest."
    )


if __name__ == "__main__":
    main()
