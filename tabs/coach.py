# tabs/coach.py
from __future__ import annotations

import os
import time
import streamlit as st
from typing import List, Dict, Any, Optional

# ---- UI → backend calls ----
from services.agent_api import find_local_pros, AGENT_API_URL, vapi_config

# -----------------------------------------------------------------------------
# Fallback seed (used only if backend search returns nothing / errors)
# -----------------------------------------------------------------------------
def _seed_pros() -> List[Dict[str, Any]]:
    return [
        {
            "id": "rd_001",
            "name": "Dr. Maya Chen, RD, CNSC",
            "role": "Dietitian",
            "rating": 4.9,
            "reviews": 178,
            "address": "Washington, DC, USA",
            "phone": "+1 (617) 555-0134",
            "website": None,
            "link": None,
            "price_per_session": 120,
            "snippet": "Board-certified clinical dietitian with 10+ years in obesity & metabolic care.",
        },
    ]

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
def _ensure_state():
    st.session_state.setdefault("coach_search_results", [])   # latest backend results
    st.session_state.setdefault("pros_seed", _seed_pros())    # local fallback list
    st.session_state.setdefault("selected_pro_id", None)      # last selected card
    st.session_state.setdefault("coach_requests", [])         # local “sent” history

# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------
def _starbar(rating: Optional[float]) -> str:
    if rating is None:
        return "⭐ N/A"
    full = int(round(rating))
    return "⭐" * min(max(full, 0), 5) + f" ({rating:.1f})"

def _card(pro: Dict[str, Any], idx: int):
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.markdown(f"### {pro.get('name','(unknown)')}")
            meta_bits = []
            if pro.get("role"):
                meta_bits.append(f"**{pro['role']}**")
            if pro.get("rating") is not None:
                meta_bits.append(f"{_starbar(pro['rating'])}")
            if pro.get("reviews"):
                meta_bits.append(f"{pro['reviews']} reviews")
            if meta_bits:
                st.write(" · ".join(meta_bits))
            if pro.get("address"):
                st.write(pro["address"])
            if pro.get("distance_km") is not None:
                st.caption(f"~{pro['distance_km']:.1f} km away")
            if pro.get("snippet"):
                st.caption(pro["snippet"])

        with right:
            if pro.get("price_per_session"):
                st.write(f"**${pro['price_per_session']}** / session")

        c1, c2, c3 = st.columns(3)
        with c1:
            if pro.get("phone"):
                st.link_button("📞 Call", f"tel:{pro['phone']}", use_container_width=True)
        with c2:
            if pro.get("website"):
                st.link_button("🌐 Website", pro["website"], use_container_width=True)
            elif pro.get("link"):
                st.link_button("🌐 Map", pro["link"], use_container_width=True)
        with c3:
            if st.button("👋 Contact", key=f"contact_{idx}", use_container_width=True):
                st.session_state["selected_pro_id"] = pro.get("id") or pro.get("link") or f"idx_{idx}"
                st.toast(f"Selected: {pro.get('name','(unknown)')}", icon="✉️")

