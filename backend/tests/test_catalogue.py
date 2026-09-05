from app.catalogue import build_catalogue

def test_grouping_is_by_content_group_and_language():
    class E:
        def __init__(self,lang): self.language=lang; self.season=type('S',(),{'season_number':1})(); self.episode_number=1; self.content_group='x'; self.title='T'; self.synopsis=''; self.duration_seconds=10; self.artwork=[]; self.status='published'
    class Sh:
        status='published'; section='featured'; title='A'; slug='a'; synopsis=''; categories=[]; seasons=[type('S',(),{'episodes':[E('hi'),E('en')]})()]
    class Q:
        def filter(self,*a): return self
        def all(self): return [Sh()]
    class DB:
        def query(self,*a): return Q()
    c=build_catalogue(DB()); ep=c['sections']['featured'][0]['seasons'][0]['episodes'][0]
    assert ep['languages']==['en','hi']
