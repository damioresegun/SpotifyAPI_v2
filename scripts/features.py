from __future__ import annotations
import logging
import random
import requests
import pandas as pd
from .playlists import ensure_playlist

logger = logging.getLogger(__name__)

def save_top_tracks_playlist(sp, user_id: str, time_range: str = "short_term", limit: int = 50) -> dict:
    """Fetch user's top tracks and save them to a playlist."""
    res = sp.current_user_top_tracks(time_range=time_range, limit=limit)
    tracks = res.get("items", [])
    if not tracks:
        return {"error": "No top tracks found."}
    
    uris = [t["uri"] for t in tracks]
    
    mapping = {
        "short_term": "Top Tracks (Last 4 Weeks)",
        "medium_term": "Top Tracks (Last 6 Months)",
        "long_term": "Top Tracks (All Time)"
    }
    playlist_name = mapping.get(time_range, "My Top Tracks")
    
    pid = ensure_playlist(sp, user_id, playlist_name, public=False)
    sp.playlist_replace_items(pid, uris)
    
    return {"playlist_id": pid, "playlist_name": playlist_name, "count": len(uris)}


def build_discography(sp, user_id: str, artist_id: str, artist_name: str) -> dict:
    """Pulls all albums by an artist, chronologically saves all tracks."""
    albums = []
    limit, offset = 50, 0
    while True:
        res = sp.artist_albums(artist_id, album_type="album,single", limit=limit, offset=offset)
        albums.extend(res.get("items", []))
        if res.get("next"):
            offset += limit
        else:
            break
            
    albums.sort(key=lambda x: x.get("release_date", "1970-01-01"))
    
    track_uris = []
    seen_track_names = set()
    
    for album in albums:
        a_id = album["id"]
        res = sp.album_tracks(a_id, limit=50)
        for t in res.get("items", []):
            name = t["name"].lower()
            if name not in seen_track_names:
                track_uris.append(t["uri"])
                seen_track_names.add(name)
                
    if not track_uris:
        return {"error": "No tracks found for this artist."}
        
    playlist_name = f"{artist_name}: Complete Discography"
    pid = ensure_playlist(sp, user_id, playlist_name, public=False)
    
    sp.playlist_replace_items(pid, [])
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(pid, track_uris[i:i+100])
        
    return {"playlist_name": playlist_name, "count": len(track_uris)}


def find_and_remove_duplicates(sp, playlist_id: str, playlist_name: str) -> dict:
    """Finds meta-duplicates in a playlist, strips them entirely, appends one instance back."""
    limit, offset = 100, 0
    seen_signatures = set()
    dupes_uris = set()
    
    while True:
        res = sp.playlist_items(playlist_id, fields="items(track(uri,name,artists(name))),next", limit=limit, offset=offset)
        items = res.get("items", [])
        if not items:
            break
        for it in items:
            t = it.get("track")
            if not t: continue
            uri = t.get("uri")
            name = t.get("name", "").lower()
            artist = t.get("artists", [{}])[0].get("name", "").lower()
            signature = f"{name}::{artist}"
            
            if signature in seen_signatures:
                dupes_uris.add(uri)
            else:
                seen_signatures.add(signature)
                
        if res.get("next"):
            offset += limit
        else:
            break
            
    if not dupes_uris:
        return {"removed": 0}
        
    # Standard removal (removes ALL occurrences of the passed URIs)
    # Then we add exactly ONE of each duplicate URI back to the end
    to_remove = [{"uri": u} for u in dupes_uris]
    
    # We remove them natively in chunks of 100
    for i in range(0, len(to_remove), 100):
        sp.playlist_remove_specific_occurrences_of_items(playlist_id, to_remove[i:i+100])
        
    # Append exactly 1 copy of the duplicates back to the playlist
    back_add = list(dupes_uris)
    for i in range(0, len(back_add), 100):
        sp.playlist_add_items(playlist_id, back_add[i:i+100])
        
    return {"removed": len(dupes_uris), "playlist_name": playlist_name}

def blend_playlists(sp, user_id: str, playlist_ids: list[str], target_name: str = "Blended Playlist") -> dict:
    all_uris = set()
    for pid in playlist_ids:
        limit, offset = 100, 0
        while True:
            res = sp.playlist_items(pid, fields="items(track(uri)),next", limit=limit, offset=offset)
            for it in res.get("items", []):
                t = it.get("track")
                if t and t.get("uri"):
                    all_uris.add(t["uri"])
            if res.get("next"):
                offset += limit
            else:
                break
                
    uris_list = list(all_uris)
    random.shuffle(uris_list)
    
    if not uris_list: return {"error": "Selected playlists were empty."}
    
    pid = ensure_playlist(sp, user_id, target_name, public=False)
    sp.playlist_replace_items(pid, [])
    for i in range(0, len(uris_list), 100):
        sp.playlist_add_items(pid, uris_list[i:i+100])
        
    return {"playlist_name": target_name, "count": len(uris_list)}


def build_time_machine(sp, user_id: str, year: int) -> dict:
    # We will grab 50 top tracks released in that year
    res = sp.search(q=f"year:{year}", type="track", limit=50)
    tracks = res.get("tracks", {}).get("items", [])
    if not tracks: return {"error": f"No tracks found for {year}."}
    
    uris = [t["uri"] for t in tracks]
    name = f"Time Machine: {year}"
    pid = ensure_playlist(sp, user_id, name, public=False)
    sp.playlist_replace_items(pid, uris)
    return {"playlist_name": name, "count": len(uris)}


