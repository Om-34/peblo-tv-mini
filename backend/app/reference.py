import json
from pathlib import Path
from .settings import settings

def load_reference(): return json.loads(Path(settings.reference_file).read_text())
