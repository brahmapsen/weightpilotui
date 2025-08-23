# services/agent_api.py
import os, json
import requests
import streamlit as st

AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = int(os.getenv("UI_HTTP_TIMEOUT", "60"))
API_KEY = os.getenv("UI_API_KEY")  # optional

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    if API_KEY:
        s.headers["X-API-Key"] = API_KEY
    return s

def agent_url() -> str:
    return AGENT_API_URL

def ping_backend() -> bool:
    try:
        r = _session().get(f"{AGENT_API_URL}/health", timeout=10)
        return r.status_code == 200
    except Exception:
        return False

# -------- Profile helpers (read from session_state labels you used on Profile tab) --------
def build_profile_from_session() -> dict:
    ss = st.session_state
    # Fallbacks allow Action tab to still work if user hasn't visited Profile yet.
    age = int(ss.get("Age", 28))
    sex_ab = ss.get("Gender", "Male")
    height_cm = float(ss.get("Height (cm)", 170))
    weight_kg = float(ss.get("Weight (kg)", 72.0))
    gender_id = ss.get("Gender(optional)", None)
    race_eth = ss.get("Race/Ethnicity (optional)", None)
    activity = ss.get("Activity level", "Light")
    goal = (ss.get("Goal", "lose") or "lose").lower()
    goal_rate = ss.get("Intensity", "moderate")
    diet = ss.get("Diet pattern", "none")
    cuisines = ss.get("Cuisines you enjoy (for menu ideas)", ["American", "Indian"])
    allergies = ss.get("Allergies/intolerances", ["none"])
    medical_flags = ss.get("Medical considerations (informational only — consult your clinician)", ["none"])

    profile = {
        "age": age,
        "sex_assigned_at_birth": sex_ab,
        "gender_identity": gender_id or None,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "activity_level": activity,
        "goal": goal,
        "goal_rate": goal_rate,
        "diet": None if diet == "none" else diet,
        "allergies": [] if ("none" in allergies) else allergies,
        "medical_flags": [] if ("none" in medical_flags) else medical_flags,
        "cuisines": cuisines or [],
        "race_ethnicity": race_eth or None,
    }
    return profile

# -------- Backend calls --------
def generate_diet_plan(profile: dict) -> dict:
    r = _session().post(f"{AGENT_API_URL}/v1/plan", data=json.dumps(profile), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()  # {"targets": {...}, "plan_markdown": "..."}

def generate_exercise_plan(payload: dict) -> dict:
    # payload shape: {"profile": {...}, "preferences": {...}}
    r = _session().post(f"{AGENT_API_URL}/v1/exercise/plan", data=json.dumps(payload), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()  # {"plan_markdown": "..."}

def vapi_config():
    r = _session().get(f"{AGENT_API_URL}/v1/vapi/config", timeout=10)
    r.raise_for_status()
    return r.json()
