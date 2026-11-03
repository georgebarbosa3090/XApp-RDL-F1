#!/usr/bin/env python3
"""Compatibility entry point for the six simulation-monitoring panels."""

import os
import sys

workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from scripts.wsl_pane_monitors import main


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("all")
    main()
