# -*- coding: utf-8 -*-
"""
onboarding.py

Multi-step first-run wizard that guides non-technical users through
creating a Spotify Developer App and entering their credentials.
Credentials are persisted in the user's browser localStorage.
"""
from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
from streamlit_local_storage import LocalStorage

# localStorage key names
_KEY_CLIENT_ID = "spm_client_id"
_KEY_CLIENT_SECRET = "spm_client_secret"

# ──────────────────────────────────────────────
# Public helpers
# ──────────────────────────────────────────────

def load_credentials(local_storage: LocalStorage) -> tuple[str | None, str | None]:
    """Read (client_id, client_secret) from browser localStorage.
    Returns (None, None) if not yet saved."""
    cid = local_storage.getItem(_KEY_CLIENT_ID)
    csec = local_storage.getItem(_KEY_CLIENT_SECRET)
    return cid, csec


def clear_credentials(local_storage: LocalStorage) -> None:
    """Remove saved credentials (used by the Settings reset button)."""
    local_storage.deleteItem(_KEY_CLIENT_ID)
    local_storage.deleteItem(_KEY_CLIENT_SECRET)


def show_onboarding(local_storage: LocalStorage) -> bool:
    """Render the onboarding wizard.

    Returns True once the user has completed setup (step 5 confirmed).
    Returns False while the wizard is still in progress.
    """
    if "onboarding_step" not in st.session_state:
        st.session_state["onboarding_step"] = 1

    step = st.session_state["onboarding_step"]

    # Outer glass-card wrapper
    st.markdown("""
    <div style="max-width:680px; margin:2rem auto; padding:2.5rem 3rem;
                background:rgba(255,255,255,0.04); border-radius:20px;
                border:1px solid rgba(255,255,255,0.08);
                backdrop-filter:blur(12px);
                box-shadow:0 8px 32px rgba(0,0,0,0.5);">
    """, unsafe_allow_html=True)

    _progress_bar(step)

    if step == 1:
        _step_welcome()
    elif step == 2:
        _step_create_app()
    elif step == 3:
        _step_redirect_uri()
    elif step == 4:
        _step_enter_credentials(local_storage)
    elif step == 5:
        _step_done()
        st.markdown("</div>", unsafe_allow_html=True)
        return True

    st.markdown("</div>", unsafe_allow_html=True)
    return False


# ──────────────────────────────────────────────
# Private — progress indicator
# ──────────────────────────────────────────────

def _progress_bar(current: int, total: int = 5):
    labels = ["Welcome", "Create App", "Redirect URI", "Enter Keys", "All Done"]
    cols = st.columns(total)
    for i, (col, label) in enumerate(zip(cols, labels)):
        n = i + 1
        if n < current:
            colour, bg, text_col = "#1db954", "#1db954", "#000"
            icon = "✓"
        elif n == current:
            colour, bg, text_col = "#17df64", "linear-gradient(135deg,#1db954,#17df64)", "#fff"
            icon = str(n)
        else:
            colour, bg, text_col = "#64748b", "rgba(255,255,255,0.06)", "#64748b"
            icon = str(n)

        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:0.4rem 0;">
              <div style="width:34px;height:34px;border-radius:50%;background:{bg};color:{text_col};
                          display:inline-flex;align-items:center;justify-content:center;font-weight:700;
                          {'box-shadow:0 0 14px rgba(29,185,84,0.6);' if n == current else ''}
                          font-size:0.85rem;">{icon}</div>
              <div style="font-size:0.7rem;color:{colour};margin-top:4px;font-weight:{'700' if n == current else '400'};">{label}</div>
            </div>""", unsafe_allow_html=True)

    pct = int(((current - 1) / (total - 1)) * 100) if total > 1 else 0
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.08);border-radius:4px;height:4px;margin:0.5rem 0 2rem;">
      <div style="background:linear-gradient(90deg,#1db954,#17df64);width:{pct}%;height:100%;
                  border-radius:4px;transition:width 0.5s ease;"></div>
    </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Step renderers
# ──────────────────────────────────────────────

def _step_welcome():
    st.markdown("""
    <h2 style="font-size:2rem;font-weight:800;margin-bottom:0.5rem;">👋 Welcome to Spotify Manager</h2>
    <p style="color:#94a3b8;font-size:1.05rem;line-height:1.8;margin-bottom:1.2rem;">
        This tool lets you take full control of your&nbsp;Spotify library — create monthly
        playlists automatically, find and remove duplicates, build artist discographies,
        export CSVs, and much more.
    </p>
    <p style="color:#94a3b8;line-height:1.8;">
        To get started you'll need to set up a free
        <strong style="color:#f8fafc;">Spotify Developer App</strong>.
        Don't worry — it sounds technical but takes about&nbsp;<strong style="color:#1db954;">5 minutes</strong>
        and we'll guide you through every click.
    </p>
    <div style="background:rgba(29,185,84,0.08);border:1px solid rgba(29,185,84,0.25);
                border-radius:10px;padding:0.85rem 1rem;margin:1.5rem 0;">
        🔒 <strong>Privacy guarantee:</strong> Your Spotify credentials are stored
        only in <em>your</em> browser and are never transmitted to any external server.
    </div>
    """, unsafe_allow_html=True)

    if st.button("Get Started →", type="primary", key="ob_s1_next"):
        st.session_state["onboarding_step"] = 2
        st.rerun()


def _step_create_app():
    st.markdown("""
    <h2 style="font-size:1.7rem;font-weight:800;margin-bottom:0.4rem;">🛠️ Create Your Spotify Developer App</h2>
    <p style="color:#94a3b8;margin-bottom:1.2rem;">
        Spotify requires every integration to be registered. This gives you a personal
        <strong style="color:#f8fafc;">Client&nbsp;ID</strong> and
        <strong style="color:#f8fafc;">Client&nbsp;Secret</strong> — think of them as
        a username and password that lets this app speak to Spotify on your behalf.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
