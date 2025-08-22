# tabs/profile.py
import streamlit as st

def render():
    with st.expander("Privacy & Consent", expanded=True):
        st.markdown(
            "- Race/ethnicity is optional and used only for culturally familiar menu ideas."
        )
        consent = st.checkbox("I understand and consent to proceed.", value=True)
        st.session_state["consent"] = consent

    st.header("Basic Profile")
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        age = st.number_input("Age", min_value=13, max_value=100, value=28, step=1)
    with c2:
        sex_ab = st.selectbox("Gender", ["Female", "Male"])
    with c3:
        height_cm = st.number_input("Height (cm)", min_value=120, max_value=230, value=170)
    with c4:
        weight_kg = st.number_input("Weight (kg)", min_value=35.0, max_value=250.0, value=72.0, step=0.1)
    with c5:
        gender_id = st.text_input("Gender(optional)", placeholder="e.g., woman, man, non-binary")
    with c6:
        race_eth = st.text_input("Race/Ethnicity (optional)", placeholder="Optional")
    with c7:
        activity = st.selectbox(
            "Activity level",
            ["Sedentary", "Light", "Moderate", "Active", "Very Active"],
            index=1,
        )

    st.header("Goals & preferences")
    g1, g2, g3 = st.columns(3)
    with g1:
        goal = st.selectbox("Goal", ["Maintain", "Lose", "Gain"], index=1).lower()
    with g2:
        goal_rate = st.selectbox("Intensity", ["gentle", "moderate", "aggressive"], index=1)
    with g3:
        diet = st.selectbox(
            "Diet pattern",
            ["none", "vegetarian", "vegan", "pescatarian", "mediterranean", "low-carb", "high-protein"],
            index=0,
        )

    cuisines = st.multiselect(
        "Cuisines you enjoy (for menu ideas)",
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

    # Auto-save the profile in session so Action tab can use it
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
    st.session_state["profile"] = profile

    st.info("Your profile is saved automatically. Use the **Action → Diet** tab to generate your plan.")

    st.divider()
    st.caption(
        "Disclaimer: Prototype only. Not medical advice. Consult a clinician before changing your diet."
    )
