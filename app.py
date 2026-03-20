import os
import re
import json
import time
import pandas as pd
import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# ==========================================
# 1. CONFIGURATION & CANON (STRICT)
# ==========================================

st.set_page_config(page_title="Archiviste V18.0", layout="wide")

CANON_DATA = {
    "Jonas": "ÂGE: 17 ans. Grizzly. Couple exclusif Léo. Aura: VERTE phosphorescente (Colère). Yeux verts, cheveux bruns, cicatrice gorge.",
    "Léo": "ÂGE: 15-17 ans. Moineau. Couple exclusif Jonas. Aura: BLEUE. Louve blanche de lumière (gardienne). Voit les fils.",
    "Zack": "ÂGE: 15 ans. Zackary/Zack. Aura: ROUGE CHAUD. Ailes aux flancs. Couple asexuel avec Jade. Talismans: Louveteau pierre, sac fleur.",
    "Jade": "Jade. Cheffe de terrain. Aura: JAUNE/DORÉE. Arme: Fronde. Souveraineté. Couple asexuel avec Zack.",
    "Autyss": "Autyss. Chirurgien des colonnes. Aura: VIOLETTE. Capacité: Colonnes. Profil autiste (règles strictes).",
    "Luc": "Luc. Surnom: Gremlin. Protégé de Zack. Enjeux d'appartenance.",
    "SAGA": "Couple Jonas-Léo intouchable. Si flou = non. Consentement explicite. Reconstruction et Trauma."
}

# Ton ID Google Sheet
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

# ==========================================
# 2. MÉMOIRE SESSION
# ==========================================

if "txt_complet" not in st.session_state:
    st.session_state.txt_complet = ""
if "analyses" not in st.session_state:
    st.session_state.analyses = []

# ==========================================
# 3. TRIAGE ET EXTRACTION (ÉCONOMIE DE QUOTA)
# ==========================================

def extraire_texte(file) -> str:
    try:
        if file.name.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
        elif file.name.endswith(".docx"):
            return "\n".join([p.text for p in Document(file).paragraphs])
        elif file.name.endswith(".odt"):
            odt_doc = load(file)
            return "\n".join([extractText(p) for p in odt_doc.getElementsByType(P)])
    except Exception: return ""
    return ""

def trier_passages_perso(texte, nom_perso, contexte_mots=800):
    """
    Filtre 1600 pages pour n'envoyer que les extraits du personnage.
    C'est le secret pour ne pas payer d'abonnement.
    """
    nom = nom_perso.lower()
    matches = [m.start() for m in re.finditer(re.escape(nom), texte.lower())]
    
    extraits = []
    # On prend les 25 occurrences les plus significatives pour rester sous le quota
    for m in matches[:25]:
        start = max(0, m - contexte_mots)
        end = min(len(texte), m + contexte_mots)
        extraits.append(texte[start:end])
    
    return "\n\n--- EXTRAIT DU MANUSCRIT ---\n\n".join(extraits)

# ==========================================
# 4. MOTEUR IA (ANTI-404)
# ==========================================

def appel_ia_stable(prompt: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key: return "❌ Clé API manquante."

    genai.configure(api_key=api_key)
    # Utilisation du nom stable 'gemini-1.5-flash' (le plus robuste)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        return f"❌ Erreur Gemini : {str(e)}"

# ==========================================
# 5. CONNEXION SHEETS
# ==========================================

def get_worksheet(nom_onglet: str):
    try:
        json_info = json.loads(st.secrets["GCP_JSON_BRUT"], strict=False)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json_info, scopes=scope)
        client_gs = gspread.authorize(creds)
        ss = client_gs.open_by_key(SHEET_ID)
        try:
            return ss.worksheet(nom_onglet)
        except gspread.exceptions.WorksheetNotFound:
            ws = ss.add_worksheet(title=nom_onglet, rows="1000", cols="5")
            ws.append_row(["Date", "Type", "Analyse"])
            return ws
    except Exception as e:
        st.error(f"Erreur Sheets : {e}")
        return None

# ==========================================
# 6. INTERFACE
# ==========================================

with st.sidebar:
    st.title("🛡️ L'Archiviste V18")
    files = st.file_uploader("Charger tes Tomes", accept_multiple_files=True, type=["pdf", "docx", "odt"])
    
    if st.button("🚀 Scanner la Saga"):
        if files:
            with st.spinner("Fusion des manuscrits..."):
                all_text = ""
                for f in files:
                    all_text += f"\n\n[TOME: {f.name}]\n\n" + extraire_texte(f)
                st.session_state.txt_complet = all_text.replace("’", "'").replace("œ", "oe")
                st.success("Saga chargée en mémoire !")

st.title("🔬 Laboratoire d'Analyse Narrative")

if not st.session_state.txt_complet:
    st.info("📂 Charge tes fichiers pour commencer l'analyse.")
else:
    perso = st.selectbox("Personnage à diagnostiquer", list(CANON_DATA.keys()))
    
    col1, col2, col3, col4 = st.columns(4)
    outils = {
        "🧠 Psyché": "Trauma et évolution.",
        "⚔️ Physique": "Cicatrices, auras et somatique.",
        "🕸️ Liens": "Relations et fils d'auras.",
        "🕵️ Diagnostic": "Analyse clinique du trauma."
    }

    for i, (label, focus) in enumerate(outils.items()):
        if [col1, col2, col3, col4][i].button(label, use_container_width=True):
            with st.spinner(f"Extraction des passages de {perso}..."):
                extraits = trier_passages_perso(st.session_state.txt_complet, perso)
                prompt = f"CANON {perso}: {CANON_DATA[perso]}\nANALYSE: {focus}\nEXTRAITS: {extraits}"
                
                res = appel_ia_stable(prompt)
                st.session_state.analyses.insert(0, {
                    "date": datetime.now().strftime("%d/%m %H:%M"),
                    "perso": perso,
                    "type": label,
                    "texte": res
                })

for ana in st.session_state.analyses:
    with st.expander(f"📌 {ana['type']} - {ana['perso']} ({ana['date']})", expanded=True):
        st.markdown(ana["texte"])
        if st.button("💾 Archiver dans Google Sheets", key=ana['date']+ana['type']):
            ws = get_worksheet(ana["perso"])
            if ws:
                ws.append_row([ana['date'], ana['type'], ana['texte']])
                st.success("Archivé !")
