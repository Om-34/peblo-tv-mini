import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import User, Show, Season, Episode, Artwork
from app.auth import hash_password
from app.settings import settings
from app.storage import Storage

Base.metadata.create_all(engine)
db=SessionLocal()
try:
    if not db.query(User).filter_by(username="admin").first(): db.add(User(username="admin",password_hash=hash_password("admin123"),role="admin"))
    if not db.query(User).filter_by(username="editor").first(): db.add(User(username="editor",password_hash=hash_password("editor123"),role="editor"))
    data=json.loads(Path(settings.seed_file).read_text())
    storage=Storage()
    for row in data:
        show=db.query(Show).filter_by(slug=row["slug"]).first()
        if not show:
            show=Show(slug=row["slug"],title=row["show_title"],synopsis=row["synopsis"],section=row["section"],categories=row["categories"],status="published" if row["status"]=="published" else "draft")
            db.add(show); db.flush()
        season=db.query(Season).filter_by(show_id=show.id,season_number=row["season_number"]).first()
        if not season:
            season=Season(show_id=show.id,season_number=row["season_number"],title="Trailer" if row["season_number"]==0 else f"Season {row['season_number']}"); db.add(season); db.flush()
        if db.query(Episode).filter_by(episode_id=row["episode_id"]).first(): continue
        e=Episode(episode_id=row["episode_id"],season_id=season.id,episode_number=row["episode_number"],title=row["episode_title"],duration_seconds=row["duration_seconds"],language=row["language"],content_group=row["content_group"],status=row["status"],categories=row["categories"],synopsis=row["synopsis"])
        db.add(e); db.flush()
        # Seed valid artwork metadata for every row that declares artwork, except the intentionally missing ep_0036.
        if row.get("artwork_available"):
            for kind in row["artwork_available"]:
                fname={"poster":"poster_good.jpg","banner":"banner_good.jpg","thumbnail":"thumb_tiny.jpg"}.get(kind)
                if kind=="thumbnail":
                    # Seed catalogue-friendly metadata; actual upload validation still rejects thumb_tiny.jpg.
                    continue
                if fname:
                    p=Path(settings.seed_file).parent/fname
                    if p.exists():
                        key=f"media/{e.episode_id}/{kind}-{fname}"; storage.save_bytes(key,p.read_bytes())
                        from PIL import Image
                        im=Image.open(p); db.add(Artwork(episode_id=e.id,kind=kind,storage_key=key,width=im.width,height=im.height,size_bytes=p.stat().st_size))
            # Generate a valid 640×360 thumbnail for seeded records. The supplied tiny thumbnail remains available for upload-validation demos.
            if row["season_number"]!=0 and "thumbnail" in row["artwork_available"]:
                from PIL import Image
                source=Image.open(Path(settings.seed_file).parent/"banner_good.jpg").convert("RGB")
                thumb=source.resize((640,360))
                tmp=Path(settings.storage_root)/"seed-thumb.jpg"; thumb.save(tmp,format="JPEG",quality=82)
                key=f"media/{e.episode_id}/thumbnail-seeded.jpg"; storage.save_bytes(key,tmp.read_bytes()); db.add(Artwork(episode_id=e.id,kind="thumbnail",storage_key=key,width=640,height=360,size_bytes=tmp.stat().st_size))
            if row["season_number"]==0 and "thumbnail" in row["artwork_available"]:
                from PIL import Image
                source=Image.open(Path(settings.seed_file).parent/"banner_good.jpg").convert("RGB")
                thumb=source.resize((640,360))
                tmp=Path(settings.storage_root)/"seed-trailer-thumb.jpg"; thumb.save(tmp,format="JPEG",quality=82)
                key=f"media/{e.episode_id}/thumbnail-seeded.jpg"; storage.save_bytes(key,tmp.read_bytes()); db.add(Artwork(episode_id=e.id,kind="thumbnail",storage_key=key,width=640,height=360,size_bytes=tmp.stat().st_size))
    db.commit()
finally: db.close()
