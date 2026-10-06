#!/usr/bin/python3 -ISB
"""RPM entry point: stdlib plus the private payload, without site initialization."""

import os
from pathlib import Path
import sys

# Resolve /usr/bin/hf -> ../lib64/huggingface-cli/hf.py, including in the buildroot.
sys.path.insert(0, str(Path(__file__).resolve().parent / "site-packages"))
# Make settings effective for subprocesses too; -I ignores PYTHON* in this process.
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ.setdefault("HF_HUB_DISABLE_UPDATE_CHECK", "1")

from huggingface_hub.cli.hf import main

if __name__ == "__main__":
    main()
