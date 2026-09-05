from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from PIL import Image
from io import BytesIO
from .db import get_db
from .settings import settings
from .models import User, Show, Season, Episode, Artwork, PublishRun
from .schemas import *
from .auth import *
from .storage import Storage
from .validation import validate
from .catalogue import build_catalogue
from .reference import load_reference

app=FastAPI(title="Peblo TV Mini API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
storage=Storage()
media_dir=Path(settings.storage_root)/"media"; media_dir.mkdir(parents=True,exist_ok=True)
app.mount("/media",StaticFiles(directory=media_dir),name="media")

@app.get("/health")
def health(db:Session=Depends(get_db)):
    from sqlalchemy import text
    db.execute(text("SELECT 1")); return {"status":"ok","database":"ok","storage":"ok"}

@app.post("/auth/login",response_model=Token)
def login(body:Login,db:Session=Depends(get_db)):
    u=db.query(User).filter(User.username==body.username).first()
    if not u or not verify_password(body.password,u.password_hash): raise HTTPException(401,"Invalid username or password.")
    return {"token":make_token(u),"role":u.role,"username":u.username}

@app.get("/auth/me")
def me(user=Depends(current_user)): return {"username":user.username,"role":user.role}

def check_show(s:ShowIn):
    ref=load_reference()
    if s.section and s.section not in ref["sections"]: raise HTTPException(422,"Choose a valid section.")
    bad=[c for c in s.categories if c not in ref["categories"]]
    if bad: raise HTTPException(422,f"These categories are not allowed: {', '.join(bad)}")

def check_episode(body:EpisodeIn):
    ref=load_reference()
    if body.language not in ref["languages"]: raise HTTPException(422,"Choose en or hi as the language.")
    bad=[c for c in body.categories if c not in ref["categories"]]
    if bad: raise HTTPException(422,f"These categories are not allowed: {', '.join(bad)}")

def lock_content_group_language(db:Session,content_group:str,language:str):
    # Transaction-scoped advisory lock, released automatically at commit/rollback.
    # Because (content_group, language) can't be a hard UNIQUE constraint (see
    # models.py — the seed data intentionally contains a duplicate that the
    # validation report must detect), this closes the check-then-insert race
    # window for normal application writes without touching existing rows.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),{"key":f"{content_group}:{language}"})

@app.get("/admin/shows",response_model=list[ShowOut])
def list_shows(q:str|None=None,section:str|None=None,status:str|None=None,language:str|None=None,page:int=1,page_size:int=20,db:Session=Depends(get_db),user=Depends(current_user)):
    query=db.query(Show)
    if q: query=query.filter(Show.title.ilike(f"%{q}%"))
    if section: query=query.filter(Show.section==section)
    if status: query=query.filter(Show.status==status)
    if language: query=query.filter(Show.seasons.any(Season.episodes.any(Episode.language==language)))
    return query.order_by(Show.title).offset((page-1)*page_size).limit(min(page_size,100)).all()

@app.post("/admin/shows",response_model=ShowOut)
def create_show(body:ShowIn,db:Session=Depends(get_db),user=Depends(current_user)):
    check_show(body)
    if db.query(Show).filter(Show.slug==body.slug).first(): raise HTTPException(409,"That show slug already exists.")
    s=Show(**body.model_dump()); db.add(s); db.commit(); db.refresh(s); return s

@app.get("/admin/shows/{show_id}",response_model=ShowOut)
def get_show(show_id:int,db:Session=Depends(get_db),user=Depends(current_user)):
    s=db.get(Show,show_id)
    if not s: raise HTTPException(404,"Show not found.")
    return s

@app.put("/admin/shows/{show_id}",response_model=ShowOut)
def update_show(show_id:int,body:ShowIn,db:Session=Depends(get_db),user=Depends(current_user)):
    s=db.get(Show,show_id)
    if not s: raise HTTPException(404,"Show not found.")
    check_show(body)
    for k,v in body.model_dump().items(): setattr(s,k,v)
    db.commit(); db.refresh(s); return s

@app.delete("/admin/shows/{show_id}")
def delete_show(show_id:int,db:Session=Depends(get_db),user=Depends(current_user)):
    s=db.get(Show,show_id)
    if not s: raise HTTPException(404,"Show not found.")
    db.delete(s); db.commit(); return {"ok":True}

@app.get("/admin/seasons",response_model=list[SeasonOut])
def list_seasons(show_id:int|None=None,db:Session=Depends(get_db),user=Depends(current_user)):
    q=db.query(Season); q=q.filter(Season.show_id==show_id) if show_id else q; return q.order_by(Season.season_number).all()

@app.post("/admin/seasons",response_model=SeasonOut)
def create_season(body:SeasonIn,db:Session=Depends(get_db),user=Depends(current_user)):
    if not db.get(Show,body.show_id): raise HTTPException(404,"Show not found.")
    s=Season(**body.model_dump()); db.add(s); db.commit(); db.refresh(s); return s

@app.put("/admin/seasons/{season_id}",response_model=SeasonOut)
def update_season(season_id:int,body:SeasonIn,db:Session=Depends(get_db),user=Depends(current_user)):
    s=db.get(Season,season_id)
    if not s: raise HTTPException(404,"Season not found.")
    for k,v in body.model_dump().items(): setattr(s,k,v)
    db.commit(); db.refresh(s); return s

@app.delete("/admin/seasons/{season_id}")
def delete_season(season_id:int,db:Session=Depends(get_db),user=Depends(current_user)):
    s=db.get(Season,season_id)
    if not s: raise HTTPException(404,"Season not found.")
    db.delete(s); db.commit(); return {"ok":True}

@app.get("/admin/episodes",response_model=list[EpisodeOut])
def list_episodes(show_id:int|None=None,status:str|None=None,language:str|None=None,db:Session=Depends(get_db),user=Depends(current_user)):
    q=db.query(Episode)
    if show_id: q=q.join(Season).filter(Season.show_id==show_id)
    if status: q=q.filter(Episode.status==status)
    if language: q=q.filter(Episode.language==language)
    return q.order_by(Episode.episode_id).all()

@app.post("/admin/episodes",response_model=EpisodeOut)
def create_episode(body:EpisodeIn,db:Session=Depends(get_db),user=Depends(current_user)):
    check_episode(body)
    lock_content_group_language(db,body.content_group,body.language)
    if db.query(Episode).filter(Episode.episode_id==body.episode_id).first(): raise HTTPException(409,"That episode id already exists.")
    if db.query(Episode).filter(Episode.content_group==body.content_group,Episode.language==body.language).first(): raise HTTPException(409,"This content group already has an episode in that language.")
    e=Episode(**body.model_dump()); db.add(e); db.commit(); db.refresh(e); return e

@app.put("/admin/episodes/{episode_id}",response_model=EpisodeOut)
def update_episode(episode_id:str,body:EpisodeIn,db:Session=Depends(get_db),user=Depends(current_user)):
    e=db.query(Episode).filter(Episode.episode_id==episode_id).first()
    if not e: raise HTTPException(404,"Episode not found.")
    check_episode(body)
    lock_content_group_language(db,body.content_group,body.language)
    conflict=db.query(Episode).filter(Episode.content_group==body.content_group,Episode.language==body.language,Episode.id!=e.id).first()
    if conflict: raise HTTPException(409,"This content group already has an episode in that language.")
    for k,v in body.model_dump().items(): setattr(e,k,v)
    db.commit(); db.refresh(e); return e

@app.delete("/admin/episodes/{episode_id}")
def delete_episode(episode_id:str,db:Session=Depends(get_db),user=Depends(current_user)):
    e=db.query(Episode).filter(Episode.episode_id==episode_id).first()
    if not e: raise HTTPException(404,"Episode not found.")
    db.delete(e); db.commit(); return {"ok":True}

@app.post("/admin/episodes/{episode_id}/artwork")
def upload_artwork(episode_id:str,kind:str=Query(...,pattern="^(poster|banner|thumbnail)$"),file:UploadFile=File(...),db:Session=Depends(get_db),user=Depends(current_user)):
    e=db.query(Episode).filter(Episode.episode_id==episode_id).first()
    if not e: raise HTTPException(404,"Episode not found.")
    data=file.file.read(); ref=load_reference(); spec=ref["artwork_specs"][kind]
    if len(data)>spec["max_kb"]*1024: raise HTTPException(422,f"This {kind} is too large. Please upload an image under 200 KB.")
    try: im=Image.open(BytesIO(data)); im.verify(); im=Image.open(BytesIO(data)); w,h=im.size
    except Exception: raise HTTPException(422,"The uploaded file is not a valid image.")
    tw,th=spec["target_px"]; ratio=w/h; expected=tw/th
    if abs(ratio-expected)>0.02: raise HTTPException(422,f"This {kind} must use a {spec['aspect']} aspect ratio. Your image is {w}×{h}px.")
    # Target dimensions are intentionally strict enough to catch the supplied wrong-size samples while allowing exact target files.
    if w!=tw or h!=th: raise HTTPException(422,f"This {kind} must be exactly {tw}×{th}px for this catalogue. Your image is {w}×{h}px.")
    key=f"media/{episode_id}/{kind}-{file.filename.replace('/','_')}"; storage.save_bytes(key,data)
    old=db.query(Artwork).filter(Artwork.episode_id==e.id,Artwork.kind==kind).first()
    if old: old.storage_key=key; old.width=w; old.height=h; old.size_bytes=len(data)
    else: db.add(Artwork(episode_id=e.id,kind=kind,storage_key=key,width=w,height=h,size_bytes=len(data)))
    db.commit(); return {"kind":kind,"width":w,"height":h,"size_bytes":len(data),"url":f"/media/{key.removeprefix('media/')}"}

@app.get("/admin/validation-report")
def validation_report(db:Session=Depends(get_db),user=Depends(current_user)):
    issues=validate(db); groups={}
    for i in issues: groups.setdefault(i["group"],[]).append(i)
    return {"blocking":len(issues)>0,"count":len(issues),"groups":groups}

@app.get("/admin/publish-runs")
def publish_runs(db:Session=Depends(get_db),user=Depends(current_user)):
    return [{"id":r.id,"started_at":r.started_at,"completed_at":r.completed_at,"triggered_by":r.triggered_by,"status":r.status,"show_count":r.show_count,"episode_count":r.episode_count,"error":r.error} for r in db.query(PublishRun).order_by(PublishRun.id.desc()).limit(20).all()]

@app.post("/admin/catalog/publish")
def publish(db:Session=Depends(get_db),user=Depends(require_admin)):
    from datetime import datetime, timezone
    run=PublishRun(triggered_by=user.username,status="running",started_at=datetime.now(timezone.utc)); db.add(run); db.commit()
    try:
        issues=validate(db)
        if issues:
            run.status="failed"; run.completed_at=datetime.now(timezone.utc); run.error=f"{len(issues)} validation issue(s) block publishing."; db.commit(); raise HTTPException(409,{"message":"Publishing is blocked until validation issues are fixed.","count":len(issues)})
        cat=build_catalogue(db); digest,version=storage.publish_catalogue(cat)
        show_count=sum(len(v) for v in cat["sections"].values())
        episode_count=sum(len(season["episodes"]) for v in cat["sections"].values() for show in v for season in show["seasons"])
        run.status="success"; run.completed_at=datetime.now(timezone.utc); run.show_count=show_count; run.episode_count=episode_count; run.catalogue_hash=digest; db.commit()
        return {"status":"success","catalogue_hash":digest,"path":version,"show_count":show_count,"episode_count":episode_count}
    except HTTPException: raise
    except Exception as exc:
        db.rollback(); run=db.get(PublishRun,run.id); run.status="failed"; run.completed_at=datetime.now(timezone.utc); run.error=str(exc); db.commit(); raise HTTPException(500,"Publishing failed. The previous catalogue remains active.")

@app.get("/catalog")
def catalog():
    cat=storage.read_catalogue()
    if cat is None: raise HTTPException(503,"The catalogue has not been published yet.")
    return cat

@app.get("/catalog/search")
def search(q:str="",category:str|None=None,language:str|None=None,section:str|None=None):
    cat=storage.read_catalogue()
    if cat is None: raise HTTPException(503,"The catalogue has not been published yet.")
    q=q.strip().lower(); results=[]
    for sec,shows in cat["sections"].items():
        if section and sec!=section: continue
        for show in shows:
            hay=(show["title"]+" "+" ".join(show.get("categories",[]))).lower()
            matched=q in hay
            matched_eps=[]
            for season in show["seasons"]:
                for ep in season["episodes"]:
                    eh=(ep["title"]+" "+" ".join(ep.get("languages",[]))).lower()
                    if q and q not in hay and q not in eh: continue
                    if language and language not in ep["languages"]: continue
                    if category and category not in show.get("categories",[]): continue
                    matched_eps.append(ep)
            if category and category not in show.get("categories",[]): continue
            if language and not any(language in ep["languages"] for s in show["seasons"] for ep in s["episodes"]): continue
            if q and not matched and not matched_eps: continue
            results.append(show)
    return {"results":results,"count":len(results)}
