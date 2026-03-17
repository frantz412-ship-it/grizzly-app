import streamlit as st
from google import genai # Nouvelle syntaxe
import json
from docx import Document

# --- CONFIGURATION API ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=API_KEY) # Nouveau client
except Exception:
    st.error("Configurez 'GOOGLE_API_KEY' dans les Secrets Streamlit.")
    st.stop()

# --- STYLE & CONFIG PAGE ---
st.set_page_config(page_title="Grizzly et Moineau - Bible Pro", layout="wide")
st.markdown("<style>.stApp { background-color: #0f172a; color: #f1f5f9; }</style>", unsafe_allow_html=True)

# --- FONCTIONS ---
def read_docx(file):
    doc = Document(file)
    return '\n'.join([p.text for p in doc.paragraphs])

def analyser_texte(texte):
    try:
        # Nouvelle façon d'appeler Gemini 2.0
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"Analyse ce texte de Grizzly et Moineau et réponds en JSON : {texte[:8000]}",
            config={
                'response_mime_type': 'application/json', # Plus besoin de nettoyer le markdown !
            }
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

# --- UI ---
st.title("📚 Grizzly et Moineau : Analyseur de Saga")

uploaded_file = st.file_uploader("Importer un chapitre (.docx)", type="docx")
if uploaded_file:
    full_text = read_docx(uploaded_file)
    if st.button("🚀 LANCER L'ANALYSE"):
        with st.spinner("Analyse 2.0 en cours..."):
            res = analyser_texte(full_text)
            if "error" in res:
                st.error(res["error"])
            else:
                st.success("Analyse terminée !")
                st.write(res) # Affiche le JSON proprement
                    
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
