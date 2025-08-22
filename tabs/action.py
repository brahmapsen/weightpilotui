# tabs/action.py
# tabs/action.py
import streamlit as st
import requests
from services.agent_api import call_plan_api

def _render_plan_output(result: dict):
    targets = result.get("targets", {})
    if targets:
        st.subheader("Daily targets (estimates)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("BMI", f"{targets.get('bmi', '–')}")
        m2.metric("BMR", f"{targets.get('bmr', '–')} kcal")
        m3.metric("TDEE", f"{targets.get('tdee', '–')} kcal")
        m4.metric("Calorie target", f"{targets.get('calorie_target', '–')} kcal")

    st.subheader("Recommended 7-day diet chart")
    st.markdown(result.get("plan_markdown", "_No plan returned_"))

def render():
    st.header("Sucess Map")

    # ---- Diet section ----
    st.subheader("Diet")
    st.caption("Generate a personalized 7-day plan based on your saved Profile.")
    col_btn, col_status = st.columns([1, 3])

    with col_btn:
        if st.button("✨ Generate my 7-day plan", use_container_width=True):
            profile = st.session_state.get("profile")
            consent = st.session_state.get("consent", True)

            if not consent:
                st.error("Please provide consent on the Profile tab first.")
            elif not profile:
                st.warning("No profile found. Please fill out the Profile tab.")
            else:
                with st.spinner("Contacting agent…"):
                    try:
                        result = call_plan_api(profile)
                        st.session_state["last_plan_result"] = result
                        st.success("Plan ready!")
                    except requests.HTTPError as e:
                        st.error(f"Agent error {e.response.status_code}: {e.response.text}")
                    except Exception as e:
                        st.error(f"Could not reach agent engine: {e}")

    with col_status:
        if "last_plan_result" in st.session_state:
            _render_plan_output(st.session_state["last_plan_result"])
        else:
            st.info("Your generated plan will appear here.")

    st.divider()

    # ---- Exercise section ----
    st.subheader("Exercise")
    st.info("Planned workouts, weekly activity targets, and movement nudges. (Coming soon)")

    st.divider()

    # ---- Sleep & Stress management section ----
    st.subheader("Sleep & Stress management")
    st.info("Bedtime routine, wind-down prompts, and stress-reduction practices. (Coming soon)")

