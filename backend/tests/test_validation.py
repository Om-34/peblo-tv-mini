def test_reference_has_required_specs():
    import json
    r=json.load(open('../seed/reference.json'))
    assert r['artwork_specs']['poster']['max_kb']==200
    assert r['conventions']['season_zero'].startswith('Season 0')
