"""Make `sdlc_mux` importable from src/ here and in the subprocesses the agent loop starts,
even when the editable-install .pth file is hidden or missing."""

import os
import sys
from pathlib import Path

SRC = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, SRC)
os.environ["PYTHONPATH"] = SRC + os.pathsep + os.environ.get("PYTHONPATH", "")
