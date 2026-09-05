from app.catalogue import build_catalogue

class Art:
    def __init__(self, kind, key): self.kind = kind; self.storage_key = key

class E:
    def __init__(self, season_number, ep_num, lang, content_group, artwork_kinds, status="published"):
        self.language = lang
        self.season = type("S", (), {"season_number": season_number})()
        self.episode_number = ep_num
        self.content_group = content_group
        self.title = f"T{ep_num}"
        self.synopsis = ""
        self.duration_seconds = 10
        self.status = status
        self.artwork = [Art(k, f"{content_group}-{lang}-{k}.jpg") for k in artwork_kinds]

class Sh:
    status = "published"; section = "featured"; title = "A"; slug = "a"; synopsis = ""; categories = []
    def __init__(self, seasons): self.seasons = seasons

class Q:
    def filter(self, *a): return self
    def all(self): return self._rows
    def __init__(self, rows): self._rows = rows

class DB:
    def __init__(self, shows): self.shows = shows
    def query(self, *a): return Q(self.shows)


def test_show_artwork_is_deterministic_by_earliest_episode():
    # Two episodes both carry a "poster", but in different (unordered) list positions.
    # The show-level poster must always resolve to the earliest episode's poster
    # (season 1, episode 1), regardless of relationship iteration order.
    ep2 = E(1, 2, "en", "cg2", ["poster", "banner", "thumbnail"])
    ep1 = E(1, 1, "en", "cg1", ["poster", "banner", "thumbnail"])
    season = type("S", (), {"episodes": [ep2, ep1]})()  # deliberately out of order
    show = Sh([season])
    cat = build_catalogue(DB([show]))
    show_obj = cat["sections"]["featured"][0]
    assert show_obj["artwork"]["poster"] == "/media/cg1-en-poster.jpg"


def test_content_group_language_variants_collapse_with_correct_languages():
    ep_en = E(1, 1, "en", "cg1", ["poster", "banner", "thumbnail"])
    ep_hi = E(1, 1, "hi", "cg1", ["poster", "banner", "thumbnail"])
    season = type("S", (), {"episodes": [ep_en, ep_hi]})()
    show = Sh([season])
    cat = build_catalogue(DB([show]))
    ep = cat["sections"]["featured"][0]["seasons"][0]["episodes"][0]
    assert ep["languages"] == ["en", "hi"]
