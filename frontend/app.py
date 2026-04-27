import streamlit as st
import requests
import time

import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT = 600

st.set_page_config(
    page_title="DriveRAG — Google Drive Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

.main {
    background-color: #f8f9fa;
}

.stButton>button {
    width: 100%;
    border-radius: 8px;
    height: 3em;
    background-color: #4F46E5;
    color: white;
    font-weight: 600;
    border: none;
    transition: all 0.3s ease;
}

.stButton>button:hover {
    background-color: #4338CA;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    transform: translateY(-2px);
}

.answer-box {
    background-color: white;
    padding: 2rem;
    border-radius: 12px;
    border-left: 5px solid #4F46E5;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    margin-bottom: 2rem;
    line-height: 1.6;
    color: #374151;
}

.source-tag {
    display: inline-block;
    background-color: #E0E7FF;
    color: #3730A3;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.85rem;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    border: 1px solid #C7D2FE;
}

.login-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    background-color: white;
    border-radius: 16px;
    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    text-align: center;
    max-width: 600px;
    margin: auto;
}

h1, h2, h3 {
    color: #111827;
}
</style>
""", unsafe_allow_html=True)

def check_auth():
    try:
        res = requests.get(f"{BACKEND_URL}/auth/status", timeout=5)
        if res.status_code == 200:
            return res.json().get("authenticated", False)
    except:
        return False
    return False

def get_health():
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return {}

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = check_auth()

with st.sidebar:

    st.title("DriveRAG")

    st.divider()

    health_data = get_health()

    if health_data:
        st.success("System Online")
        st.info(f"{health_data.get('files_synced', 0)} Files Indexed")
    else:
        st.error("System Offline")

    st.divider()

    if st.session_state.authenticated:

        if st.button("Sync Google Drive"):

            with st.spinner("Syncing and indexing files..."):

                try:
                    res = requests.post(
                        f"{BACKEND_URL}/sync-drive",
                        timeout=TIMEOUT
                    )

                    if res.status_code == 200:

                        st.success("Sync complete!")

                        st.rerun()

                    else:

                        st.error(f"Sync failed: {res.text}")

                except Exception as e:

                    st.error(f"Error: {str(e)}")

        st.divider()

        st.caption("Authenticated with Google Drive")

    else:

        st.warning("Action Required: Connect Drive")


if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-container">
        <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">
            Welcome to DriveRAG
        </h1>
        <p style="color: #6B7280; font-size: 1.1rem;">
            Connect your Google Drive to build a private knowledge base.
            Search across your documents and get answers instantly.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        if st.button("Connect Google Drive"):

            try:

                res = requests.get(
                    f"{BACKEND_URL}/auth/url"
                )

                if res.status_code == 200:

                    url = res.json().get("url")

                    st.link_button(
                        "Confirm Connection with Google",
                        url
                    )

                    st.info(
                        "After connecting, refresh this page."
                    )

                else:

                    st.error(
                        "Could not fetch auth URL."
                    )

            except Exception as e:

                st.error(
                    f"Connection error: {str(e)}"
                )

else:

    st.title("Ask your Documents")

    st.markdown(
        "Search across all synced Google Drive files."
    )

    query = st.text_input(
        "Search Bar",
        placeholder="e.g. What are the main findings in the Q3 report?",
        label_visibility="collapsed"
    )

    if st.button("Search Knowledge Base"):

        if not query.strip():

            st.warning("Please enter a question.")

        else:

            with st.spinner("Analyzing documents..."):

                try:

                    res = requests.post(
                        f"{BACKEND_URL}/ask",
                        json={"query": query},
                        timeout=TIMEOUT
                    )

                    if res.status_code == 200:

                        result = res.json()

                        st.markdown(
                            f"""
                            <div class="answer-box">
                                {result.get('answer', 'No answer found.')}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        st.subheader("📚 Referenced Sources")

                        sources = result.get(
                            'sources',
                            []
                        )

                        if sources:

                            source_html = "".join(
                                [
                                    f'<span class="source-tag">📄 {s}</span>'
                                    for s in sources
                                ]
                            )

                            st.markdown(
                                source_html,
                                unsafe_allow_html=True
                            )

                        else:

                            st.caption(
                                "No specific documents were referenced."
                            )

                    else:

                        st.error(
                            f"Search failed: {res.text}"
                        )

                except Exception as e:

                    st.error(
                        f"Search error: {str(e)}"
                    )

st.divider()

st.markdown(
    "<center><p style='color:#9CA3AF;font-size:0.8rem;'>DriveRAG | Secure AI Knowledge Assistant</p></center>",
    unsafe_allow_html=True
)