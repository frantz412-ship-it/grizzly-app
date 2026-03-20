import os
import re
import json
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
st.set_page_config(page_title="Archiviste V18.2", layout="wide")

CANON_DATA = {
    "Jonas": "ÂGE: 17 ans. Grizzly. Couple exclusif Léo. Aura: VERTE (Colère). Yeux verts, cheveux bruns, cicatrice gorge.",
    "Léo": "ÂGE: 15-17 ans. Moineau. Couple exclusif Jonas. Aura: BLEUE. Louve blanche de lumière (gardienne). Voit les fils.",
    "Zack": "ÂGE: 15 ans. Zackary/Zack. Aura: ROUGE CHAUD. Ailes aux flancs. Couple asexuel avec Jade. Talismans: Louveteau pierre, sac fleur.",
    "Jade": "Jade. Cheffe de terrain. Aura: JAUNE/DORÉE. Arme: Fronde. Souveraineté. Couple asexuel avec Zack.",
    "Autyss": "Autyss. Chirurgien des colonnes. Aura: VIOLETTE. Capacité: Colonnes. Profil autiste (règles strictes).",
    "Luc": "Luc. Surnom: Gremlin. Protégé de Zack. Enjeux d'appartenance.",
    "SAGA": "Couple Jonas-Léo intouchable. Si flou = non. Consentement explicite. Reconstruction et Trauma."
}

SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

# ==========================================
# 2. MÉMOIRE SESSION
# ==========================================
if "txt_complet" not in st.session_state:
    st.session_state.txt_complet = ""
if "analyses" not in st.session_state:
    st.session_state.analyses = []

# ==========================================
# 3. FONCTIONS TECHNIQUES
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
    except: return ""
    return ""

def trier_passages_perso(texte, nom_perso, contexte_mots=1000):
    """Filtre le manuscrit pour n'envoyer que l'essentiel à l'IA."""
    nom = nom_perso.lower()
    matches = [m.start() for m in re.finditer(re.escape(nom), texte.lower())]
    extraits = []
    for m in matches[:25]: # Limite à 25 passages pour le quota gratuit
        start, end = max(0, m - contexte_mots), min(len(texte), m + contexte_mots)
        extraits.append(texte[start:end])
    return "\n\n--- EXTRAIT ---\n\n".join(extraits)

# ==========================================
# 4. MOTEUR IA (GÉNÉRATION 3)
# ==========================================
def appel_ia_stable(prompt: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key: return "❌ Clé API manquante."
    genai.configure(api_key=api_key)
    
    # On utilise les noms EXACTS confirmés par ton diagnostic
    modeles = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.0-flash"]
    
    for m_name in modeles:
        try:
            model = genai.GenerativeModel(m_name)
            resp = model.generate_content(prompt)
            return resp.text
        except: continue
    return "❌ Aucun modèle Gemini n'a répondu. Vérifie tes quotas AI Studio."

# ==========================================
# 5. CONNEXION SHEETS (GSPREAD)
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
            ws = ss.add_worksheet(title=nom_onglet, rows="1000", cols="4")
            ws.append_row(["Date", "Type", "Analyse", "Perso"])
            return ws
    except Exception as e:
        st.error(f"Erreur Sheets : {e}")
        return None

# ==========================================
# 6. INTERFACE
# ==========================================
with st.sidebar:
    st.title("🛡️ L'Archiviste V18.2")
    files = st.file_uploader("Charger tes Tomes", accept_multiple_files=True, type=["pdf", "docx", "odt"])
    if st.button("🚀 Scanner la Saga"):
        if files:
            with st.spinner("Fusion des manuscrits..."):
                all_text = ""
                for f in files:
                    all_text += f"\n\n[TOME: {f.name}]\n\n" + extraire_texte(f)
                st.session_state.txt_complet = all_text.replace("’", "'").replace("œ", "oe")
                st.success(f"Saga chargée ! ({len(st.session_state.txt_complet)} caractères)")

st.title("🔬 Laboratoire d'Analyse Narrative")

if not st.session_state.txt_complet:
    st.info("📂 Charge tes fichiers dans la barre latérale pour commencer.")
else:
    perso = st.selectbox("Personnage à analyser", list(CANON_DATA.keys()))
    col1, col2, col3, col4 = st.columns(4)
    outils = {
        "🧠 Psyché": "Trauma, émotions et évolution psychologique.",
        "⚔️ Physique": "Portrait, auras et manifestations somatiques.",
        "🕸️ Liens": "Relations affectives, complicité et fils bleus.",
        "🕵️ Diagnostic": "Analyse clinique du trauma et cohérence narrative."
    }

    for i, (label, focus) in enumerate(outils.items()):
        if [col1, col2, col3, col4][i].button(label, use_container_width=True):
            with st.spinner(f"Analyse de {perso}..."):
                extraits = trier_passages_perso(st.session_state.txt_complet, perso)
                prompt = f"RÉFÉRENCE CANON {perso}: {CANON_DATA[perso]}\n\nFOCUS: {focus}\n\nMANUSCRIT:\n{extraits}"
                res = appel_ia_stable(prompt)
                st.session_state.analyses.insert(0, {
                    "date": datetime.now().strftime("%d/%m %H:%M"),
                    "perso": perso, "type": label, "texte": res
                })

for ana in st.session_state.analyses:
    with st.expander(f"📌 {ana['type']} - {ana['perso']} ({ana['date']})", expanded=True):
        st.markdown(ana["texte"])
        if st.button(f"💾 Archiver {ana['perso']}", key=ana['date']+ana['type']):
            ws = get_worksheet(ana["perso"])
            if ws:
                ws.append_row([ana['date'], ana['type'], ana['texte'], ana['perso']])
                st.success("Archivé dans Google Sheets !")
