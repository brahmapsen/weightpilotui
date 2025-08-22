# tabs/monitor.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ---------- helpers & defaults ----------

def _init_state():
    if "profile" not in st.session_state:
        st.session_state["profile"] = {}

    # Default exercise schedule (editable)
    if "exercise_schedule" not in st.session_state:
        st.session_state["exercise_schedule"] = pd.DataFrame([
            {"Day": "Mon", "Time": "07:00", "Activity": "Brisk Walk", "Duration (min)": 30, "Intensity": "Light"},
            {"Day": "Tue", "Time": "18:00", "Activity": "Strength (Upper)", "Duration (min)": 35, "Intensity": "Moderate"},
            {"Day": "Wed", "Time": "07:00", "Activity": "Cycling", "Duration (min)": 30, "Intensity": "Moderate"},
            {"Day": "Thu", "Time": "18:00", "Activity": "Strength (Lower)", "Duration (min)": 35, "Intensity": "Moderate"},
            {"Day": "Fri", "Time": "07:00", "Activity": "Jog/Run", "Duration (min)": 25, "Intensity": "Vigorous"},
            {"Day": "Sat", "Time": "09:00", "Activity": "Yoga / Mobility", "Duration (min)": 30, "Intensity": "Light"},
            {"Day": "Sun", "Time": "—", "Activity": "Rest / Steps 6–8k", "Duration (min)": 0, "Intensity": "—"},
        ])

    # Default events / alerts
    if "events" not in st.session_state:
        today = date.today()
        st.session_state["events"] = pd.DataFrame([
            {"Date": today, "Title": "Meal prep (week)", "Category": "Diet"},
            {"Date": today + timedelta(days=1), "Title": "Evening workout", "Category": "Exercise"},
            {"Date": today + timedelta(days=3), "Title": "Weigh-in", "Category": "Progress"},
        ])

    # Weight history (weekly). You can add real logs later.
    if "weights" not in st.session_state:
        prof = st.session_state.get("profile", {})
        current = float(prof.get("weight_kg") or 72.0)
        # Make a short synthetic 6-week history (slight drift)
        base = [current + d for d in [2.0, 1.3, 0.8, 0.3, -0.1, 0.0]]
        start = date.today() - timedelta(weeks=len(base) - 1)
        st.session_state["weights"] = pd.DataFrame({
            "Date": [start + timedelta(weeks=i) for i in range(len(base))],
            "Weight_kg": base,
        })

    # Progress targets
    if "start_weight_kg" not in st.session_state:
        # first weight in series
        st.session_state["start_weight_kg"] = float(st.session_state["weights"]["Weight_kg"].iloc[0])
    if "target_weight_kg" not in st.session_state:
        prof = st.session_state.get("profile", {})
        goal = str(prof.get("goal") or "maintain").lower()
        start_w = float(st.session_state["start_weight_kg"])
        if goal == "lose":
            st.session_state["target_weight_kg"] = max(35.0, start_w * 0.93)  # ~7% cut default
        elif goal == "gain":
            st.session_state["target_weight_kg"] = min(250.0, start_w * 1.05) # ~5% gain default
        else:
            st.session_state["target_weight_kg"] = start_w

def _progress_percent(start_w: float, current_w: float, target_w: float) -> float:
    # Handle lose / gain / maintain generically
    if target_w == start_w:
        # Maintain: within ±1 kg = 100%
        delta = abs(current_w - start_w)
        return 1.0 if delta <= 1.0 else max(0.0, 1.0 - (delta - 1.0) / 4.0)  # soft falloff
    # Move from start toward target
    total = abs(target_w - start_w)
    done = total - abs(target_w - current_w)
    pct = 0.0 if total == 0 else max(0.0, min(1.0, done / total))
    return pct

# ---------- renderers ----------

def _section_schedule():
    st.subheader("Scheduling")
    st.caption("Your current weekly **exercise schedule**. Edit cells and click **Save**.")

    edited = st.data_editor(
        st.session_state["exercise_schedule"],
        num_rows="dynamic",
        use_container_width=True,
        key="exercise_editor",
    )
    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("💾 Save schedule"):
            st.session_state["exercise_schedule"] = pd.DataFrame(edited)
            st.success("Schedule saved.")
    with cols[1]:
        st.info("Tip: Add rows for classes, team sports, or active commute.")

