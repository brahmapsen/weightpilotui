# tabs/sections/recipe_section.py
from __future__ import annotations

import base64
from io import BytesIO
from typing import List, Dict, Any
import streamlit as st

# backend API helpers
from services.agent_api import recipe_suggestions, recipe_detail

# --------- local state keys ----------
_SUG_KEY = "recipe_suggestions"
_SEL_KEY = "recipe_selected"
_DET_KEY = "recipe_detail"

def _ensure_state():
    st.session_state.setdefault(_SUG_KEY, [])
    st.session_state.setdefault(_SEL_KEY, None)
    st.session_state.setdefault(_DET_KEY, None)

def _dish_card(d: Dict[str, Any]) -> str:
    return f"**{d.get('name','Dish')}** — {d.get('one_liner','')}"

def _decode_b64_image(b64_str: str):
    try:
        raw = base64.b64decode(b64_str)
        return BytesIO(raw)
    except Exception:
        return None

def render_recipe_section():
    _ensure_state()

    st.subheader("🍳 Make your recipe")
    st.caption("Pick ingredients and a cuisine. We’ll suggest dishes and generate a short recipe, nutrition, and an image preview.")

    # ----- Inputs -----
    col1, col2, col3 = st.columns([1.6, 1.6, 1.0])

    with col1:
        veg = st.multiselect(
            "Vegetables",
            ["Tomato", "Onion", "Spinach", "Broccoli", "Bell Pepper", "Potato", "Cauliflower", "Mushroom", "Carrot"],
            default=["Onion", "Tomato"],
        )
    with col2:
        proteins = st.multiselect(
            "Proteins",
            ["Chicken", "Egg", "Tofu", "Paneer", "Lentils", "Fish", "Shrimp", "Turkey", "Chickpeas"],
            default=["Chicken"],
        )
    with col3:
        cuisine = st.selectbox(
            "Cuisine",
            ["american", "indian", "mexican", "italian", "mediterranean", "japanese", "chinese", "middle eastern"],
            index=1,
        )

    ingredients = veg + proteins

    st.write("")  # tiny spacer

    cA, cB, cC = st.columns([1, 1, 1])
    with cA:
        if st.button("🔎 **Find dishes**", use_container_width=True):
            if not ingredients:
                st.warning("Please choose at least one ingredient.")
            else:
                with st.spinner("Finding dish ideas…"):
                    try:
                        ideas = recipe_suggestions(ingredients=ingredients, cuisine=cuisine, count=5)
                        st.session_state[_SUG_KEY] = ideas or []
                        st.session_state[_SEL_KEY] = None
                        st.session_state[_DET_KEY] = None
                        if ideas:
                            st.success("Got some ideas!")
                        else:
                            st.info("No suggestions were returned.")
                    except Exception as e:
                        st.error(f"Could not fetch suggestions: {e}")

    with cB:
        if st.button("🧹 **Clear**", use_container_width=True):
            st.session_state[_SUG_KEY] = []
            st.session_state[_SEL_KEY] = None
            st.session_state[_DET_KEY] = None

    # ----- Suggestions list -----
    ideas: List[Dict[str, Any]] = st.session_state.get(_SUG_KEY, [])
    if ideas:
        st.markdown("#### Suggestions")
        labels = [f"{i+1}. {d.get('name','Dish')}" for i, d in enumerate(ideas)]
        idx = st.radio(
            "Choose one dish to view the recipe",
            options=list(range(len(ideas))),
            format_func=lambda i: labels[i],
            index=0 if st.session_state[_SEL_KEY] is None else st.session_state[_SEL_KEY],
            horizontal=False,
        )
        st.session_state[_SEL_KEY] = idx

        # show one-liners
        st.caption(_dish_card(ideas[idx]))

        if st.button("📜 **Get recipe**", use_container_width=True):
            chosen = ideas[idx].get("name") or ""
            with st.spinner("Generating recipe, nutrition, and image…"):
                try:
                    detail = recipe_detail(dish=chosen, ingredients=ingredients, cuisine=cuisine) or {}
                    st.session_state[_DET_KEY] = detail
                    st.success(f"Recipe ready: {chosen}")
                except Exception as e:
                    st.error(f"Could not fetch recipe detail: {e}")

    # ----- Recipe detail -----
    detail = st.session_state.get(_DET_KEY)
    if detail:
        st.markdown("#### Recipe")
        steps = detail.get("steps") or []
        servings = detail.get("servings") or None
        if servings:
            st.markdown(f"**Servings:** {servings}")
        if steps:
            st.markdown("\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)]))

        # Nutrition
        nutr = detail.get("nutrition") or {}
        if nutr:
            st.markdown("#### Per-serving nutrition (approx.)")
            cols = st.columns(5)
            cols[0].metric("Calories", f"{nutr.get('kcal','–')}")
            cols[1].metric("Protein", f"{nutr.get('protein_g','–')} g")
            cols[2].metric("Carbs", f"{nutr.get('carbs_g','–')} g")
            cols[3].metric("Fat", f"{nutr.get('fat_g','–')} g")
            cols[4].metric("Sodium", f"{nutr.get('sodium_mg','–')} mg")

        # Image (url or base64)
        img_url = detail.get("image_url")
        img_b64 = detail.get("image_b64")
        img_err = detail.get("image_error")
        if img_url:
            st.image(img_url, caption=detail.get("dish") or "Recipe", use_column_width=True)
        elif img_b64:
            bio = _decode_b64_image(img_b64)
            if bio:
                st.image(bio, caption=detail.get("dish") or "Recipe", use_column_width=True)
        elif img_err:
            st.info(f"(No image available: {img_err})")

        # Tiny trust note (optional)
        st.caption("Nutrition is model-estimated; for clinical needs verify with a registered dietitian.")
