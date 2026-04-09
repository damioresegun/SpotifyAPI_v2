import os
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image
from datetime import datetime
from dateutil.relativedelta import relativedelta
from streamlit_local_storage import LocalStorage

from scripts.config import Settings
from scripts.monthly import run_monthly_backfill
from scripts.weekly import run_discover_weekly_archive
from scripts.delete import run_delete
import scripts.features as feat
from onboarding import show_onboarding, load_credentials, clear_credentials

# Initialise browser localStorage bridge (reads persisted credentials)
_local_storage = LocalStorage()

try:
    logo_image = Image.open("logo.png")
except Exception:
    logo_image = "🎵"

st.set_page_config(page_title="Spotify Manager", page_icon=logo_image, layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

/* Apply modern font globally */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
}

/* Premium gradient background */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
    color: #f8fafc;
}

/* Center App Level Text */
.stApp, .block-container, p, h1, h2, h3, h4, h5, h6, label, .stMarkdown {
    text-align: center !important;
}

/* Glassmorphism for expanders and layout elements */
[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

/* Center tabs and style them */
[data-baseweb="tab-list"] {
    justify-content: center;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 12px;
    padding: 5px;
    gap: 5px;
}

[data-baseweb="tab"] {
    justify-content: center;
    background: transparent;
    color: #94a3b8;
    border-radius: 8px;
    transition: all 0.3s ease;
    border: none !important;
}

[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(29, 185, 84, 0.2) !important;
    color: #1db954 !important;
}

[data-baseweb="tab"]:hover {
    background: rgba(255, 255, 255, 0.05);
}

/* Button Micro-animations & Glassmorphism */
.stButton, .stDownloadButton {
    display: flex;
    justify-content: center;
}

.stButton > button, .stDownloadButton > button {
    background: linear-gradient(90deg, #1db954 0%, #17df64 100%);
    color: #000 !important;
    border: none;
    border-radius: 24px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(29, 185, 84, 0.3);
}

.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(29, 185, 84, 0.5);
    color: #000 !important;
    border: none;
}

/* Center widget text and labels */
[data-testid="stCheckbox"] {
    display: flex;
    justify-content: center;
    width: 100%;
}

[data-testid="stWidgetLabel"] {
    display: flex;
    justify-content: center;
}

/* Center the image */
[data-testid="stImage"] {
    display: flex;
    justify-content: center;
    margin: 0 auto;
}

/* Customize scrollbar */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.05); 
}
::-webkit-scrollbar-thumb {
    background: #1db954; 
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: #17df64; 
}
</style>
""", unsafe_allow_html=True)

if isinstance(logo_image, Image.Image):
    col_l, col_m, col_r = st.columns([2, 1, 2])
    with col_m:
        st.image(logo_image, width=160)

st.title("Spotify Manager")

# ── Sidebar: settings reset ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if st.button("🔄 Update Spotify Credentials", key="sidebar_reset_creds"):
        clear_credentials(_local_storage)
        for k in ["spm_client_id", "spm_client_secret", "token_info", "onboarding_complete", "onboarding_step"]:
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown("---")
    st.caption("Spotify Manager · Personal Edition")

# ── Credential resolution ────────────────────────────────────────────────────
# Priority: session_state (already loaded this tab) → localStorage → wizard
_cid  = st.session_state.get("spm_client_id")
_csec = st.session_state.get("spm_client_secret")

if not _cid or not _csec:
    _stored_cid, _stored_csec = load_credentials(_local_storage)
    if _stored_cid and _stored_csec:
        st.session_state["spm_client_id"] = _stored_cid
        st.session_state["spm_client_secret"] = _stored_csec
        _cid, _csec = _stored_cid, _stored_csec

if not _cid or not _csec:
    # Show onboarding wizard — stop here until complete
    if show_onboarding(_local_storage):
        st.rerun()   # wizard just completed → reload to enter main app
    st.stop()

# Credentials confirmed — inject into os.environ for Settings.from_env()
os.environ["SPOTIPY_CLIENT_ID"]     = _cid
os.environ["SPOTIPY_CLIENT_SECRET"] = _csec
os.environ.setdefault("SPOTIPY_REDIRECT_URI", "http://localhost:8501")

# ── Spotify client setup ─────────────────────────────────────────────────────
settings = Settings.from_env()
scope = os.getenv(
    "SCOPE",
    "user-library-read playlist-modify-public playlist-modify-private "
    "playlist-read-private user-top-read user-read-recently-played",
)

sp_oauth = SpotifyOAuth(
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    redirect_uri=settings.redirect_uri,
    scope=scope,
    cache_handler=spotipy.cache_handler.MemoryCacheHandler(),
)

if "code" in st.query_params:
    code = st.query_params["code"]
    sp_oauth.get_access_token(code)
    token_info = sp_oauth.get_cached_token()
    if token_info:
        st.session_state["token_info"] = token_info
    st.query_params.clear()

if "token_info" not in st.session_state:
    st.warning("You are not connected to Spotify.")
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"**[Click here to Connect to Spotify]({auth_url})**")
    st.stop()

token_info = st.session_state["token_info"]
if sp_oauth.is_token_expired(token_info):
    token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
    st.session_state["token_info"] = token_info

sp = spotipy.Spotify(auth=token_info["access_token"])

try:
    user = sp.current_user()
    st.success(f"✅ Securely Connected as **{user.get('display_name', user.get('id'))}**")
except Exception as e:
    st.error(f"Failed to connect to Spotify: {e}")
    st.stop()

st.divider()

# ------ TABS ------
tab_monthly, tab_cleaner, tab_wrapped, tab_disco, tab_dupes, tab_blend, tab_time, tab_export, tab_setlist, tab_player, tab_stats, tab_market = st.tabs([
    "📅 Monthly", 
    "🧹 Playlist Cleaner", 
    "📊 Top Tracks", 
    "💽 Discography", 
    "👯 Duplicate Finder",
    "🔀 Blender",
    "🕰️ Time Machine",
    "🗄️ Exporter",
    "🎧 Live Setlists",
    "📻 Player & History",
    "👤 Profile Stats",
    "🌍 Dead Song Checker"
])

# ----- TAB 1: Monthly -----
with tab_monthly:
    st.header("📅 Monthly Playlists")
    retroactive = st.checkbox("Retroactively create past playlists?", value=False)
    if retroactive:
        col1, col2 = st.columns(2)
        with col1: start_date = st.date_input("Start Date", value=datetime.today() - relativedelta(months=2))
        with col2: end_date = st.date_input("End Date", value=datetime.today())
        start_yyyymm = start_date.strftime("%Y-%m")
        end_yyyymm = end_date.strftime("%Y-%m")
        
        if st.button("Generate Retroactive Playlists"):
            if start_date > end_date: st.error("Start date cannot be after end date.")
            else:
                with st.spinner("Generating..."):
                    try:
                        res = run_monthly_backfill(sp, user["id"], "", settings.monthly_format, start_yyyymm, until_yyyymm=end_yyyymm)
                        for item in res.get("created_or_updated", []):
                            st.write(f"- **{item['playlist_name']}**: Added {item['added']} new tracks.")
                        st.success("Finished!")
                    except Exception as e: st.error(f"Error: {e}")
    else:
        if st.button("Generate Current Month Playlist"):
            with st.spinner("Updating..."):
                try:
                    res = run_monthly_backfill(sp, user["id"], "", settings.monthly_format, datetime.today().strftime("%Y-%m"), until_yyyymm=datetime.today().strftime("%Y-%m"))
                    if res.get("created_or_updated"):
                        info = res["created_or_updated"][0]
                        if info['added'] > 0: st.success(f"Added {info['added']} tracks to **{info['playlist_name']}**!")
                        else: st.info(f"**{info['playlist_name']}** is already up to date.")
                except Exception as e: st.error(f"Error: {e}")

# ----- TAB 2: Playlist Cleaner -----
with tab_cleaner:
    st.header("🧹 Playlist Cleaner")
    st.write("Batch unfollow (delete) playlists that match a specific naming pattern.")
    pattern = st.text_input("Regex or Text Pattern (e.g., 'Monthly' or '^2021')")
    col1, col2 = st.columns(2)
    if pattern:
        with col1:
            if st.button("Preview Deletions"):
                with st.spinner("Scanning..."):
                    res = run_delete(sp, user["id"], pattern, dry_run=True)
                    st.info(f"Found {res['matched']} playlists matching '{pattern}'.")
                    for p in res.get("playlists", []):
                        st.write(f"- {p[1]}")
        with col2:
            if st.button("🔴 Confirm Delete", type="primary"):
                with st.spinner("Deleting..."):
                    res = run_delete(sp, user["id"], pattern, dry_run=False)
                    st.success(f"Successfully deleted {res['matched']} playlists.")

# ----- TAB 3: On-Demand Wrapped -----
with tab_wrapped:
    st.header("📊 Top Tracks (Wrapped)")
    st.write("Generate playlists from your most listened to tracks.")
    range_map = {"Last 4 Weeks": "short_term", "Last 6 Months": "medium_term", "All Time": "long_term"}
    selected_range = st.radio("Timeframe", list(range_map.keys()))
    if st.button("Generate Top Tracks Playlist"):
        with st.spinner("Fetching data..."):
            try:
                res = feat.save_top_tracks_playlist(sp, user["id"], range_map[selected_range])
                if "error" in res: st.error(res["error"])
                else: st.success(f"Generated playlist **{res['playlist_name']}** with {res['count']} tracks!")
            except Exception as e: st.error(e)

# ----- TAB 4: Discography -----
with tab_disco:
    st.header("💽 Discography Builder")
    st.write("Search for an artist to fetch every track they've released chronologically.")
    artist_q = st.text_input("Search Artist Name:")
    
    if st.button("Search Artist"):
        with st.spinner("Searching..."):
            search_res = sp.search(artist_q, type="artist", limit=10)
            st.session_state["disco_search_results"] = search_res.get("artists", {}).get("items", [])
            
    if "disco_search_results" in st.session_state and st.session_state["disco_search_results"]:
        items = st.session_state["disco_search_results"]
        artist_options = { f"{a['name']} ({a.get('followers', {}).get('total', 0):,} followers)" : a for a in items }
        selected_artist_label = st.selectbox("Select the correct artist:", list(artist_options.keys()))
        
        if st.button("Build Artist Discography"):
            artist = artist_options[selected_artist_label]
            with st.spinner(f"Building {artist['name']}'s Discography..."):
                try:
                    res = feat.build_discography(sp, user["id"], artist["id"], artist["name"])
                    if "error" in res: st.error(res["error"])
                    else: st.success(f"Created **{res['playlist_name']}** with {res['count']} tracks!")
                except Exception as e: st.error(e)

# ----- TAB 5: Duplicates -----
with tab_dupes:
    st.header("👯 Duplicate Finder")
    st.write("Prune repeating tracks from your playlists.")
    # Fetch 50 playlists for the dropdown
    if "user_playlists" not in st.session_state:
        st.session_state["user_playlists"] = []
    
    if st.button("Load My Playlists"):
        with st.spinner("Fetching..."):
            pl_res = sp.current_user_playlists(limit=50)
            st.session_state["user_playlists"] = pl_res.get("items", [])
            st.success("Loaded!")
            
    if st.session_state["user_playlists"]:
        pl_choices = {p["name"]: p["id"] for p in st.session_state["user_playlists"] if p["owner"]["id"] == user["id"]}
        if not pl_choices:
            st.warning("No playlists found that you own.")
        else:
            selected_pl = st.selectbox("Select a Playlist to Prune", list(pl_choices.keys()))
            if st.button("Prune Duplicates"):
                with st.spinner("Scanning structure..."):
                    try:
                        res = feat.find_and_remove_duplicates(sp, pl_choices[selected_pl], selected_pl)
                        removed = res.get("removed", 0)
                        if removed > 0:
                            st.success(f"Successfully pruned {removed} duplicated tracks from {selected_pl}.")
                        else:
                            st.info("No duplicates found in this playlist!")
                    except Exception as e: st.error(e)

# ----- TAB 6: Blender -----
with tab_blend:
    st.header("🔀 Master Blender")
    st.write("Combine multiple playlists into one giant shuffled mega-playlist.")
    if st.session_state.get("user_playlists"):
        pl_choices = {p["name"]: p["id"] for p in st.session_state["user_playlists"]}
        selected_pls = st.multiselect("Select Playlists to Blend", list(pl_choices.keys()))
        target_name = st.text_input("New Playlist Name", value="My Blend")
        if selected_pls and target_name and st.button("Blend Playlists"):
            with st.spinner("Blending..."):
                try:
                    target_ids = [pl_choices[name] for name in selected_pls]
                    res = feat.blend_playlists(sp, user["id"], target_ids, target_name)
                    if "error" in res: st.error(res["error"])
                    else: st.success(f"Created '{res['playlist_name']}' with {res['count']} tracks!")
                except Exception as e: st.error(e)
    else:
        st.info("Please go to 'Duplicate Finder' tab and load your playlists first.")

# ----- TAB 7: Time Machine -----
with tab_time:
    st.header("🕰️ Time Machine")
    st.write("Generate a playlist of the top 50 hits from a specific year.")
    target_year = st.number_input("Year", min_value=1950, max_value=2026, value=2010)
    if st.button("Travel in Time"):
        with st.spinner("Warping..."):
            try:
                res = feat.build_time_machine(sp, user["id"], int(target_year))
                if "error" in res: st.error(res["error"])
                else: st.success(f"Created '{res['playlist_name']}'!")
            except Exception as e: st.error(e)

# ----- TAB 8: Exporter -----
with tab_export:
    st.header("🗄️ Playlist Exporter")
    st.write("Download a hard backup of any playlist as a CSV file.")
    if st.session_state.get("user_playlists"):
        pl_choices = {p["name"]: p["id"] for p in st.session_state["user_playlists"]}
        selected_pl = st.selectbox("Select Playlist to Export", list(pl_choices.keys()))
        if st.button("Generate CSV"):
            with st.spinner("Compiling CSV..."):
                try:
                    csv_data = feat.export_playlist_csv(sp, pl_choices[selected_pl])
                    st.download_button(label="Download CSV", data=csv_data, file_name=f"{selected_pl}.csv", mime="text/csv")
                except Exception as e: st.error(e)
    else:
        st.info("Please go to 'Duplicate Finder' tab and load your playlists first.")

# ----- TAB 10: Setlist Builder -----
with tab_setlist:
    st.header("🎧 Live Setlist Recreator")
    st.write("Requires a Setlist.fm Developer API Key.")
    api_key_input = st.text_input("Setlist.fm API Key", type="password")
    live_artist_q = st.text_input("Traveling Artist Name")
    
    if st.button("Recreate Latest Setlist"):
        if not api_key_input or not live_artist_q:
            st.error("Both fields are required.")
        else:
            with st.spinner("Scraping Setlists and Spotify..."):
                try:
                    res = feat.recreate_live_setlist(sp, user["id"], api_key_input, live_artist_q)
                    if "error" in res: st.error(res["error"])
                    else: st.success(f"Successfully recreated '{res['playlist_name']}'!")
                except Exception as e: st.error(e)

# ----- TAB: Player & History -----
with tab_player:
    st.header("📻 Player & History")
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("Live Player", expanded=True):
            if st.button("Refresh Player"):
                player_state = feat.get_live_player(sp)
                if "error" in player_state:
                    st.error(player_state["error"])
                elif not player_state.get("playing"):
                    st.info("No music currently playing.")
                else:
                    st.success(f"**Playing**: {player_state['track']} by {player_state['artist']}")
                    if player_state.get("image"):
                        st.image(player_state["image"], width=200)
    
    with col2:
        with st.expander("History Logger", expanded=True):
            st.write("Save your last 50 played tracks.")
            if st.button("Log History to Playlist"):
                with st.spinner("Fetching..."):
                    res = feat.save_recent_history(sp, user["id"])
                    if "error" in res: st.error(res["error"])
                    else: st.success(f"Logged {res['count']} tracks to '{res['playlist_name']}'.")

# ----- TAB: Profile Stats -----
with tab_stats:
    st.header("👤 Profile Stats")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        with st.expander("Top Artists (All Time)", expanded=True):
            if st.button("Load Top Artists"):
                with st.spinner("Loading..."):
                    df = feat.get_top_artists_df(sp, "long_term")
                    st.dataframe(df, use_container_width=True)
                    
    with col_s2:
        with st.expander("Follower Pruner", expanded=True):
            st.write("Unfollow up to 50 artists you follow but don't actively listen to.")
            st.warning("⚠️ This modifies your Spotify library.")
            if st.button("Prune Dead Followers"):
                with st.spinner("Scanning..."):
                    res = feat.prune_empty_followers(sp)
                    unf = res.get("unfollowed", [])
                    if not unf: st.info("No inactive followers to prune right now!")
                    else:
                        st.success(f"Unfollowed {len(unf)} artists:")
                        for a in unf: st.write(f"- {a}")

# ----- TAB: Dead Song Checker -----
with tab_market:
    st.header("🌍 Dead Song Checker")
    st.write("Scan a playlist and completely strip away greyed-out tracks that are not playable in your country.")
    if st.session_state.get("user_playlists"):
        pl_choices = {p["name"]: p["id"] for p in st.session_state["user_playlists"] if p["owner"]["id"] == user["id"]}
        if pl_choices:
            selected_pl = st.selectbox("Select Playlist to Scan", list(pl_choices.keys()))
            if st.button("Scan & Cleanse"):
                if not user.get("country"):
                    st.error("Spotify doesn't broadcast your country code. Cannot verify markets.")
                else:
                    with st.spinner("Cleansing..."):
                        res = feat.cleanse_dead_tracks(sp, pl_choices[selected_pl], user["country"])
                        if res.get("removed_count", 0) > 0:
                            st.success(f"Removed {res['removed_count']} unplayable dead tracks.")
                            for nt in res.get("tracks", []): st.write(f"- {nt}")
                        else:
                            st.info("Playlist is 100% playable in your country!")
        else:
            st.warning("No playlists you own.")
    else:
        st.info("Load your playlists first in the Duplicate Finder tab.")
