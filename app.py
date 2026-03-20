import streamlit as st
import google.generativeai as genai

st.title("🔍 Diagnostic Modèles Gemini")

api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    st.error("Clé GEMINI_API_KEY manquante.")
else:
    genai.configure(api_key=api_key)
    try:
        modeles = genai.list_models()
        st.success("✅ Connexion OK. Modèles disponibles sur ton compte :")
        for m in modeles:
            if "generateContent" in m.supported_generation_methods:
                st.write(f"✅ **{m.name}** — {m.display_name}")
            else:
                st.write(f"⛔ {m.name} (pas generateContent)")
    except Exception as e:
        st.error(f"Erreur : {e}")