def export_playlist_csv(sp, playlist_id: str) -> str:
    limit, offset = 100, 0
    data = []
    while True:
        res = sp.playlist_items(playlist_id, fields="items(track(name,album(name),artists(name))),next", limit=limit, offset=offset)
        for it in res.get("items", []):
            t = it.get("track")
            if not t: continue
            data.append({
                "Track": t.get("name", "Unknown"),
                "Artist": t.get("artists", [{}])[0].get("name", "Unknown"),
                "Album": t.get("album", {}).get("name", "Unknown")
            })
        if res.get("next"):
            offset += limit
        else:
            break
    df = pd.DataFrame(data)
    return df.to_csv(index=False)


def recreate_live_setlist(sp, user_id: str, api_key: str, artist_name: str) -> dict:
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    url = f"https://api.setlist.fm/rest/1.0/search/setlists?artistName={requests.utils.quote(artist_name)}&p=1"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return {"error": f"Setlist.fm API Error: {r.status_code}. Are you sure your API key is correct?"}
        
    data = r.json()
    setlists = data.get("setlist", [])
    if not setlists: return {"error": "No setlists found for this artist."}
    
    # Extract the first valid setlist with songs
    songs_to_find = []
    target_set = None
    for s in setlists:
        sets = s.get("sets", {}).get("set", [])
        for subset in sets:
            for act in subset.get("song", []):
                if act.get("name"):
                    songs_to_find.append(act["name"])
        if songs_to_find:
            target_set = s
            break
            
    if not songs_to_find: return {"error": "Recent setlists exist, but they have no tracked songs!"}
    
    uris = []
    for song in songs_to_find:
        search_res = sp.search(q=f"track:{song} artist:{artist_name}", type="track", limit=1)
        tracks = search_res.get("tracks", {}).get("items", [])
        if tracks:
            uris.append(tracks[0]["uri"])
            
    if not uris: return {"error": "Could not map setlist songs to Spotify catalog."}
    
    venue = target_set.get("venue", {}).get("name", "Unknown Venue")
    name = f"{artist_name} Live at {venue}"
    pid = ensure_playlist(sp, user_id, name, public=False)
    sp.playlist_replace_items(pid, uris)
    return {"playlist_name": name, "count": len(uris)}

def get_live_player(sp) -> dict:
    try:
        res = sp.current_user_playing_track()
        if not res or not res.get("item"):
            return {"playing": False}
        t = res["item"]
        return {
            "playing": res.get("is_playing", False),
            "track": t.get("name", "Unknown"),
            "artist": t.get("artists", [{}])[0].get("name", "Unknown"),
            "image": t.get("album", {}).get("images", [{}])[0].get("url", "")
        }
    except:
        return {"error": "Could not access playback"}

def save_recent_history(sp, user_id: str) -> dict:
    res = sp.current_user_recently_played(limit=50)
    items = res.get("items", [])
    if not items: return {"error": "No recent listening history found."}
    
    uris = [it["track"]["uri"] for it in items]
    name = "Listening History Tracker"
    pid = ensure_playlist(sp, user_id, name, public=False)
    sp.playlist_replace_items(pid, uris)
    return {"playlist_name": name, "count": len(uris)}

def get_top_artists_df(sp, time_range="medium_term") -> pd.DataFrame:
    res = sp.current_user_top_artists(time_range=time_range, limit=50)
    items = res.get("items", [])
    data = []
    for rank, a in enumerate(items, 1):
        data.append({
            "Rank": rank,
            "Artist": a.get("name", "Unknown"),
            "Followers": a.get("followers", {}).get("total", 0),
            "Genres": ", ".join(a.get("genres", [])[:3])
        })
    return pd.DataFrame(data)

def prune_empty_followers(sp) -> dict:
    # Get top listened artists (long term) to ensure we don't accidentally prune favorites
    top_res = sp.current_user_top_artists(time_range="long_term", limit=50)
    top_ids = {a["id"] for a in top_res.get("items", [])}
    
    # Get currently followed
    followed_ids = set()
    last_id = None
    while True:
        f_res = sp.current_user_followed_artists(limit=50, after=last_id)
        f_items = f_res.get("artists", {}).get("items", [])
        if not f_items: break
        for a in f_items: followed_ids.add((a["id"], a["name"]))
        last_id = f_items[-1]["id"]
        
    to_unfollow = []
    for aid, aname in followed_ids:
        if aid not in top_ids:
            to_unfollow.append((aid, aname))
            
    if not to_unfollow: return {"unfollowed": []}
    
    # We will only unfollow 50 at a time safely to preview
    strip_ids = [aid for aid, aname in to_unfollow[:50]]
    if strip_ids:
        sp.user_unfollow_artists(strip_ids)
        
    return {"unfollowed": [aname for aid, aname in to_unfollow[:50]]}


def cleanse_dead_tracks(sp, playlist_id: str, market: str) -> dict:
    limit, offset = 100, 0
    removed_tracks = []
    dead_uris = []
    
    while True:
        res = sp.playlist_items(playlist_id, fields="items(track(uri,name,available_markets)),next", limit=limit, offset=offset)
        items = res.get("items", [])
        if not items: break
        for it in items:
            t = it.get("track")
            if not t: continue
            
            markets = t.get("available_markets", [])
            is_dead = False
            if markets and market not in markets:
                is_dead = True
                
            if is_dead and t.get("uri"):
                dead_uris.append(t["uri"])
                removed_tracks.append(t.get("name", "Unknown"))
                
        if res.get("next"):
            offset += limit
        else:
            break
            
    if dead_uris:
        to_remove = [{"uri": u} for u in dead_uris]
        for i in range(0, len(to_remove), 100):
            sp.playlist_remove_specific_occurrences_of_items(playlist_id, to_remove[i:i+100])
            
    return {"removed_count": len(dead_uris), "tracks": removed_tracks}
