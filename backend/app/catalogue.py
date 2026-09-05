from collections import defaultdict

def build_catalogue(db):
    from .models import Show
    shows=db.query(Show).filter(Show.status=="published").all()
    out={"version":1,"sections":{}}
    for show in sorted(shows,key=lambda s:(s.section or "",s.title.lower(),s.slug)):
        eps=[e for season in show.seasons for e in season.episodes if e.status=="published"]
        normal=[e for e in eps if e.season.season_number!=0]
        trailers=[e for e in eps if e.season.season_number==0]
        grouped={}
        for e in normal:
            grouped.setdefault((e.season.season_number,e.episode_number,e.content_group),[]).append(e)
        seasons=defaultdict(list)
        for key,variants in grouped.items():
            variants=sorted(variants,key=lambda e:e.language)
            first=variants[0]
            artwork={a.kind:f"/media/{a.storage_key}" for a in first.artwork}
            seasons[key[0]].append({"content_group":key[2],"episode_number":key[1],"title":first.title,"synopsis":first.synopsis,"duration_seconds":first.duration_seconds,"languages":[e.language for e in variants],"artwork":artwork})
        show_obj={"slug":show.slug,"title":show.title,"synopsis":show.synopsis,"section":show.section,"categories":show.categories or [],"artwork":{},"seasons":[],"trailers":[]}
        # Show-level artwork is derived from the earliest published episode (by season,
        # episode number, then content_group) that has each kind, so the choice is
        # deterministic and stable across publishes rather than depending on unordered
        # ORM relationship iteration order.
        eps_in_order=sorted(eps,key=lambda e:(e.season.season_number,e.episode_number,e.content_group,e.language))
        for kind in ("poster","banner","thumbnail"):
            match=next((a for e in eps_in_order for a in e.artwork if a.kind==kind),None)
            if match: show_obj["artwork"][kind]=f"/media/{match.storage_key}"
        for sn in sorted(seasons):
            show_obj["seasons"].append({"season_number":sn,"episodes":sorted(seasons[sn],key=lambda x:(x["episode_number"],x["title"].lower()))})
        for e in sorted(trailers,key=lambda x:(x.episode_number,x.title.lower())):
            art={a.kind:f"/media/{a.storage_key}" for a in e.artwork}
            show_obj["trailers"].append({"content_group":e.content_group,"title":e.title,"languages":[e.language],"duration_seconds":e.duration_seconds,"artwork":art})
        out["sections"].setdefault(show.section,[]).append(show_obj)
    return out
