import streamlit as st
import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path so we can import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.rag_service import RAGService

# --- Configuration & Logic ---
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")

st.set_page_config(
    page_title="DriveRAG | Standalone Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize RAG Service (Cached to prevent re-loading models on every rerun)
@st.cache_resource
def get_rag_service():
    return RAGService()

rag_service = get_rag_service()

# --- OAuth Callback Handler ---
# Check if we are returning from a Google Auth redirect
query_params = st.query_params
if "code" in query_params:
    try:
        auth_code = query_params["code"]
        rag_service.complete_auth(auth_code, redirect_uri=REDIRECT_URI)
        st.success("Authentication Successful! You can now start searching.")
        # Clear query params to prevent re-auth on refresh
        st.query_params.clear()
        st.session_state.authenticated = True
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")

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

.stApp {
    background-color: var(--dark-bg);
    color: var(--text-main);
}

[data-testid="stSidebar"] {
    background-color: #020617;
    color: white;
}

.main-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 6px 18px rgba(0,0,0,0.4);
}

.stTextInput > div > div > input {
    background-color: white;
    border-radius: 8px;
    padding: 1rem;
    font-size: 1.1rem;
    color: black !important;
}

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

.answer-box {
    background-color: var(--card-bg);
    border-radius: 12px;
    padding: 2.5rem;
    border: 1px solid var(--border);
    margin-top: 2rem;
}

.answer-text {
    font-size: 1.65rem;
    line-height: 1.5;
}

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
    border-left: 4px solid var(--primary);
}
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = rag_service.is_authenticated()

# --- Sidebar ---
with st.sidebar:
    st.markdown("# DRIVERAG")
    st.caption("STANDALONE INTELLIGENCE")
    st.divider()

    health = rag_service.get_health()
    if health:
        st.success("System Ready")
        st.write(f"Knowledge Base: **{health.get('files_synced', 0)}** Records")

    st.divider()

    if st.session_state.authenticated:
        if st.button("Synchronize Drive", use_container_width=True):
            with st.spinner("Syncing..."):
                try:
                    rag_service.sync_drive()
                    st.success("Sync complete")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Sync error: {str(e)}")
        
        if st.button("Reset Session", use_container_width=True):
            rag_service.logout()
            st.session_state.authenticated = False
            st.rerun()
    else:
        st.caption("Awaiting authentication")

# --- Main Interface ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="main-card" style="text-align: center; margin-top: 5rem;">
            <h1 style="font-size: 2.5rem; color: white;">Document Intelligence</h1>
            <p style="color: #94A3B8; font-size: 1.1rem; margin-bottom: 2rem;">
                Standalone Mode Enabled. Access your Google Drive documents directly from the browser.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Authenticate with Google", use_container_width=True):
            try:
                url = rag_service.get_auth_url(redirect_uri=REDIRECT_URI)
                st.markdown(f"""
                <div style="text-align: center; margin-top: 2rem;">
                    <a href="{url}" target="_blank" style="text-decoration: none;">
                        <div style="background: var(--primary); color: white; padding: 1rem; border-radius: 8px; font-weight: 700; display: inline-block;">
                            CONTINUE TO GOOGLE AUTH
                        </div>
                    </a>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Auth error: {str(e)}")

else:
    st.markdown("<h2 style='font-size: 2.25rem;'>Internal Search</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; margin-bottom: 2rem;'>Semantic retrieval across all indexed assets.</p>", unsafe_allow_html=True)
    
    query = st.text_input(
        "Search Query",
        placeholder="Ask a question...",
        label_visibility="collapsed"
    )

    if st.button("Execute Search") or query:
        if query.strip():
            with st.spinner("Searching..."):
                try:
                    data = rag_service.ask(query)
                    
                    st.markdown(f"""
                    <div class="answer-box">
                        <div class="answer-text">{data.get('answer')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    sources = data.get("sources", [])
                    if sources:
                        st.markdown("<div style='margin-top: 3rem;'>", unsafe_allow_html=True)
                        st.markdown("<div class='source-grid'>", unsafe_allow_html=True)
                        for s in sources:
                            st.markdown(f'<div class="source-item">{s}</div>', unsafe_allow_html=True)
                        st.markdown("</div></div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Search error: {str(e)}")

st.markdown("<br><br><br><div style='border-top: 1px solid var(--border); padding-top: 2rem; text-align: center;'><p style='color: #64748B; font-size: 0.75rem; letter-spacing: 0.1em; font-weight: 600;'>DRIVERAG STANDALONE | DIRECT INTELLIGENCE SYSTEM</p></div>", unsafe_allow_html=True)