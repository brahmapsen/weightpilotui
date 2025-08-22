# tabs/coach.py
from __future__ import annotations

import os
import json
import streamlit as st
from datetime import date, time
from typing import List, Dict, Any

# -----------------------------------------------------------------------------
# Sample directory of professionals (replace with your backend later)
# -----------------------------------------------------------------------------
def _seed_pros() -> List[Dict[str, Any]]:
    # Minimal, realistic sample set. Replace/augment from DB/API when ready.
    return [
        {
            "id": "rd_001",
            "name": "Dr. Maya Chen, RD, CNSC",
            "role": "Dietitian",
            "certifications": ["RD", "CNSC"],
            "specialties": ["Weight management", "Diabetes", "Clinical nutrition"],
            "location": {"city": "Boston", "state": "MA", "country": "USA"},
            "modalities": ["Virtual", "In-person"],
            "email": "maya.chen@example.com",
            "phone": "+1 (617) 555-0134",
            "bio": "Board-certified clinical dietitian with 10+ years in obesity & metabolic care. Practical, culturally-aware meal planning.",
            "rating": 4.9,
            "reviews": 178,
            "price_per_session": 120,
            "accepting_clients": True,
            "languages": ["English", "Mandarin"],
        },
        {
            "id": "pt_101",
            "name": "Alex Rivera, CSCS",
            "role": "Personal Trainer",
            "certifications": ["CSCS"],
            "specialties": ["Strength training", "Weight loss", "Mobility"],
            "location": {"city": "Austin", "state": "TX", "country": "USA"},
            "modalities": ["Virtual"],
            "email": "alex.rivera@example.com",
            "phone": "+1 (512) 555-0198",
            "bio": "Evidence-based programming with a focus on form, small habits, and sustainable fat loss.",
            "rating": 4.7,
            "reviews": 95,
            "price_per_session": 85,
            "accepting_clients": True,
            "languages": ["English", "Spanish"],
        },
        {
            "id": "rd_014",
            "name": "Priya Nair, MS, RD",
            "role": "Dietitian",
            "certifications": ["RD"],
            "specialties": ["Mediterranean diet", "Vegetarian/Vegan", "Gut health"],
            "location": {"city": "San Jose", "state": "CA", "country": "USA"},
            "modalities": ["Virtual"],
            "email": "priya.nair@example.com",
            "phone": "+1 (408) 555-0143",
            "bio": "Specializes in plant-forward, culturally familiar menus with macro consistency for weight care.",
            "rating": 4.8,
            "reviews": 123,
            "price_per_session": 110,
            "accepting_clients": False,
            "languages": ["English", "Hindi"],
        },
        {
            "id": "pt_221",
            "name": "Samir Haddad, NASM-CPT",
            "role": "Personal Trainer",
            "certifications": ["NASM-CPT"],
            "specialties": ["HIIT", "Cardio conditioning", "Beginner programs"],
            "location": {"city": "Seattle", "state": "WA", "country": "USA"},
            "modalities": ["In-person"],
            "email": "samir.haddad@example.com",
            "phone": "+1 (206) 555-0112",
            "bio": "Fun, accountability-first coaching. Progressive overload without burnout.",
            "rating": 4.6,
            "reviews": 64,
            "price_per_session": 75,
            "accepting_clients": True,
            "languages": ["English", "Arabic"],
        },
        {
            "id": "rd_045",
            "name": "Elena Rossi, RD",
            "role": "Dietitian",
            "certifications": ["RD"],
            "specialties": ["Weight management", "Hypertension", "Mediterranean diet"],
            "location": {"city": "Miami", "state": "FL", "country": "USA"},
            "modalities": ["Virtual", "In-person"],
            "email": "elena.rossi@example.com",
            "phone": "+1 (305) 555-0172",
            "bio": "Habit-centric approach: small changes, big outcomes. Fluent in Spanish & Italian.",
            "rating": 4.8,
            "reviews": 82,
            "price_per_session": 95,
            "accepting_clients": True,
            "languages": ["English", "Spanish", "Italian"],
        },
        {
            "id": "pt_333",
            "name": "Jordan Lee, CPT",
            "role": "Personal Trainer",
            "certifications": ["CPT"],
            "specialties": ["Functional training", "Posture", "Weight loss"],
            "location": {"city": "Chicago", "state": "IL", "country": "USA"},
            "modalities": ["Virtual"],
            "email": "jordan.lee@example.com",
            "phone": "+1 (773) 555-0150",
            "bio": "Remote-friendly coaching with flexible check-ins and weekly progress reviews.",
            "rating": 4.5,
            "reviews": 51,
            "price_per_session": 65,
            "accepting_clients": True,
            "languages": ["English", "Korean"],
        },
    ]


