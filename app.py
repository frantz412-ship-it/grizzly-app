import streamlit as st
import re
import time
import google.generativeai as genai
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# ==========================================
# 0. CONFIGURATION & MOTEUR
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def appel_ia(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if "429" in str(e): return "⚠️ Quota atteint. Attends 10s."
        return f"❌ Erreur : {e}"

# ==========================================
# 1. CONVERSION & FILTRAGE (LE TRIEUR)
# ==========================================

def convertir_en_txt(f):
    """Transforme n'importe quel fichier en texte brut (.txt interne)"""
    if f.name.endswith(".pdf"):
        with pdfplumber.open(f) as pdf:
            return "\n".join([p.extract_text() or "" for p in pdf.pages])
    elif f.name.endswith(".docx"):
        return "\n".join([p.text for p in Document(f).paragraphs])
    elif f.name.endswith(".odt"):
        return "\n".join([extractText(p) for p in load(f).getElementsByType(P)])
    return ""

def extraire_passages_clefs(texte_complet, nom_perso, fenetre=500):
    """
    Trieur Python : Trouve le nom du perso et prend du contexte autour.
    Évite d'envoyer 400 pages à l'IA pour rien.
    """
    nom_perso = nom_perso.lower()
    passages = []
    # On cherche toutes les occurrences du nom
    for match in re.finditer(re.escape(nom_perso), texte_complet.lower()):
        start = max(0, match.start() - fenetre)
        end = min(len(texte_complet), match.end() + fenetre)
        passages.append(texte_complet[start:end])
    
    # On limite à 15-20 passages les plus pertinents pour ne pas saturer
    return "\n\n--- NOUVEL EXTRAIT ---\n\n".join(passages[:25])

# ==========================================
# 2. INTERFACE
# ==========================================
st.set_page_config(page_title="L'Archiviste Stratège", layout="wide")
st.title("🛡️ L'Archiviste V17.0 (Triage & Fiches)")

# Sidebar : Chargement
st.sidebar.header("📁 Importation de la Saga")
f_inputs = st.sidebar.file_uploader("Charger les Tomes", type=["pdf", "docx", "odt"], accept_multiple_files=True)

if f_inputs:
    if st.sidebar.button("⚙️ Préparer le Triage"):
        with st.spinner("Conversion en .txt en cours..."):
            full_txt = ""
            for f in f_inputs:
                full_txt += convertir_en_txt(f) + "\n\n"
            st.session_state.txt_saga = full_txt.replace("’", "'")
            st.success("Saga prête pour l'analyse !")

# Analyse et Fiche
if "txt_saga" in st.session_state:
    nom_cible = st.text_input("Nom du personnage à extraire (ex: Zack, Léo, Jonas...)")
    
    if nom_cible and st.button(f"🔍 Générer la Fiche de {nom_cible}"):
        # Étape 1 : Le Triage (Python)
        with st.spinner("Triage des passages pertinents..."):
            extraits = extraire_passages_clefs(st.session_state.txt_saga, nom_cible)
        
        # Étape 2 : L'Analyse (IA)
        if extraits:
            st.info(f"Analyse de {len(extraits)//1000}ko de données ciblées...")
            prompt_fiche = f"""
            [INSTRUCTIONS ÉDITORIALES - SAGA GRIZZLY ET MOINEAU]
            À partir des extraits fournis, génère une FICHE PERSONNAGE exhaustive pour {nom_cible}.
            
            STRUCTURE :
            1. PHYSIQUE : Taille, traits, cicatrices, auras.
            2. PSYCHOLOGIE : État mental, évolution du soi, traumatismes.
            3. DIAGNOSTIC FICTIONNEL : Analyse somatique et psychologique du trauma (à titre de cohérence narrative).
            4. LIENS & RAPPORTS : Relations amoureuses, sexuelles, amitiés et tensions.
            5. ÉQUIPEMENT : Armes, vêtements récurrents.
            6. LIEUX : Endroits associés au personnage.
            7. ÉCARTS AU CANON : Si tu détectes une incohérence par rapport à l'évolution habituelle.

            EXTRAITS :
            {extraits}
            """
            with st.spinner("Gemini rédige la fiche..."):
                fiche = appel_ia(prompt_fiche)
                st.markdown(fiche)
                st.download_button("💾 Télécharger la Fiche", fiche, file_name=f"Fiche_{nom_cible}.txt")
        else:
            st.error("Aucune mention de ce personnage trouvée.")
