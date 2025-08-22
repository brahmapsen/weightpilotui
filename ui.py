# ui.py
import os
from dotenv import load_dotenv
import streamlit as st

# from services.agent_api import agent_url, ping_backend
from tabs import profile, action, monitor, coach

load_dotenv()

LOGO_PATH = os.getenv("UI_LOGO_PATH")  # e.g., "./weightpilot_logo.png"

# -----------------------------
# Page shell
# -----------------------------
st.set_page_config(page_title="WeightPilot AI", page_icon="🧭", layout="wide")

top_left, top_mid = st.columns([1, 4])
with top_left:
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, caption=None, use_column_width=True)

with top_mid:
    st.title("🧭 Personalized Weight Management")

# with st.sidebar:
#     st.subheader("Agent")
#     st.write(f"**URL:** {agent_url()}")
#     st.metric("Status", "Online ✅" if ping_backend() else "Offline ❌")

# Tab styling
st.markdown("""
<style>
/* Make tab labels bold (works across recent Streamlit versions) */
.stTabs [role="tablist"] button div[data-testid="stMarkdownContainer"] p {
    font-weight: 700 !important;
}
/* Fallback: also bold the tab button text */
.stTabs [role="tablist"] button {
    font-weight: 700 !important;
}
/* Optional: bump size a bit */
.stTabs [role="tablist"] button p {
    font-size: 1.0rem !important;  /* try 1.05–1.1 if you want larger */
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Profile", "Action", "Monitor", "Coach"])

with tab1:
    profile.render()

with tab2:
    action.render()

with tab3:
    monitor.render()

with tab4:
    coach.render()
