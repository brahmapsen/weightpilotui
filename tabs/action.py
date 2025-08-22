# tabs/action.py
import os, json, time
import streamlit as st
from services.agent_api import (
    build_profile_from_session,
    generate_diet_plan,
    generate_exercise_plan,
)

# -------- Simple local JSON cache --------
CACHE_DIR = os.path.expanduser(os.getenv("UI_CACHE_DIR", "~/.weightpilot_cache"))

def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(name: str) -> str:
    return os.path.join(CACHE_DIR, f"{name}.json")

def _save_cache(name: str, data: dict):
    _ensure_cache_dir()
    with open(_cache_path(name), "w", encoding="utf-8") as f:
        json.dump({"ts": time.time(), "data": data}, f, ensure_ascii=False, indent=2)

def _load_cache(name: str):
    try:
        with open(_cache_path(name), "r", encoding="utf-8") as f:
            return json.load(f).get("data")
    except Exception:
        return None

def _init_state_from_cache():
    if "diet_result" not in st.session_state:
        st.session_state["diet_result"] = _load_cache("diet_result")
    if "exercise_result" not in st.session_state:
        st.session_state["exercise_result"] = _load_cache("exercise_result")

# -------- UI --------
def render():
    _init_state_from_cache()

    st.header("⚡ Success Steps")

    # --- Diet section ---
    st.subheader("🥗 Diet")
    colA, colB = st.columns([1, 3])
    with colA:
        if st.button("✨ Generate my 7-day plan", key="btn_diet_generate", use_container_width=True):
            profile = build_profile_from_session()
            with st.spinner("Contacting diet agent…"):
                try:
                    result = generate_diet_plan(profile)
                    st.session_state["diet_result"] = result
                    _save_cache("diet_result", result)
                    st.success("Diet plan ready ✅")
                except Exception as e:
                    st.error(f"Failed to generate diet plan: {e}")

        if st.button("🧹 Clear diet result", key="btn_diet_clear", use_container_width=True):
            st.session_state["diet_result"] = None
            try:
                os.remove(_cache_path("diet_result"))
            except Exception:
                pass

    with colB:
        res = st.session_state.get("diet_result")
        if res:
            targets = res.get("targets") or {}
            if targets:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("BMI", f"{targets.get('bmi', '–')}")
                c2.metric("BMR", f"{targets.get('bmr', '–')} kcal")
                c3.metric("TDEE", f"{targets.get('tdee', '–')} kcal")
                c4.metric("Target", f"{targets.get('calorie_target', '–')} kcal")
            st.markdown(res.get("plan_markdown", "_No plan returned_"))
        else:
            st.info("No diet plan yet. Click **Generate** to create one.")

    st.divider()

    # --- Exercise section ---
    st.subheader("🏋️ Exercise")
    colX, colY = st.columns([1, 3])
    with colX:
        if st.button("🏃 Generate weekly regimen", key="btn_ex_generate", use_container_width=True):
            profile = build_profile_from_session()
            payload = {"profile": profile, "preferences": {}}
            with st.spinner("Contacting exercise agent…"):
                try:
                    result = generate_exercise_plan(payload)
                    st.session_state["exercise_result"] = result
                    _save_cache("exercise_result", result)
                    st.success("Exercise plan ready ✅")
                except Exception as e:
                    st.error(f"Failed to generate exercise plan: {e}")

        if st.button("🧹 Clear exercise result", key="btn_ex_clear", use_container_width=True):
            st.session_state["exercise_result"] = None
            try:
                os.remove(_cache_path("exercise_result"))
            except Exception:
                pass

    with colY:
        exres = st.session_state.get("exercise_result")
        if exres:
            st.markdown(exres.get("plan_markdown", "_No plan returned_"))
        else:
            st.info("No exercise regimen yet. Click **Generate** to create one.")
