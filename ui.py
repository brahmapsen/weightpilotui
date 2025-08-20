# streamlit_app.py
import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---- Config ----
AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")  # e.g., FastAPI base
API_KEY = os.getenv("UI_API_KEY")  # optional if your backend requires it
TIMEOUT = int(os.getenv("UI_HTTP_TIMEOUT", "60"))

def call_backend_plan(profile: dict) -> dict:
    """POST profile -> {targets: {...}, plan_markdown: "..."}"""
    url = f"{AGENT_API_URL.rstrip('/')}/v1/plan"
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    r = requests.post(url, headers=headers, data=json.dumps(profile), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def ping_backend() -> bool:
    try:
        r = requests.get(f"{AGENT_API_URL.rstrip('/')}/health", timeout=10)
        return r.status_code == 200
    except Exception:
        return False

# ---- UI ----
st.set_page_config(page_title="WeightPilot AI", page_icon="🧭", layout="wide")
st.title("🧭 WeightPilot AI")
st.caption("Personalized Diet & Weight Care — demo UI calls your FastAPI backend.")

with st.sidebar:
    st.subheader("Backend")
    st.text_input("Backend URL", value=AGENT_API_URL, key="agent_api_url_help", disabled=True)
    online = ping_backend()
    st.metric("Backend status", "Online" if online else "Offline")

with st.expander("Privacy & Consent", expanded=True):
    st.markdown(
        "- Data you enter here is sent to **your backend** to generate a plan.\n"
        "- Race/ethnicity is optional and used only for culturally relevant menu ideas."
    )
    consent = st.checkbox("I understand and consent to proceed.", value=True)

st.header("1) Your basics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    age = st.number_input("Age", min_value=13, max_value=100, value=28, step=1)
with col2:
    sex_ab = st.selectbox("Sex assigned at birth", ["Female", "Male"])
with col3:
    height_cm = st.number_input("Height (cm)", min_value=120, max_value=230, value=170)
with col4:
    weight_kg = st.number_input("Weight (kg)", min_value=35.0, max_value=250.0, value=72.0, step=0.1)

col5, col6, col7 = st.columns(3)
with col5:
    gender_id = st.text_input("Gender identity (optional)", placeholder="e.g., woman, man, non-binary")
with col6:
    race_eth = st.text_input("Race/Ethnicity (optional)", placeholder="Optional")
with col7:
    activity = st.selectbox(
        "Activity level",
        ["Sedentary", "Light", "Moderate", "Active", "Very Active"],
        index=1,
    )

st.header("2) Goals & preferences")
col8, col9, col10 = st.columns(3)
with col8:
    goal = st.selectbox("Goal", ["Maintain", "Lose", "Gain"], index=1).lower()
with col9:
    goal_rate = st.selectbox("Intensity", ["gentle", "moderate", "aggressive"], index=1)
with col10:
    diet = st.selectbox(
        "Diet pattern",
        ["none", "vegetarian", "vegan", "pescatarian", "mediterranean", "low-carb", "high-protein"],
        index=0,
    )

cuisines = st.multiselect(
    "Cultural cuisines you enjoy (for menu ideas)",
    ["American", "Indian", "Mexican", "Chinese", "Japanese", "Middle Eastern", "Mediterranean", "Ethiopian", "Italian", "Other"],
    default=["American", "Indian"],
)
allergies = st.multiselect(
    "Allergies/intolerances",
    ["none", "peanut", "tree nut", "gluten", "dairy", "egg", "shellfish", "soy", "sesame"],
    default=["none"],
)
medical_flags = st.multiselect(
    "Medical considerations (informational only — consult your clinician)",
    ["none", "diabetes", "hypertension", "kidney disease", "pregnancy/breastfeeding"],
    default=["none"],
)

st.divider()
if st.button("✨ Generate my 7-day plan", use_container_width=True, disabled=not consent):
    profile = {
        "age": int(age),
        "sex_assigned_at_birth": sex_ab,
        "gender_identity": gender_id or None,
        "height_cm": float(height_cm),
        "weight_kg": float(weight_kg),
        "activity_level": activity,
        "goal": goal,
        "goal_rate": goal_rate,
        "diet": None if diet == "none" else diet,
        "allergies": [] if "none" in allergies else allergies,
        "medical_flags": [] if "none" in medical_flags else medical_flags,
        "cuisines": cuisines,
        "race_ethnicity": race_eth or None,
    }

    with st.spinner("Contacting backend..."):
        try:
            result = call_backend_plan(profile)
        except requests.HTTPError as e:
            st.error(f"Backend error: {e}\n\n{getattr(e.response, 'text', '')}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")
        else:
            st.success("Plan ready!")
            if "targets" in result:
                t = result["targets"]
                st.subheader("Daily targets (estimates)")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("BMI", f"{t.get('bmi', '?')}")
                c2.metric("BMR", f"{t.get('bmr', '?')} kcal")
                c3.metric("TDEE", f"{t.get('tdee', '?')} kcal")
                c4.metric("Calorie target", f"{t.get('calorie_target', '?')} kcal")

            st.subheader("Recommended 7-day diet chart")
            st.markdown(result.get("plan_markdown", "_No plan returned_"))

st.divider()
with st.expander("Setup tips"):
    st.code(
        "pip install streamlit python-dotenv requests\n\n"
        "# .env\n"
        "AGENT_API_URL=http://localhost:8000\n"
        "# UI_API_KEY=optional-if-your-backend-requires-a-key\n"
        "# UI_HTTP_TIMEOUT=60\n",
        language="bash",
    )

st.caption(
    "Disclaimer: Educational only. Not a substitute for professional medical advice. "
    "Consult a clinician before changing your diet."
)