def _section_alerts():
    import pandas as pd
    from datetime import date, timedelta

    st.subheader("Alerts & Notifications")
    st.caption("Simple **Calendar of Events**. Add reminders for weigh-ins, workouts, meal prep, etc.")

    # --- Filters (these are datetime.date) ---
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        start_d = st.date_input("From", value=date.today() - timedelta(days=7))
    with c2:
        end_d = st.date_input("To", value=date.today() + timedelta(days=21))
    with c3:
        cat = st.selectbox("Category filter", ["All", "Diet", "Exercise", "Progress", "Other"], index=0)

    # --- Normalize ALL dates to pandas Timestamp (midnight) ---
    df = st.session_state["events"].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()

    start_ts = pd.to_datetime(start_d).normalize()
    end_ts   = pd.to_datetime(end_d).normalize()

    # --- Apply filters safely ---
    mask = (df["Date"] >= start_ts) & (df["Date"] <= end_ts)
    if cat != "All":
        mask = mask & (df["Category"] == cat)

    st.dataframe(
        df.loc[mask].sort_values("Date"),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**Add an event**")
    a1, a2, a3, a4 = st.columns([2, 4, 2, 1])
    with a1:
        ev_date_d = st.date_input("Date", value=date.today(), key="new_ev_date")
    with a2:
        ev_title = st.text_input("Title", placeholder="e.g., Meal prep", key="new_ev_title")
    with a3:
        ev_cat = st.selectbox("Category", ["Diet", "Exercise", "Progress", "Other"], key="new_ev_cat")
    with a4:
        st.write("")  # spacer
        if st.button("➕ Add"):
            if ev_title.strip():
                new_row = {
                    "Date": pd.to_datetime(ev_date_d).normalize(),
                    "Title": ev_title.strip(),
                    "Category": ev_cat,
                }
                st.session_state["events"] = pd.concat(
                    [st.session_state["events"], pd.DataFrame([new_row])],
                    ignore_index=True,
                )
                st.success("Event added.")
            else:
                st.warning("Please enter a title.")

def _section_progress():
    st.subheader("Progress Indicators")

    # Targets editor
    p = st.session_state.get("profile", {})
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state["start_weight_kg"] = st.number_input(
            "Start weight (kg)",
            value=float(st.session_state["start_weight_kg"]),
            min_value=35.0, max_value=250.0, step=0.1,
        )
    with c2:
        current = float(st.session_state["weights"]["Weight_kg"].iloc[-1])
        st.metric("Current weight (kg)", f"{current:.1f}")
    with c3:
        st.session_state["target_weight_kg"] = st.number_input(
            "Target weight (kg)",
            value=float(st.session_state["target_weight_kg"]),
            min_value=35.0, max_value=250.0, step=0.1,
        )

    start_w = float(st.session_state["start_weight_kg"])
    target_w = float(st.session_state["target_weight_kg"])
    pct = _progress_percent(start_w, current, target_w)

    st.write("**Overall progress toward target**")
    st.progress(pct, text=f"{int(pct*100)}% complete")

    st.divider()
    st.write("**Weekly weight trend**")
    # Log a new weight
    lw1, lw2, lw3 = st.columns([2, 2, 1])
    with lw1:
        log_date = st.date_input("Log date", value=date.today(), key="log_date")
    with lw2:
        log_w = st.number_input("Weight (kg)", min_value=35.0, max_value=250.0, step=0.1, key="log_weight")
    with lw3:
        st.write("")
        if st.button("📈 Add weight"):
            df = st.session_state["weights"]
            new = pd.DataFrame([{"Date": log_date, "Weight_kg": float(log_w)}])
            st.session_state["weights"] = (
                pd.concat([df, new], ignore_index=True)
                .drop_duplicates(subset=["Date"], keep="last")
                .sort_values("Date")
            )
            st.success("Weight logged.")

    # Show last 8 weeks
    dfw = st.session_state["weights"].copy()
    dfw["Date"] = pd.to_datetime(dfw["Date"])
    cutoff = pd.Timestamp(date.today() - timedelta(weeks=8))
    dfw = dfw[dfw["Date"] >= cutoff]
    dfw = dfw.set_index("Date")

    st.line_chart(dfw["Weight_kg"], use_container_width=True)
    st.caption("Tip: weigh at the same time of day (e.g., morning, after bathroom, before breakfast).")

# ---------- public entry ----------

def render():
    _init_state()
    st.header("Progress monitoring and Feedback")

    _section_schedule()
    st.divider()

    _section_alerts()
    st.divider()

    _section_progress()
