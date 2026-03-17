import streamlit as st
import google.generativeai as genai
import json
from docx import Document
import io

# --- CONFIGURATION ---
API_KEY = "AIzaSyAVOZz6MuW_ml4GbvLyUaQUGyNLSmTTrWs"
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Grizzly et Moineau - Bible Pro", layout="wide")

# --- STYLE PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    .stTextArea textarea { background-color: #000; color: #38bdf8; }
    .tag { 
        display: inline-block; 
        padding: 2px 10px; 
        border-radius: 10px; 
        background: #1e293b; 
        border: 1px solid #38bdf8; 
        margin: 2px; 
        font-size: 0.8rem; 
    }
    </style>
    """, unsafe_allow_html=True) # <-- C'est ici qu'on corrige 'html' au lieu de 'stdio'
# --- FONCTION DE LECTURE DOCX ---
def read_docx(file):
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# --- LOGIQUE D'ANALYSE ---
def analyser_texte(texte):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""Tu es l'expert de la saga 'Grizzly et Moineau'. Analyse cet extrait de chapitre.
    Identifie : Personnages, Capacités, Armes, Traumas, Lieux.
    Réponds UNIQUEMENT en JSON :
    {{"personnages":[], "capacites":[], "armes":[], "traumas":[], "lieux":[], "resume":""}}
    Texte : {texte[:4000]}""" # On limite à 4000 caractères pour la stabilité
    
    response = model.generate_content(
        prompt,
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    )
    return json.loads(response.text.replace('```json', '').replace('```', ''))

# --- INTERFACE ---
st.title("📚 Grizzly et Moineau : Gestionnaire de Chapitres")

tab1, tab2 = st.tabs(["🔍 Analyse de Fichier", "👥 Personnages"])

with tab1:
    st.subheader("Importer un Chapitre (.docx)")
    uploaded_file = st.file_uploader("Choisis ton fichier Word", type="docx")
    
    if uploaded_file is not None:
        texte_complet = read_docx(uploaded_file)
        st.info(f"Fichier chargé : {len(texte_complet)} caractères détectés.")
        
        # Aperçu du début du texte
        with st.expander("Voir l'aperçu du texte"):
            st.write(texte_complet[:1000] + "...")

        if st.button("Lancer l'Analyse Intelligente"):
            with st.spinner("L'IA parcourt ton chapitre..."):
                try:
                    res = analyser_texte(texte_complet)
                    
                    # AFFICHAGE DES RÉSULTATS
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**👤 Personnages :**")
                        st.write(", ".join(res['personnages']))
                        st.write("**✨ Capacités & Armes :**")
                        st.write(", ".join(res['capacites'] + res['armes']))
                    
                    with col2:
                        st.write("**🧠 Thèmes & Traumas :**")
                        st.write(", ".join(res['traumas']))
                        st.write("**📍 Lieux :**")
                        st.write(", ".join(res['lieux']))
                    
                    st.divider()
                    st.write("**📝 Résumé du chapitre :**")
                    st.info(res['resume'])
                    
                except Exception as e:
                    st.error(f"Erreur d'analyse : {e}")

with tab2:
    st.write("Ici tu pourras voir l'évolution de Lo, Jonas et les autres au fil des tomes.")
