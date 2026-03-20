import os
import re
import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime, timezone
from PyPDF2 import PdfReader
from docx import Document
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & CANON DÉFINITIF ---
st.set_page_config(page_title="Grizzly & Moineau - Lab", page_icon="📚", layout="wide")

CANON_DATA = {
    "Jonas": "ÂGE: 17 ans. Grizzly. Couple exclusif Léo. Aura: VERTE (Colère).",
    "Léo": "ÂGE: 15-17 ans. Moineau. Couple exclusif Jonas. Aura: BLEUE. Louve blanche.",
    "Zack": "ÂGE: 15 ans. Zackary/Zack. Aura: ROUGE CHAUD. Ailes aux flancs. Note: Luc 'Gremlin'.",
    "Jade": "Jade. Cheffe de terrain. Aura: JAUNE/DORÉE. Souveraineté.",
    "Autyss": "Autyss. Chirurgien des colonnes. Aura: VIOLETTE. Poésie.",
    "Luc": "Luc. Surnom: Gremlin. Personnage secondaire.",
    "SAGA": "Couple Jonas-Léo intouchable. Consentement explicite. Corps passager."
}

# --- 2. MÉMOIRE DE L'APPLICATION ---
if "chapitres" not in st.session_state:
    st.session_state.chapitres = []
if "analyses" not in st.session_state:
    st.session_state.analyses = []

# --- 3. FONCTIONS TECHNIQUES ---
def normaliser_texte(txt: str) -> str:
    replacements = {"’": "'", "«": '"', "»": '"', "œ": "oe", "…": "..."}
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt

def extraire_texte(file) -> str:
    try:
        if file.name.endswith(".pdf"):
            return " ".join([page.extract_text() or "" for page in PdfReader(file).pages])
        elif file.name.endswith(".docx"):
            return " ".join([p.text for p in Document(file).paragraphs])
    except Exception as e:
        st.error(f"Erreur lecture {file.name}: {e}")
    return ""

def decouper_chapitres(texte: str):
    parts = re.split(r"(?i)(chapitre\s+\d+)", texte)
    if len(parts) <= 1:
        return [{"titre": "Manuscrit Complet", "contenu": texte}]
    chapitres = []
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            chapitres.append({"titre": parts[i], "contenu": parts[i + 1]})
    return chapitres

# --- 4. CONNEXION IA (Méthode Résiliente "Roc de Pierre") ---
def appel_ia_stable(prompt, temperature=0.2):
    """
    Tente d'utiliser les modèles dans l'ordre de stabilité.
    C'est cette méthode qui évite les erreurs 404.
    """
    if "GEMINI_API_KEY" not in st.secrets:
        return "❌ Erreur : Clé API manquante dans les Secrets Streamlit."
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Liste des modèles qui ont fonctionné lors du diagnostic
    modeles_a_tester = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    for m_name in modeles_a_tester:
        try:
            model = genai.GenerativeModel(m_name)
            resp = model.generate_content(
                prompt,
                generation_config={"temperature": temperature}
            )
            if resp.text:
                return resp.text
        except Exception:
            continue # Passe au modèle suivant en cas d'échec
            
    return "❌ Aucun modèle Gemini n'a répondu (404 ou Quota atteint)."

# --- 5. SIDEBAR : GESTION DES FICHIERS ---
with st.sidebar:
    st.header("📂 Manuscrit")
    files = st.file_uploader("Importer Tomes (PDF/DOCX)", accept_multiple_files=True)

    if st.button("🚀 Traiter les fichiers"):
        if not files:
            st.warning("Sélectionne au moins un fichier.")
        else:
            with st.spinner("Décodage de la Saga..."):
                all_text = ""
                for f in files:
                    all_text += f"\n\n[TOME: {f.name}]\n\n"
                    all_text += extraire_texte(f)
                st.session_state.chapitres = decouper_chapitres(normaliser_texte(all_text))
            st.success(f"{len(st.session_state.chapitres)} sections détectées.")

    if st.button("🗑️ Reset Application"):
        st.session_state.chapitres = []
        st.session_state.analyses = []
        st.rerun()

# --- 6. STATION D'ANALYSE ---
st.title("🔬 Laboratoire Grizzly & Moineau")

if st.session_state.chapitres:
    col_sel, col_outils = st.columns([1, 2])
    with col_sel:
        perso = st.selectbox("Personnage à scanner", list(CANON_DATA.keys()))
        filtre = [c for c in st.session_state.chapitres if perso.lower() in c["contenu"].lower() or perso == "SAGA"]
        selection = st.multiselect("Sélectionner les chapitres", filtre, format_func=lambda x: x["titre"])

    with col_outils:
        st.subheader("Outils d'analyse")
        btns = st.columns(4)
        config_outils = {
            "🧠 Psyché": "Trauma, évolution psychologique et émotions.",
            "⚔️ Physique": "Portrait physique, Aura et manifestations de pouvoir.",
            "🕸️ Liens": "Fils bleus, relations de groupe et complicité.",
            "🕵️ Incohérences": "Contradictions avec le Canon fixé.",
        }

        for i, (label, focus) in enumerate(config_outils.items()):
            if btns[i].button(label):
                if not selection:
                    st.error("Choisis au moins un chapitre !")
                else:
                    contexte = "\n\n".join([f"### {c['titre']}\n{c['contenu'][:10000]}" for c in selection])
                    prompt = f"RÉFÉRENCE CANON {perso} : {CANON_DATA[perso]}\n\nFOCUS : {focus}\n\nTEXTE :\n{contexte}"
                    
                    with st.spinner(f"Analyse de {perso} en cours..."):
                        txt_ia = appel_ia_stable(prompt)
                        
                        st.session_state.analyses.insert(0, {
                            "id": datetime.now(timezone.utc).timestamp(),
                            "date": datetime.now().strftime("%d/%m %H:%M"),
                            "perso": perso,
                            "type": label,
                            "texte": txt_ia,
                        })

# --- 7. HISTORIQUE & ARCHIVAGE ---
st.divider()
for ana in st.session_state.analyses:
    u_key = f"{ana['id']}-{ana['perso']}-{ana['type']}"
    with st.expander(f"📌 {ana['type']} - {ana['perso']} ({ana['date']})", expanded=True):
        st.markdown(ana["texte"])
        if st.button(f"💾 Archiver {ana['perso']}", key=f"btn-{u_key}"):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                # Tentative de lecture/création
                try: existing = conn.read(worksheet=ana["perso"])
                except: existing = pd.DataFrame()
                
                new_row = pd.DataFrame([ana])
                final_df = pd.concat([existing, new_row], ignore_index=True) if existing is not None and not existing.empty else new_row
                
                conn.update(worksheet=ana["perso"], data=final_df)
                st.success(f"Archivé dans l'onglet '{ana['perso']}' !")
            except Exception as e:
                st.error(f"Erreur GSheets : {e}")