# -----------------------------------------------------------------------------
# Main Render
# -----------------------------------------------------------------------------
def render():
    _ensure_state()

    st.header("👩‍⚕️ Connect with an Expert")
    st.caption("Search **dietitians**, **nutritionists**, and **health coaches** near you, then request a consultation.")

    # ---------------- Search form (calls backend) ----------------
    with st.form("coach_search_form", clear_on_submit=False):
        col1, col2, col3, col4 = st.columns([1.2, 1.0, 1.0, 1.0])
        with col1:
            zip_code = st.text_input("ZIP Code", placeholder="e.g., 94105")
        with col2:
            city = st.text_input("City (optional)", placeholder="e.g., San Francisco")
        with col3:
            state = st.text_input("State (optional)", placeholder="e.g., CA")
        with col4:
            radius_km = st.number_input("Radius (km)", min_value=2, max_value=80, value=20, step=2)

        roles = st.multiselect(
            "Profession Types",
            ["Dietitian", "Nutritionist", "Health Coach"],
            default=["Dietitian", "Health Coach"],
        )
        max_results = st.slider("Max results", min_value=3, max_value=6, value=4, step=1)

        submitted = st.form_submit_button("🔎 **Search Nearby**", use_container_width=True)
        if submitted:
            if not zip_code and not (city and state):
                st.error("Please provide either a ZIP Code, or City + State.")
            else:
                with st.spinner("Searching professionals…"):
                    try:
                        items = find_local_pros(
                            zip_code=zip_code.strip() or None,
                            city=city.strip() or None,
                            state=state.strip() or None,
                            roles=roles,
                            radius_km=int(radius_km),
                            max_results=int(max_results),
                        )
                        st.session_state["coach_search_results"] = items or []
                        if items:
                            st.success(f"Found {len(items)} professional(s).")
                        else:
                            st.info("No matches from the search API. Showing local examples.")
                    except Exception as e:
                        st.session_state["coach_search_results"] = []
                        st.error(f"Search failed: {e}")

    # ---------------- Results grid ----------------
    results: List[Dict[str, Any]] = st.session_state.get("coach_search_results") or []
    if results:
        st.write(f"**Results:** {len(results)}")
        grid_cols = st.columns(2)
        for i, pro in enumerate(results):
            with grid_cols[i % 2]:
                _card(pro, i)
    else:
        # Fallback to seed if nothing fetched yet / error
        st.info("No results yet. Enter your location and click **Search Nearby**. Showing sample experts meanwhile:")
        seed = st.session_state["pros_seed"]
        grid_cols = st.columns(2)
        for i, pro in enumerate(seed):
            with grid_cols[i % 2]:
                _card(pro, i)

    st.divider()

    # ---------------- Request a Consultation (kept from your code) ----------------
    st.subheader("Request a consultation")

    # Build options from current results; fallback to seed
    source_list = results if results else st.session_state["pros_seed"]
    name_to_id = { (p.get("name") or f"Pro {i}"): (p.get("id") or p.get("link") or f"idx_{i}") for i, p in enumerate(source_list) }
    names = list(name_to_id.keys())

    # Preselect if user clicked a “Contact” button above
    sel_id = st.session_state.get("selected_pro_id")
    default_idx = 0
    if sel_id:
        try:
            selected_name = next(n for n, pid in name_to_id.items() if pid == sel_id)
            default_idx = names.index(selected_name)
        except Exception:
            default_idx = 0

    colc1, colc2 = st.columns([2, 3])
    with colc1:
        pro_name = st.selectbox("Choose expert", names, index=default_idx if names else 0)
    with colc2:
        send_btn = st.button("📨 **Send request**", use_container_width=True)

    if send_btn:
        # Save a local “request” record (demo)
        st.session_state["coach_requests"].append({
            "when": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pro_name": pro_name,
            "pro_id": name_to_id.get(pro_name),
        })

        # Voice call widget (same flow you had; uses env via services.agent_api.vapi_config)
        try:
            cfg = vapi_config()
            vapi_pk  = cfg.get("public_key")
            vapi_aid = cfg.get("assistant_id")
        except Exception as e:
            vapi_pk = vapi_aid = None
            st.warning(f"Vapi not configured: {e}")

        if vapi_pk and vapi_aid:
            fallback_url = f"{AGENT_API_URL}/vapi/widget?assistantId={vapi_aid}&publicKey={vapi_pk}"

            html = f"""
            <div style="font-family:system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;">
              <h4>Vapi Voice Assistant</h4>
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

              log("Secure context: " + (window.isSecureContext ? "yes" : "no"));
              log("Browser: " + navigator.userAgent);
            </script>
            """
            st.components.v1.html(html, height=360, scrolling=True)
            st.success(f"Request prepared for **{pro_name}**. Use Start/End to talk.")

        else:
            st.success(f"Request sent for **{pro_name}**.")
            st.caption("Voice widget not configured (set VAPI_PUBLIC_KEY and VAPI_ASSISTANT_ID).")

    # Simple history viewer (local demo only)
    if st.session_state["coach_requests"]:
        with st.expander("View my sent requests"):
            st.json(st.session_state["coach_requests"])
