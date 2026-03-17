import streamlit as st
from google import genai
import json
from docx import Document

# --- CONFIGURATION API ---
try:
    # Récupération sécurisée de la clé depuis les secrets Streamlit
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception:
    st.error("Erreur : Configurez 'GOOGLE_API_KEY' dans les Secrets de Streamlit.")
    st.stop()

# --- STYLE & CONFIG PAGE ---
st.set_page_config(page_title="Grizzly et Moineau - Bible Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .tag { 
        display: inline-block; 
        padding: 4px 12px; 
        border-radius: 20px; 
        background: #1e293b; 
        border: 1px solid #38bdf8; 
        margin: 4px; 
        color: #38bdf8; 
        font-size: 0.85rem; 
    }
    h1, h2, h3 { color: #38bdf8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS ---
def read_docx(file):
    doc = Document(file)
    return '\n'.join([p.text for p in doc.paragraphs])

def analyser_texte(texte):
    try:
        # Utilisation de Gemini 2.0 Flash
        prompt = f"Analyse cet extrait de 'Grizzly et Moineau'. Identifie : personnages, capacites, armes, traumas, lieux, resume. Réponds UNIQUEMENT en JSON : {texte[:8000]}"
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

# --- INTERFACE ---
st.title("📚 Grizzly et Moineau : Analyseur de Saga")

uploaded_file = st.file_uploader("Importer un chapitre (.docx)", type="docx")

if uploaded_file:
    full_text = read_docx(uploaded_file)
    st.info(f"Texte chargé : {len(full_text)} caractères.")
    
    if st.button("🚀 LANCER L'ANALYSE"):
        with st.spinner("Analyse en cours..."):
            res = analyser_texte(full_text)
            
            if "error" in res:
                st.error(f"Erreur IA : {res['error']}")
            else:
                st.success("Analyse terminée !")
                
                # --- AFFICHAGE DES RÉSULTATS (Indentation critique ici) ---
                st.subheader("📝 Résumé du Chapitre")
                st.info(res.get('resume', 'Aucun résumé généré.'))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**👤 Personnages**")
                    persos = res.get('personnages', [])
                    if persos:
                        for p in persos:
                            st.markdown(f'<span class="tag">{p}</span>', unsafe_allow_html=True)
                    else:
                        st.write("_Aucun détecté_")
                    
                    st.write("**✨ Capacités & Armes**")
                    items = res.get('capacites', []) + res.get('armes', [])
                    for i in items:
                        st.markdown(f'<span class="tag">{i}</span>', unsafe_allow_html=True)

                with col2:
                    st.write("**🧠 Thèmes & Traumas**")
                    traumas = res.get('traumas', [])
                    for t in traumas:
                        st.markdown(f'<span class="tag">{t}</span>', unsafe_allow_html=True)
                    
                    st.write("**📍 Lieux**")
                    lieux = res.get('lieux', [])
                    for l in lieux:
                        st.markdown(f'<span class="tag">{l}</span>', unsafe_allow_html=True)
