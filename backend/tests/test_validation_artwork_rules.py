from app.models import Show
from app.validation import validate

class Art:
    def __init__(self, kind): self.kind = kind

class MockEpisode:
    def __init__(self, season_number, kinds, status="published", content_group="cg", language="en", duration=10):
        self.episode_id = f"ep-{season_number}-{language}"
        self.season = type("S", (), {"season_number": season_number})()
        self.status = status
        self.duration_seconds = duration
        self.language = language
        self.content_group = content_group
        self.categories = []
        self.artwork = [Art(k) for k in kinds]

def make_episode(season_number, kinds, status="published", content_group="cg", language="en", duration=10):
    return MockEpisode(season_number, kinds, status, content_group, language, duration)

class Q:
    def __init__(self, rows): self._rows = rows
    def all(self): return self._rows

class DB:
    def __init__(self, shows, episodes): self.shows = shows; self.episodes = episodes
    def query(self, model):
        return Q(self.shows) if model is Show else Q(self.episodes)


def test_normal_published_episode_missing_banner_is_blocked():
    ep = make_episode(1, ["poster", "thumbnail"])  # banner missing
    issues = validate(DB([], [ep]))
    art_issues = [i for i in issues if i["group"] == "Artwork"]
    assert len(art_issues) == 1
    assert "banner" in art_issues[0]["message"]


def test_normal_published_episode_with_all_three_artwork_passes():
    ep = make_episode(1, ["poster", "banner", "thumbnail"])
    issues = validate(DB([], [ep]))
    assert not [i for i in issues if i["group"] == "Artwork"]


def test_trailer_only_needs_thumbnail():
    ep = make_episode(0, ["thumbnail"])  # season 0 = trailer
    issues = validate(DB([], [ep]))
    assert not [i for i in issues if i["group"] == "Artwork"]


def test_trailer_missing_thumbnail_is_blocked():
    ep = make_episode(0, [])
    issues = validate(DB([], [ep]))
    art_issues = [i for i in issues if i["group"] == "Artwork"]
    assert len(art_issues) == 1
    assert "thumbnail" in art_issues[0]["field"]
