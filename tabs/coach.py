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
            "location": {"city": "Washington DC", "state": "DC", "country": "USA"},
            "modalities": ["Virtual", "In-person"],
            "email": "maya.chen@example.com",
            "phone": "+1 (617) 555-0134",
            "bio": "Board-certified clinical dietitian with 10+ years in obesity & metabolic care. Practical, culturally-aware meal planning.",
            "rating": 4.9,
            "reviews": 178,
            "price_per_session": 120,
            "accepting_clients": True,
            "languages": ["English", "Spanish"],
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
    with colc2:
        send_btn = st.button("📨 Send request", use_container_width=True)

    if send_btn:
        from services.agent_api import AGENT_API_URL
        # try:
        #     vapi_page = f"{AGENT_API_URL}/vapi/widget"
        #     st.info("Open the voice assistant in a new tab to start your call.")
        #     st.link_button("🎙️ Open Voice Call", vapi_page)
        # except Exception as e:
        #     st.error(f"Vapi not configured: {e}")
        #     return
        from services.agent_api import vapi_config

        # Use env directly; no backend dependency
        cfg = vapi_config()            # <-- call it
        vapi_pk  = cfg["public_key"]   # not vapi_config.public_key
        vapi_aid = cfg["assistant_id"]
        if not (vapi_pk and vapi_aid):
            st.error("VAPI_PUBLIC_KEY or VAPI_ASSISTANT_ID not set in environment.")
            return

        # Use Vapi's browser widget bundle (works without bundlers)
        # Docs: https://vapi.ai/docs/examples/voice-widget-example
        # sdk_src = "https://cdn.jsdelivr.net/gh/VapiAI/html-script-tag@latest/dist/assets/index.js"

        # Full-page fallback target (no sandbox; avoids worklet/worker issues in Streamlit iframe)
        fallback_url = f"{AGENT_API_URL}/vapi/widget?assistantId={vapi_aid}&publicKey={vapi_pk}"

        html = f"""
        <div style="font-family:system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;">
          <h3>Vapi Voice Assistant</h3>
          <div style="font-size:12px;color:#6B7280;margin:-6px 0 10px;">
            Assistant: <code>{vapi_aid[:8]}…</code> · Key: <code>{vapi_pk[:4]}…</code>
          </div>

          <div style="display:flex;gap:8px;margin-bottom:8px;">
            <button id="vapi-start" style="padding:6px 12px;">Start Call</button>
            <button id="vapi-stop"  style="padding:6px 12px;" disabled>End Call</button>
            <button id="vapi-open"  style="padding:6px 12px;">Open full-page</button>
          </div>

          <div style="background:#0B1220;border-radius:8px;padding:10px;">
            <pre id="vapi-log" style="margin:0;color:#E5E7EB;white-space:pre-wrap;max-height:240px;overflow:auto;">
Status / Logs:</pre>
          </div>
        </div>

        <!-- Improve load reliability -->
        <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
        <link rel="preconnect" href="https://c.daily.co" crossorigin>
        <link rel="dns-prefetch" href="https://cdn.jsdelivr.net">
        <link rel="dns-prefetch" href="https://c.daily.co">

        <script>
          const sdkUrl = "https://cdn.jsdelivr.net/gh/VapiAI/html-script-tag@latest/dist/assets/index.js";
          const assistantId = "{vapi_aid}";
          const publicKey   = "{vapi_pk}";
          const fallbackUrl = "{fallback_url}";

          const logEl   = document.getElementById('vapi-log');
          const startBt = document.getElementById('vapi-start');
          const stopBt  = document.getElementById('vapi-stop');
          const openBt  = document.getElementById('vapi-open');

          function log(s) {{
            logEl.textContent += "\\n" + s;
            logEl.scrollTop = logEl.scrollHeight;
          }}

          function loadScript(url) {{
            return new Promise((resolve, reject) => {{
              const s = document.createElement('script');
              s.src = url; s.async = true; s.defer = true;
              s.onload = resolve;
              s.onerror = (e)=>reject(new Error('Failed loading Vapi SDK: ' + e.type));
              document.head.appendChild(s);
            }});
          }}

          let vapi = null;

          async function getVapi() {{
            if (vapi) return vapi;
            await loadScript(sdkUrl).catch(e => {{ log(e.message); throw e; }});
            if (!window.vapiSDK || !window.vapiSDK.run) {{
              log("Vapi SDK not available on window (CSP/adblock?).");
              throw new Error("Vapi SDK missing");
            }}
            log("Loaded SDK: " + sdkUrl);

            vapi = window.vapiSDK.run({{
              apiKey: publicKey,
              assistant: assistantId,
              config: {{
                open: false,
                position: "bottom-right",
                theme: "light",
                showSettings: false
              }}
            }});

            vapi.on?.("error", (e) => log("error: " + (e?.message || e)));
            vapi.on?.("call-start", () => {{
              log("call-start");
              startBt.disabled = true; stopBt.disabled = false;
            }});
            vapi.on?.("call-end", () => {{
              log("call-end");
              startBt.disabled = false; stopBt.disabled = true;
            }});

            return vapi;
          }}

          function looksLikeDailyWorkerError(msg) {{
            // Heuristic: the Daily call-machine worker/worklet failed inside a sandbox/Firefox
            return /call-machine|daily\\.co|worklet|worker|bundle/i.test(String(msg||""));
          }}

          startBt.addEventListener('click', async () => {{
            try {{
              const inst = await getVapi();
              if (typeof inst.start === 'function') {{
                await inst.start(assistantId);
              }} else {{
                inst.open?.();
                log("Widget opened; press the mic to start.");
              }}
            }} catch (e) {{
              const m = e?.message || e;
              log("start error: " + m);
              if (looksLikeDailyWorkerError(m)) {{
                log("Opening full-page call to avoid iframe sandbox limitations…");
                window.open(fallbackUrl, "_blank", "noopener,noreferrer");
              }}
            }}
          }});

          stopBt.addEventListener('click', async () => {{
            try {{
              if (vapi && typeof vapi.stop === 'function') await vapi.stop();
              else vapi?.close?.();
            }} catch (e) {{
              log("stop error: " + (e?.message || e));
            }}
          }});

          openBt.addEventListener('click', () => {{
            window.open(fallbackUrl, "_blank", "noopener,noreferrer");
          }});

          // Helpful diagnostics
          log("Secure context: " + (window.isSecureContext ? "yes" : "no"));
          log("Browser: " + navigator.userAgent);
        </script>
        """

        st.components.v1.html(html, height=360, scrolling=True)
        st.success(f"Request prepared for **{pro_name}**. Use the Start/End buttons above.")

        # st.success(f"Request sent to **{pro_name}**. You'll be contacted by email.")
        # st.json(request_payload)

    # Simple history viewer (local demo only)
    if st.session_state["coach_requests"]:
        with st.expander("View my sent requests"):
            st.json(st.session_state["coach_requests"])
