from pathlib import Path
import os, json
from .settings import settings

class Storage:
    def __init__(self, root=None): self.root=Path(root or settings.storage_root); self.root.mkdir(parents=True,exist_ok=True); (self.root/"media").mkdir(exist_ok=True); (self.root/"catalogues").mkdir(exist_ok=True)
    def save_bytes(self,key,data):
        p=self.root/key; p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+".tmp"); tmp.write_bytes(data); os.replace(tmp,p); return key
    def media_path(self,key): return self.root/key
    def publish_catalogue(self,data):
        import hashlib
        raw=json.dumps(data,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()
        digest=hashlib.sha256(raw).hexdigest(); version=f"catalogues/catalogue-{digest}.json"; self.save_bytes(version,raw)
        pointer=self.root/"catalogues/current.json"; tmp=self.root/"catalogues/current.json.tmp"; tmp.write_text(version); os.replace(tmp,pointer)
        return digest,version
    def read_catalogue(self):
        p=self.root/"catalogues/current.json"
        if not p.exists(): return None
        version=p.read_text().strip(); f=self.root/version
        return json.loads(f.read_text()) if f.exists() else None