**Step-by-step:**

1. Click the button below to open the **Spotify Developer Dashboard** — log in with your normal Spotify account
2. Click the blue **"Create app"** button in the top-right corner
3. Fill in the form that appears:
   - **App name** → anything you like, e.g. `My Spotify Manager`
   - **App description** → anything, e.g. `Personal playlist tool`
   - **Redirect URI** → leave blank for now — you'll get the exact value on the next screen
   - **APIs used** → tick ✅ **Web API**
4. Tick the box to agree to Spotify's Developer Terms of Service
5. Click **Save**
""")

    st.link_button(
        "🔗 Open Spotify Developer Dashboard →",
        "https://developer.spotify.com/dashboard",
        type="primary",
    )
    st.caption("Tip: keep the dashboard tab open — you'll need it again in step 3.")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="ob_s2_back"):
            st.session_state["onboarding_step"] = 1
            st.rerun()
    with col2:
        if st.button("I've created my app →", key="ob_s2_next"):
            st.session_state["onboarding_step"] = 3
            st.rerun()


def _step_redirect_uri():
    st.markdown("""
    <h2 style="font-size:1.7rem;font-weight:800;margin-bottom:0.4rem;">🔗 Set the Redirect URI</h2>
    <p style="color:#94a3b8;margin-bottom:1.2rem;">
        Spotify needs to know the exact web address to send you back to after you log in.
        Copy the URL shown below and paste it into your Spotify Developer App's settings.
    </p>
    """, unsafe_allow_html=True)

    # Inject JS to read the current page URL and display it
    components.html("""
    <script>
        const url = window.parent.location.href.split('?')[0].replace(/\/$/, '');
        const box = document.getElementById('redir-box');
        if (box) box.textContent = url;
    </script>
    <div style="background:rgba(29,185,84,0.1);border:1px solid #1db954;border-radius:10px;
                padding:13px 18px;font-family:monospace;color:#1db954;font-size:0.95rem;
                word-break:break-all;user-select:all;cursor:text;">
        <strong>Your redirect URI:</strong><br>
        <span id="redir-box" style="font-size:1rem;">Loading…</span>
    </div>
    <p style="font-size:0.8rem;color:#64748b;margin-top:6px;">
        Click anywhere in the box above and press Ctrl+A, Ctrl+C to copy.
    </p>
    """, height=100)

    st.markdown("""
**Now in the Spotify Developer Dashboard:**

1. Click on the app you just created
2. Click **"Settings"** (top-right of the app page)
3. Find the **"Redirect URIs"** section → click **"Add"**
4. Paste the URL from the green box above **exactly as shown**
5. Click **Save** at the bottom of the page

> ⚠️ The URI must match exactly — including `http` vs `https` and no trailing slash.
""")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="ob_s3_back"):
            st.session_state["onboarding_step"] = 2
            st.rerun()
    with col2:
        if st.button("I've set the redirect URI →", key="ob_s3_next"):
            st.session_state["onboarding_step"] = 4
            st.rerun()


def _step_enter_credentials(local_storage: LocalStorage):
    st.markdown("""
    <h2 style="font-size:1.7rem;font-weight:800;margin-bottom:0.4rem;">🔑 Enter Your Credentials</h2>
    <p style="color:#94a3b8;margin-bottom:0.8rem;">
        Now go back to your Spotify Developer App → click <strong style="color:#f8fafc;">Settings</strong>.
        You'll find your credentials there.
    </p>
    """, unsafe_allow_html=True)

    st.info(
        "**Client ID** is shown directly on the Settings page.  \n"
        "**Client Secret** → click **\"View client secret\"** to reveal it.",
        icon="ℹ️",
    )

    client_id = st.text_input(
        "Client ID",
        placeholder="Paste your Client ID here…",
        key="ob_cid_input",
    )
    client_secret = st.text_input(
        "Client Secret",
        type="password",
        placeholder="Paste your Client Secret here…",
        key="ob_csec_input",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="ob_s4_back"):
            st.session_state["onboarding_step"] = 3
            st.rerun()
    with col2:
        if st.button("Save & Continue →", type="primary", key="ob_s4_save"):
            if not client_id.strip() or not client_secret.strip():
                st.error("Both fields are required — please fill in Client ID and Client Secret.")
            else:
                local_storage.setItem(_KEY_CLIENT_ID, client_id.strip())
                local_storage.setItem(_KEY_CLIENT_SECRET, client_secret.strip())
                st.session_state["spm_client_id"] = client_id.strip()
                st.session_state["spm_client_secret"] = client_secret.strip()
                st.session_state["onboarding_step"] = 5
                st.rerun()


def _step_done():
    st.markdown("""
    <div style="text-align:center;padding:2rem 1rem;">
        <div style="font-size:4rem;margin-bottom:1rem;">🎉</div>
        <h2 style="font-size:2rem;font-weight:800;color:#1db954;margin-bottom:0.5rem;">You're all set!</h2>
        <p style="color:#94a3b8;font-size:1rem;line-height:1.8;max-width:420px;margin:0.8rem auto 2rem;">
            Your credentials have been saved to your browser.
            You only need to do this once — they'll be remembered every time you visit.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.balloons()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Launch Spotify Manager", type="primary", key="ob_s5_launch"):
            st.session_state["onboarding_complete"] = True
            st.session_state.pop("onboarding_step", None)
            st.rerun()
