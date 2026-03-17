import streamlit as st
import google.generativeai as genai
import json
from docx import Document
import io

# --- CONFIGURATION API ---
API_KEY = "AIzaSyAVOZz6MuW_ml4GbvLyUaQUGyNLSmTTrWs"
genai.configure(api_key=API_KEY)

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Grizzly et Moineau - Bible Pro", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .tag { display: inline-block; padding: 4px 12px; border-radius: 20px; background: #0f172a; border: 1px solid #38bdf8; margin: 4px; color: #38bdf8; font-size: 0.85rem; }
    h1, h2, h3 { color: #38bdf8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR DIAGNOSTIC ---
with st.sidebar:
    st.title("🛠️ Outils")
    if st.button("🔍 Tester la connexion API"):
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            st.success("Connexion établie !")
            st.json(available_models)
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- FONCTIONS ---
def read_docx(file):
    doc = Document(file)
    return '\n'.join([p.text for p in doc.paragraphs])

def analyser_texte(texte):
    # Tentative de récupération dynamique du modèle
    try:
        models = [m.name for m in genai.list_models() if 'flash' in m.name.lower()]
        target_model = models[0] if models else 'gemini-1.5-flash'
        
        model = genai.GenerativeModel(target_model)
        
        prompt = f"""Analyse cet extrait de 'Grizzly et Moineau'.
        Réponds UNIQUEMENT en JSON pur :
        {{"personnages":[], "capacites":[], "armes":[], "traumas":[], "lieux":[], "resume":""}}
        Texte : {texte[:5000]}"""

        response = model.generate_content(
            prompt,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        )
        # Nettoyage et parsing
        clean_res = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_res)
    except Exception as e:
        return {"error": str(e)}

# --- UI PRINCIPALE ---
st.title("📚 Grizzly et Moineau : Analyseur de Saga")

tab1, tab2 = st.tabs(["🔍 Analyse Chapitre", "👥 Persos"])

with tab1:
    uploaded_file = st.file_uploader("Importer un .docx", type="docx")
    if uploaded_file:
        full_text = read_docx(uploaded_file)
        st.info(f"Texte chargé ({len(full_text)} caractères).")
        
        if st.button("🚀 LANCER L'ANALYSE"):
            with st.spinner("Analyse en cours..."):
                res = analyser_texte(full_text)
                
                if "error" in res:
                    st.error(f"L'IA a rencontré un problème : {res['error']}")
                else:
                    st.subheader("📝 Résumé")
                    st.write(res['resume'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**👤 Personnages**")
                        for p in res['personnages']:
                            st.markdown(f'<span class="tag">{p}</span>', unsafe_allow_html=True)
                    with col2:
                        st.write("**🧠 Thèmes & Traumas**")
                        for t in res['traumas']:
                            st.markdown(f'<span class="tag">{t}</span>', unsafe_allow_html=True)

with tab2:
    st.write("Fiches personnages en cours de construction...")
