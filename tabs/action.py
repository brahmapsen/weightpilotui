# tabs/action.py
import os, json, time
import streamlit as st
from services.agent_api import (
    build_profile_from_session,
    generate_diet_plan,
    generate_exercise_plan,
    project_progress
)

from tabs.recipe import render_recipe_section

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

    # Slightly larger, readable font across this page
    st.markdown("""
    <style>
    /* Gentle size bump for readability */
    [data-testid="stAppViewContainer"] * { font-size: 1.05rem; }
    .stMarkdown h1 { font-size: 2.0rem !important; }
    .stMarkdown h2 { font-size: 1.6rem !important; }
    .stMarkdown h3 { font-size: 1.25rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    [data-testid="stMetricDelta"] { font-size: 0.95rem !important; }
    .trust-box { background:#0b1220; color:#e6edf3; border-radius:10px; padding:12px 14px; }

    /* 🔥 Make all button labels bold */
    .stButton > button { 
        font-weight: 900 !important;
    }

    /* Optional: also bold link-style buttons if you use them */
    .stLinkButton a, .stDownloadButton button {
        font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)


    st.header("⚡ Success Steps")

    # =========================
    # 🥗 Diet
    # =========================
    st.subheader("🥗 Diet")

    # Buttons on one line; results appear below (no left/right columns)
    bcol1, bcol2 = st.columns([1, 1], vertical_alignment="center")
    with bcol1:
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
    with bcol2:
        if st.button("🧹 Clear diet result", key="btn_diet_clear", use_container_width=True):
            st.session_state["diet_result"] = None
            try:
                os.remove(_cache_path("diet_result"))
            except Exception:
                pass

    # Diet results
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

        # ---- TRUST & PROOF ----
        trust = res.get("trust") or {}
        with st.expander("🔎 Why this plan works (Trust & Proof)", expanded=True):
            # Summary
            why = trust.get("why_summary")
            if why:
                st.markdown(f"**Summary:** {why}")

            # Personalization / assumptions / safety
            pers = trust.get("personalization") or []
            if pers:
                st.markdown("**Personalization choices**")
                st.write("• " + "\n• ".join(pers))

            assm = trust.get("assumptions") or []
            if assm:
                st.markdown("**Assumptions**")
                st.write("• " + "\n• ".join(assm))

            safety = trust.get("safety_checks") or []
            if safety:
                st.markdown("**Safety checks**")
                st.write("• " + "\n• ".join(safety))

            # Computation + provenance
            daily_math = trust.get("daily_math")
            if daily_math:
                st.markdown("**How we computed totals**")
                st.json(daily_math, expanded=False)

            prov = trust.get("provenance") or {}
            if prov:
                st.markdown("**Provenance**")
                st.json(prov, expanded=False)

            # Forecast chart (12-week)
            fc = trust.get("forecast") or []
            if fc:
                try:
                    import pandas as pd
                    df = pd.DataFrame(fc)
                    if {"date", "weight_kg"}.issubset(df.columns):
                        st.markdown("**12-week forecast**")
                        st.line_chart(
                            df.set_index("date")[["weight_kg"] + [c for c in ["p10", "p90"] if c in df.columns]],
                            height=240, use_container_width=True
                        )
                        st.caption("Band shows uncertainty if provided. Based on energy-balance approximation; individual results vary.")
                    else:
                        st.info("Forecast data missing required fields.")
                except Exception as e:
                    st.warning(f"Could not render forecast chart: {e}")

            # Citations
            cites = trust.get("citations") or []
            if cites:
                st.markdown("**Evidence & references**")
                for c in cites:
                    if isinstance(c, dict):
                        title = c.get("title") or "Source"
                        url = c.get("url")
                        st.markdown(f"- [{title}]({url})" if url else f"- {title}")
                    else:
                        st.markdown(f"- {str(c)}")
    else:
        st.info("No diet plan yet. Click **Generate** to create one.")

    st.divider()

    # =========================
    # Recipe
    # =========================
    render_recipe_section()
    st.divider()

    # =========================
    # 🏋️ Exercise
    # =========================
    st.subheader("🏋️ Exercise")

    exb1, exb2 = st.columns([1, 1])
    with exb1:
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
    with exb2:
        if st.button("🧹 Clear exercise result", key="btn_ex_clear", use_container_width=True):
            st.session_state["exercise_result"] = None
            try:
                os.remove(_cache_path("exercise_result"))
            except Exception:
                pass

    exres = st.session_state.get("exercise_result")
    if exres:
        st.markdown(exres.get("plan_markdown", "_No plan returned_"))
    else:
        st.info("No exercise regimen yet. Click **Generate** to create one.")


    st.divider()
    st.subheader("📈 Predicted progress (trust builder)")
    st.caption("A simple, transparent projection based on your daily calorie target and typical activity. It’s an estimate—real bodies vary.")

    # Pull targets from the last diet result if available
    last = st.session_state.get("diet_result") or {}
    targets = last.get("targets") or {}

    calorie_target = st.number_input(
        "Daily calorie target (kcal)",
        min_value=1000, max_value=5000,
        value=int(targets.get("calorie_target", 2000)),
        step=50
    )
    extra_burn = st.number_input(
        "Average extra exercise burn (kcal/day)",
        min_value=0, max_value=1500, value=200, step=50
    )
    weeks = st.slider("Projection length (weeks)", 4, 52, 26)

    if st.button("📈 **Compute projection**", use_container_width=True):
        profile = build_profile_from_session()
        with st.spinner("Simulating…"):
            try:
                proj = project_progress(
                    profile=profile,
                    calorie_target=calorie_target,
                    extra_burn_kcal_per_day=extra_burn,
                    weeks=weeks,
                )
                st.session_state["progress_projection"] = proj
                st.success("Projection ready ✅")
            except Exception as e:
                st.error(f"Projection failed: {e}")

    proj = st.session_state.get("progress_projection")
    if proj and proj.get("series"):
        import pandas as pd
        df = pd.DataFrame(proj["series"])
        st.line_chart(df.set_index("week")[["weight_kg"]])
        end_w = proj["assumptions"]["milestones"]["end_weight_kg"]
        start_w = proj["assumptions"]["start_weight_kg"]
        total_loss = round(start_w - end_w, 1)
        st.write(f"**Projected loss:** ~{total_loss} kg over {weeks} weeks (to ~{end_w} kg).")
        if proj.get("explanation_md"):
            st.markdown("#### Why this likely works")
            st.markdown(proj["explanation_md"])
    else:
        st.info("No projection yet. Enter a calorie target and click **Compute projection**.")

