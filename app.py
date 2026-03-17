import streamlit as st
from google import genai
import json
from docx import Document
import time

# --- 1. CONFIGURATION API SÉCURISÉE ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception:
    st.error("⚠️ Clé API manquante. Configurez 'GOOGLE_API_KEY' dans les Secrets de Streamlit.")
    st.stop()

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Grizzly et Moineau - Bible Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .tag { 
        display: inline-block; padding: 4px 12px; border-radius: 20px; 
        background: #1e293b; border: 1px solid #38bdf8; 
        margin: 4px; color: #38bdf8; font-size: 0.85rem; 
    }
    h1, h2, h3 { color: #38bdf8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FONCTIONS TECHNIQUES ---
def read_docx(file):
    doc = Document(file)
    return '\n'.join([p.text for p in doc.paragraphs])

def decouper_texte(texte, taille=5000):
    """Découpe le texte en blocs pour respecter les quotas gratuits."""
    return [texte[i:i+taille] for i in range(0, len(texte), taille)]

def analyser_chapitre_complet(texte_complet):
    morceaux = decouper_texte(texte_complet)
    resultats_finaux = {
        "personnages": set(), "capacites": set(), "armes": set(),
        "traumas": set(), "lieux": set(), "resumes": []
    }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, morceau in enumerate(morceaux):
        status_text.text(f"Analyse du bloc {idx+1}/{len(morceaux)}...")
        try:
            prompt = f"Analyse cet extrait de 'Grizzly et Moineau'. Identifie : personnages, capacites, armes, traumas, lieux, resume. Réponds UNIQUEMENT en JSON : {morceau}"
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            data = json.loads(response.text)
            
            # Fusion des données
            for cle in ["personnages", "capacites", "armes", "traumas", "lieux"]:
                if cle in data and isinstance(data[cle], list):
                    resultats_finaux[cle].update(data[cle])
            
            if "resume" in data:
                resultats_finaux["resumes"].append(data["resume"])
            
            # Pause de sécurité pour le quota (Free Tier)
            time.sleep(3) 
            
        except Exception as e:
            st.warning(f"Bloc {idx+1} ignoré suite à une erreur (Quota probable).")
            
        progress_bar.progress((idx + 1) / len(morceaux))

    status_text.text("✅ Analyse terminée !")
    return resultats_finaux

# --- 4. INTERFACE UTILISATEUR ---
st.title("📚 Grizzly et Moineau : Analyseur de Saga")

# C'est cette ligne qui manquait ou était mal placée :
uploaded_file = st.file_uploader("Importer un chapitre (.docx)", type="docx")

if uploaded_file:
    full_text = read_docx(uploaded_file)
    st.info(f"Fichier chargé : {len(full_text)} caractères.")
    
    if st.button("🚀 LANCER L'ANALYSE COMPLÈTE"):
        res = analyser_chapitre_complet(full_text)
        
        # --- AFFICHAGE ---
        st.subheader("📝 Résumé Global")
        st.info(" ".join(res["resumes"]))
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**👤 Personnages**")
            for p in sorted(res["personnages"]):
                st.markdown(f'<span class="tag">{p}</span>', unsafe_allow_html=True)
            
            st.write("**✨ Capacités & Armes**")
            all_items = sorted(list(res["capacites"]) + list(res["armes"]))
            for i in all_items:
                st.markdown(f'<span class="tag">{i}</span>', unsafe_allow_html=True)

        with col2:
            st.write("**🧠 Thèmes & Traumas**")
            for t in sorted(res["traumas"]):
                st.markdown(f'<span class="tag">{t}</span>', unsafe_allow_html=True)
            
            st.write("**📍 Lieux**")
            for l in sorted(res["lieux"]):
                st.markdown(f'<span class="tag">{l}</span>', unsafe_allow_html=True)