def _ensure_state():
    if "pros" not in st.session_state:
        st.session_state["pros"] = _seed_pros()
    if "coach_requests" not in st.session_state:
        st.session_state["coach_requests"] = []
    if "selected_pro_id" not in st.session_state:
        st.session_state["selected_pro_id"] = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _starbar(rating: float) -> str:
    full = int(round(rating))
    return "⭐" * full + f" ({rating:.1f})"

def _badge(text: str) -> str:
    return f"<span style='padding:2px 8px;border-radius:12px;background:#F3F4F6;font-size:12px;margin-right:6px;'>{text}</span>"

def _contact_row(icon: str, text: str) -> str:
    return f"<div style='margin:2px 0;'> {icon} {text}</div>"

def _match_filters(pro: Dict[str, Any], role: str, location_q: str, modalities: List[str],
                   specialties: List[str], accepting_only: bool) -> bool:
    if role != "All" and pro["role"] != role:
        return False
    if accepting_only and not pro.get("accepting_clients", False):
        return False
    if modalities:
        # require any overlap
        if not any(m in pro["modalities"] for m in modalities):
            return False
    if specialties:
        if not any(s in pro["specialties"] for s in specialties):
            return False
    if location_q:
        loc = pro["location"]
        hay = f"{loc.get('city','')} {loc.get('state','')} {loc.get('country','')}".lower()
        if location_q.lower() not in hay:
            return False
    return True


