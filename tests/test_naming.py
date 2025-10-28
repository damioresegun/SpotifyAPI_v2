from scripts.playlists import month_key

def test_month_key_format():
    mk = month_key()
    assert len(mk) == 7 and mk[4] == "-"
