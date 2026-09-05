from .reference import load_reference

def validate(db):
    from .models import Show, Episode
    ref=load_reference(); issues=[]
    shows=db.query(Show).all(); episodes=db.query(Episode).all()
    allowed_s=set(ref["sections"]); allowed_c=set(ref["categories"]); allowed_l=set(ref["languages"])
    seen=set()
    for s in shows:
        if s.status=="published" and not s.section:
            issues.append({"group":"Shows","entity":s.title,"field":"section","message":"This published show needs a section.","action":"Choose featured, series, minisodes, or songs."})
        if s.section and s.section not in allowed_s: issues.append({"group":"Shows","entity":s.title,"field":"section","message":f"Section '{s.section}' is not allowed.","action":"Choose an allowed section."})
        for c in s.categories or []:
            if c not in allowed_c: issues.append({"group":"Shows","entity":s.title,"field":"category","message":f"Category '{c}' is not allowed.","action":"Remove it or choose an allowed category."})
    for e in episodes:
        key=(e.content_group,e.language)
        if key in seen: issues.append({"group":"Episodes","entity":e.episode_id,"field":"content_group/language","message":f"The language '{e.language}' is duplicated for content group '{e.content_group}'.","action":"Keep only one episode for this content group and language."})
        seen.add(key)
        if e.language not in allowed_l: issues.append({"group":"Episodes","entity":e.episode_id,"field":"language","message":f"Language '{e.language}' is not allowed.","action":"Choose en or hi."})
        for c in e.categories or []:
            if c not in allowed_c: issues.append({"group":"Episodes","entity":e.episode_id,"field":"category","message":f"Category '{c}' is not allowed.","action":"Choose an allowed category."})
        if e.status=="published":
            if not e.duration_seconds: issues.append({"group":"Episodes","entity":e.episode_id,"field":"duration","message":"A published episode needs a duration.","action":"Enter the episode duration in seconds."})
            kinds={a.kind for a in e.artwork}
            if e.season.season_number==0:
                # Season 0 = trailers. reference.json's convention only guarantees trailers a
                # place outside normal seasons; the only artwork surface a trailer actually
                # renders on (show detail "Trailer" row) is the thumbnail, so that's the one
                # required kind here rather than the full poster+banner+thumbnail set below.
                if "thumbnail" not in kinds: issues.append({"group":"Artwork","entity":e.episode_id,"field":"thumbnail","message":"A trailer needs thumbnail artwork.","action":"Upload a valid 640×360 thumbnail under 200 KB."})
            else:
                required=set(ref["artwork_specs"].keys())
                missing=sorted(required-kinds)
                if missing: issues.append({"group":"Artwork","entity":e.episode_id,"field":"artwork","message":f"A published episode needs all artwork types. Missing: {', '.join(missing)}.","action":"Upload the missing artwork before publishing."})
    return issues