# -----------------------------------------------------------------------------
# Main Render
# -----------------------------------------------------------------------------
def render():
    _ensure_state()
    pros = st.session_state["pros"]

    st.header("👩‍⚕️ Connect with an Expert")
    st.caption("Browse certified **dietitians** and **personal trainers**, view profiles, and request a consultation.")

    # ---------------- Filters ----------------
    all_specialties = sorted({s for p in pros for s in p["specialties"]})
    colf1, colf2, colf3, colf4, colf5 = st.columns([1.2, 1.4, 1.2, 1.6, 1.0])
    with colf1:
        role = st.selectbox("Role", ["All", "Dietitian", "Personal Trainer"], index=0)
    with colf2:
        modalities = st.multiselect("Modality", ["Virtual", "In-person"], default=["Virtual"])
    with colf3:
        accepting_only = st.checkbox("Accepting clients", value=True)
    with colf4:
        specialties = st.multiselect("Specialties", all_specialties, default=["Weight management"])
    with colf5:
        location_q = st.text_input("Location contains", placeholder="city / state / country")

    filtered = [p for p in pros if _match_filters(p, role, location_q, modalities, specialties, accepting_only)]

    st.write(f"**Results:** {len(filtered)} professional(s)")

    # ---------------- Grid of cards ----------------
    # 2 columns grid
    grid_cols = st.columns(2)
    for idx, pro in enumerate(filtered):
        with grid_cols[idx % 2]:
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.markdown(f"### {pro['name']}")
                    st.markdown(
                        f"{_badge(pro['role'])} " +
                        " ".join(_badge(c) for c in pro["certifications"])
                        , unsafe_allow_html=True
                    )
                    st.write(_starbar(pro["rating"]), f"· {pro['reviews']} reviews")
                    st.write("**Specialties:**", ", ".join(pro["specialties"][:4]))
                    st.write("**Languages:**", ", ".join(pro.get("languages", [])))
                    st.caption(pro["bio"])
                with right:
                    st.write(f"**${pro['price_per_session']}** / session")
                    st.write("🗺️", f"{pro['location']['city']}, {pro['location']['state']}")
                    st.write("💻", " / ".join(pro["modalities"]))
                    if pro["accepting_clients"]:
                        st.success("Accepting")
                    else:
                        st.warning("Waitlist")

                # Contact + Profile details
                cta1, cta2 = st.columns([1, 1])
                with cta1:
                    if st.button(f"👋 Contact {pro['name'].split(',')[0]}", key=f"contact_{pro['id']}"):
                        st.session_state["selected_pro_id"] = pro["id"]
                        st.toast(f"Contacting {pro['name']}…", icon="✉️")
                with cta2:
                    with st.expander("View profile & contact info"):
                        st.markdown(
                            _contact_row("📧", f"{pro['email']}") +
                            _contact_row("📞", f"{pro['phone']}") +
                            _contact_row("📍", f"{pro['location']['city']}, {pro['location']['state']}, {pro['location']['country']}")
                            , unsafe_allow_html=True
                        )
                        st.markdown(
                            "**Certifications:** " + ", ".join(pro["certifications"]) + "  \n" +
                            "**Modalities:** " + ", ".join(pro["modalities"])
                        )

    st.divider()

    # ---------------- Contact / Request Form ----------------
    st.subheader("Request a consultation")
    sel_id = st.session_state.get("selected_pro_id")
    pro_options = {p["name"]: p["id"] for p in filtered} if filtered else {p["name"]: p["id"] for p in pros}
    default_idx = 0
    if sel_id:
        # try to pre-select
        name_list = list(pro_options.keys())
        try:
            default_idx = name_list.index(next(n for n, pid in pro_options.items() if pid == sel_id))
        except Exception:
            default_idx = 0

    colc1, colc2 = st.columns([2, 3])
    with colc1:
        pro_name = st.selectbox("Choose expert", list(pro_options.keys()), index=default_idx if pro_options else 0)
        contact_name = st.text_input("Your name", placeholder="Jane Doe")
        contact_email = st.text_input("Your email", placeholder="you@example.com")
        pref_date = st.date_input("Preferred date", value=date.today())
        pref_time = st.time_input("Preferred time", value=time(10, 0))
        modality_req = st.selectbox("Consultation mode", ["Virtual", "In-person"])
    with colc2:
        msg = st.text_area(
            "Message",
            placeholder="Briefly describe your goals, preferences, or questions…",
            height=160
        )
        attach_profile = st.checkbox("Attach my profile summary (helpful for diet planning)", value=True)
        send_btn = st.button("📨 Send request", use_container_width=True)

    if send_btn:
        if not contact_name.strip() or not contact_email.strip():
            st.error("Please provide your name and email.")
        else:
            pro_id = pro_options[pro_name]
            request_payload = {
                "pro_id": pro_id,
                "pro_name": pro_name,
                "contact_name": contact_name.strip(),
                "contact_email": contact_email.strip(),
                "preferred_datetime": f"{pref_date} {pref_time}",
                "message": msg.strip(),
                "modality": modality_req,
                "attach_profile": attach_profile,
            }
            # Store locally (for demo). Replace with POST to your backend when ready.
            st.session_state["coach_requests"].append(request_payload)

            # Optional future backend:
            # try:
            #     base = os.getenv("AGENT_API_URL", "http://localhost:8000").rstrip("/")
            #     r = requests.post(f"{base}/v1/coach/request", json=request_payload, timeout=15)
            #     r.raise_for_status()
            # except Exception as e:
            #     st.warning(f"Saved locally (backend not configured): {e}")

            st.success(f"Request sent to **{pro_name}**. You'll be contacted by email.")
            st.json(request_payload)

    # Simple history viewer (local demo only)
    if st.session_state["coach_requests"]:
        with st.expander("View my sent requests"):
            st.json(st.session_state["coach_requests"])
