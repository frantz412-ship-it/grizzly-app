import streamlit as st
import google.generativeai as genai
import json
from docx import Document
import io

# --- CONFIGURATION API ---
# Ta clé est directement intégrée ici
API_KEY = "AIzaSyAVOZz6MuW_ml4GbvLyUaQUGyNLSmTTrWs"
genai.configure(api_key=API_KEY)

# --- CONFIGURATION PAGE ---
st.set_page_config(
    page_title="Grizzly et Moineau - Bible Pro",
    page_icon="📚",
    layout="wide"
)

# --- STYLE CSS (CORRIGÉ) ---
st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .stTextArea textarea { background-color: #000; color: #38bdf8; border: 1px solid #38bdf8; }
    .result-card { 
        background-color: #1e293b; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #334155;
        margin-bottom: 15px;
    }
    .tag { 
        display: inline-block; 
        padding: 4px 12px; 
        border-radius: 20px; 
        background: #0f172a; 
        border: 1px solid #38bdf8; 
        margin: 4px; 
        font-size: 0.85rem;
        color: #38bdf8;
    }
    h1, h2, h3 { color: #38bdf8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS TECHNIQUES ---
def read_docx(file):
    """Lit un fichier Word et extrait le texte."""
    doc = Document(file)
    return '\n'.join([para.text for para in doc.paragraphs])

def analyser_texte(texte):
    """Envoie le texte à l'IA avec gestion de secours pour le modèle."""
    # Liste de modèles à tester par ordre de priorité pour éviter la 404
    model_names = ['gemini-1.5-flash', 'gemini-1.5-flash-latest']
    
    prompt = f"""Tu es l'expert de la saga 'Grizzly et Moineau'. Analyse cet extrait de chapitre.
    Identifie logiquement : Personnages, Capacités, Armes, Traumas, Lieux.
    Réponds UNIQUEMENT en JSON pur avec cette structure :
    {{"personnages":[], "capacites":[], "armes":[], "traumas":[], "lieux":[], "resume":""}}
    
    Texte à analyser :
    {texte[:6000]}"""

    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt, safety_settings=safety)
            # Nettoyage du JSON
            clean_res = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_res)
        except Exception:
            continue # Si un modèle rate, on passe au suivant
            
    raise Exception("Aucun modèle Gemini disponible n'a répondu (404 ou Quota).")

# --- INTERFACE UTILISATEUR ---
st.title("📚 Grizzly et Moineau : Analyseur de Saga")
st.write("Outil professionnel d'indexation pour PC et Mobile.")

tab1, tab2, tab3 = st.tabs(["🔍 Analyse de Chapitre", "👥 Fiches Persos", "🗺️ Univers"])

with tab1:
    st.subheader("Importer un document (.docx)")
    file = st.file_uploader("Glisse ton chapitre ici", type="docx")
    
    if file:
        texte = read_docx(file)
        st.info(f"Fichier chargé : {len(texte)} caractères.")
        
        if st.button("🚀 LANCER L'ANALYSE LOGIQUE"):
            with st.spinner("L'IA déchiffre ton univers..."):
                try:
                    res = analyser_texte(texte)
                    
                    # AFFICHAGE
                    st.markdown(f"### 📝 Résumé Rapide\n> {res['resume']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### 👤 Personnages")
                        for p in res['personnages']:
                            st.markdown(f'<span class="tag">{p}</span>', unsafe_allow_html=True)
                            
                        st.markdown("#### ✨ Capacités & Pouvoirs")
                        for c in res['capacites']:
                            st.markdown(f'<span class="tag">{c}</span>', unsafe_allow_html=True)

                    with col2:
                        st.markdown("#### 🧠 Thèmes & Traumas")
                        for t in res['traumas']:
                            st.markdown(f'<span class="tag">{t}</span>', unsafe_allow_html=True)
                            
                        st.markdown("#### 📍 Lieux & Objets")
                        items = res['lieux'] + res['armes']
                        for i in items:
                            st.markdown(f'<span class="tag">{i}</span>', unsafe_allow_html=True)
                            
                except Exception as e:
                    st.error(f"Erreur : {e}")

with tab2:
    st.info("Les fiches se rempliront automatiquement lors des prochaines mises à jour.")
    st.write("**Lo (Moineau)** : Visions, fils bleus, jambe blessée.")
    st.write("**Jonas (Grizzly)** : Protecteur, Colère, fusil.")

with tab3:
    st.write("**Lieux détectés dans la saga** : Badlands, Cit, Grenville, Forge, Village Soleil.")
