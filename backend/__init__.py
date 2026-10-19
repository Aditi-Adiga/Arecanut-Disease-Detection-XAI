"""Arecanut disease detection API."""
import os
from pathlib import Path

# Keep library-generated caches inside the project, including offline use.
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent.parent / "work" / "matplotlib"))
