import streamlit as st
import requests
import time
import os
from datetime import datetime

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 60

st.set_page_config(
    page_title="DriveRAG | Enterprise Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DARK THEME CSS ---
st.markdown("""
<style>

:root {
    --primary: #4F46E5;
    --dark-bg: #0B1220;
    --card-bg: #111827;
    --border: #1F2937;
    --text-main: #FFFFFF;
}

/* Main background */
.stApp {
    background-color: var(--dark-bg);
    color: var(--text-main);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #020617;
    color: white;
}

/* Cards */
.main-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 6px 18px rgba(0,0,0,0.4);
}

/* Input */
.stTextInput > div > div > input {
    background-color: white;
    border-radius: 8px;
    padding: 1rem;
    font-size: 1.1rem;
    color: black !important;
}

/* Buttons */
.stButton > button {
    background-color: #1F2937 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
}

.stButton > button:hover {
    background-color: var(--primary) !important;
}

/* Answer box */
.answer-box {
    background-color: var(--card-bg);
    border-radius: 12px;
    padding: 2rem;
    border: 1px solid var(--border);
    margin-top: 2rem;
}

.answer-text {
    font-size: 1.5rem;
}

/* SOURCES BIG STYLE */

.source-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-top: 20px;
}

.source-item {
    background: var(--card-bg);
    border: 1px solid var(--border);
    padding: 18px 24px;
    border-radius: 10px;
    font-size: 1.15rem;
    font-weight: 600;
    color: white;
    box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    transition: all 0.2s ease;
}

.source-item:hover {
    transform: translateY(-4px);
    border-color: var(--primary);
}

</style>
""", unsafe_allow_html=True)

# --- API Helper ---
def api_request(method: str, endpoint: str, **kwargs):
    try:
        url = f"{BACKEND_URL}{endpoint}"
        response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
        return response
    except Exception as e:
        st.error(f"Network error: {str(e)}")
        return None


def check_auth():
    res = api_request("GET", "/auth/status")
    return res.json().get("authenticated", False) if res else False


def get_health():
    res = api_request("GET", "/health")
    return res.json() if res else {}


if "authenticated" not in st.session_state:
    st.session_state.authenticated = check_auth()

# --- Sidebar ---
with st.sidebar:

    st.markdown("# DRIVERAG")
    st.caption("INTERNAL DOCUMENT INTELLIGENCE")

    st.divider()

    health = get_health()

    if health:
        st.success("Network Active")
        st.write(f"Database Records: **{health.get('files_synced', 0)}**")
    else:
        st.error("Network Offline")

    st.divider()

    st.markdown("### System Information")

    st.markdown("""
- **LLM Model:** LLaMA3-8B (Groq)
- **Embedding Model:** all-MiniLM-L6-v2
- **Vector Store:** FAISS
- **Retriever:** Similarity Search
- **Chunk Size:** 500 tokens
""")

    st.divider()

    last_sync = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.caption(f"Last Sync: {last_sync}")

    st.divider()

    if st.session_state.authenticated:

        if st.button("Synchronize Drive"):

            with st.spinner("Syncing..."):

                res = api_request("POST", "/sync-drive")

                if res and res.status_code == 200:
                    st.success("Synchronization complete")
                    time.sleep(1)
                    st.rerun()

        if st.button("Reset Session"):

            res = api_request("POST", "/auth/logout")

            if res and res.status_code == 200:
                st.session_state.authenticated = False
                st.rerun()

    else:

        st.caption("Awaiting authentication")

# --- Main Interface ---

if not st.session_state.authenticated:

    st.title("Document Intelligence")

    if st.button("Authenticate with Google"):

        res = api_request("GET", "/auth/url")

        if res and res.status_code == 200:

            url = res.json().get("url")

            st.markdown(
                f"[Continue to Authentication]({url})"
            )

else:

    st.title("Internal Search")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="main-card">
        <h3>Vector Database</h3>
        <h2>FAISS</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="main-card">
        <h3>Embedding Model</h3>
        <h2>MiniLM</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="main-card">
        <h3>LLM Engine</h3>
        <h2>Groq LLaMA3</h2>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    query = st.text_input(
        "Search Query",
        placeholder="Ask questions about your documents..."
    )

    if st.button("Execute Search"):

        if query.strip():

            with st.spinner("Searching..."):

                res = api_request(
                    "POST",
                    "/ask",
                    json={"query": query}
                )

                if res and res.status_code == 200:

                    data = res.json()

                    st.markdown(
                        f"""
                        <div class="answer-box">
                        <div class="answer-text">
                        {data.get('answer')}
                        </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    sources = data.get("sources", [])

                    if sources:

                        st.markdown("### Sources")

                        st.markdown(
                            '<div class="source-grid">',
                            unsafe_allow_html=True
                        )

                        for s in sources:

                            st.markdown(
                                f'<div class="source-item">📄 {s}</div>',
                                unsafe_allow_html=True
                            )

                        st.markdown(
                            '</div>',
                            unsafe_allow_html=True
                        )

                else:

                    st.error(
                        "System error during search."
                    )

st.divider()