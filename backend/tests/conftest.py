import os
from pathlib import Path

_seed_dir = Path(__file__).resolve().parent.parent.parent / "seed"
os.environ.setdefault("REFERENCE_FILE", str(_seed_dir / "reference.json"))
os.environ.setdefault("SEED_FILE", str(_seed_dir / "seed_shows.json"))
