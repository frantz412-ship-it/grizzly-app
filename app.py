import streamlit as st
import google.generativeai as genai

st.title("🔍 Diagnostic de l'Archiviste")

# 1. Vérification du Secret
if "GEMINI_API_KEY" in st.secrets:
    key = st.secrets["GEMINI_API_KEY"]
    st.write(f"✅ Clé trouvée dans les Secrets (Commence par : {key[:5]}...)")
    genai.configure(api_key=key)
else:
    st.error("❌ Aucune clé trouvée dans st.secrets['GEMINI_API_KEY']")
    st.stop()

# 2. Test de connexion réel
try:
    st.write("---")
    st.write("🔄 Tentative de lister les modèles disponibles...")
    models = genai.list_models()
    
    st.success("🎉 Connexion réussie ! Voici tes modèles :")
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            st.code(m.name)
            
except Exception as e:
    st.error("❌ ÉCHEC DE CONNEXION")
    st.warning(f"Message d'erreur réel : {e}")
    st.info("Si l'erreur parle de 'API key not valid', génère une nouvelle clé sur AI Studio.")
