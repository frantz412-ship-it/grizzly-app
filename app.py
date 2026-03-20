import os
import re
import json
import datetime

import streamlit as st
import pdfplumber
from docx import Document
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

import gspread
from google.oauth2.service_account import Credentials

# Nouveau SDK Gemini
from google import genai
from google.genai import types

# ==========================================
# 0. CONFIG GEMINI (NUAGE)
# ==========================================

if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    api_key_env = os.getenv("GEMINI_API_KEY")
    if not api_key_env:
        st.error("GEMINI_API_KEY manquante (Secrets Streamlit ou variable d'environnement).")
    client = genai.Client(api_key=api_key_env)

# ==========================================
# 1. CONSTANTES (CANON)
# ==========================================

CONSTANTES_SAGA = {
    "Zack": "ÂGE: 15 ans. Zackary/Zack. Bisexuel. Couple Asexuel avec Jade. Aura Rouge/Noir.",
    "Jonas": "ÂGE: 17 ans. Grizzly. Gay. Couple Léo. Pas de sexe avec Jade. Aura Brun.",
    "Léo": "ÂGE: 15 ans. Moineau. Bisexuel. Couple Jonas. Voit les fils.",
    "SAGA": "Thèmes: Reconstruction, Souveraineté, l'Ombre."
}

# ==========================================
# 2. GOOGLE SHEETS (optionnel)
# ==========================================

SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

def connecter_et_obtenir_onglet(nom_onglet):
    try:
        if "GCP_JSON_BRUT" not in st.secrets:
            return None
        json_info = json.loads(st.secrets["GCP_JSON_BRUT"], strict=False)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(json_info, scopes=scope)
        client_gs = gspread.authorize(creds)
        ss = client_gs.open_by_key(SHEET_ID)
        try:
            return ss.worksheet(nom_onglet)
        except gspread.exceptions.WorksheetNotFound:
            nouvel_onglet = ss.add_worksheet(title=nom_onglet, rows="2000", cols="5")
            nouvel_onglet.append_row(["Date", "Diagnostic", "Type"])
            return nouvel_onglet
    except Exception as e:
        st.error(f"Erreur Sheets : {e}")
        return None

# ==========================================
# 3. IA – APPEL GEMINI
# ==========================================

def appel_ia(prompt: str, temperature: float = 0.1) -> str:
    """
    Appel unique à Gemini via google-genai.
    On utilise flash par défaut (rapide, stable).
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # change en "gemini-2.0-pro" si ton compte y a accès
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=4096,
            ),
        )
        return response.text or ""
    except Exception as e:
        return f"❌ Erreur Gemini : {e}"

# ==========================================
# 4. FICHIERS – EXTRACTION & CHAPITRES
# ==========================================

def extraire_texte(f) -> str:
    """Lit PDF / DOCX / ODT et renvoie le texte brut."""
    try:
        if f.name.endswith(".pdf"):
            with pdfplumber.open(f) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
        elif f.name.endswith(".docx"):
            doc = Document(f)
            return "\n".join([p.text for p in doc.paragraphs])
        elif f.name.endswith(".odt"):
            odt_doc = load(f)
            return "\n".join([extractText(p) for p in odt_doc.getElementsByType(P)])
        return ""
    except Exception:
        return ""

def decouper_chapitres(texte: str):
    pattern = r'(?i)chapitre\s+\d+'
    segments = re.split(pattern, texte)
    titres = re.findall(pattern, texte)
    chaps = []

    if len(segments) > 0 and len(segments[0].strip()) > 100:
        chaps.append({"titre": "Prologue", "contenu": segments[0].strip()})

    for i, t in enumerate(titres):
        if i + 1 < len(segments):
            chaps.append({"titre": t, "contenu": segments[i + 1].strip()})
    return chaps

# ==========================================
# 5. INTERFACE STREAMLIT (NUAGE)
# ==========================================

st.set_page_config(page_title="Archiviste Stable (Gemini SDK)", layout="wide")
st.title("🛡️ L'Archiviste V16.5 (Roc de Pierre, Gemini SDK)")

if "db" not in st.session_state:
    st.session_state.db = {"chapitres": [], "ready": False}

f_inputs = st.sidebar.file_uploader(
    "Charger les fichiers",
    type=["pdf", "docx", "odt"],
    accept_multiple_files=True,
)

if f_inputs and not st.session_state.db["ready"]:
    if st.button("🚀 Scanner la Saga"):
        full_txt = ""
        for f in f_inputs:
            full_txt += extraire_texte(f) + "\n\n"
        full_txt = full_txt.replace("’", "'").replace("œ", "oe")
        st.session_state.db["chapitres"] = decouper_chapitres(full_txt)
        st.session_state.db["ready"] = True
        st.rerun()

if st.session_state.db["ready"]:
    perso = st.sidebar.selectbox("Personnage", options=list(CONSTANTES_SAGA.keys()))

    indices = [
        i for i, c in enumerate(st.session_state.db["chapitres"])
        if perso.lower() in c['contenu'].lower()
    ]

    sel = st.multiselect(
        "Chapitres",
        options=indices,
        format_func=lambda x: st.session_state.db["chapitres"][x]['titre'],
    )

    if sel and st.button("🧠 Analyser"):
        txt_focus = "\n".join(
            [st.session_state.db["chapitres"][i]['contenu'][:10000] for i in sel]
        )
        canon = CONSTANTES_SAGA[perso]
        prompt = f"""
[DIAGNOSTIC ARCHIVISTE STABLE]

PERSONNAGE : {perso}
CANON (à respecter strictement) : {canon}

CONSigne :
- Analyse le personnage dans ces extraits (somatique, réactions, souveraineté).
- Ne contredit jamais le canon.
- Si une information n'est pas présente, écris "Non mentionné dans le manuscrit.".

EXTRAITS :
{txt_focus}
"""
        with st.spinner("L'IA consulte les archives..."):
            resultat = appel_ia(prompt, temperature=0.1)
            st.markdown(resultat)
            st.session_state["dernier_resultat"] = resultat
            st.session_state["dernier_perso"] = perso

    # Archivage optionnel dans Sheets
    if "dernier_resultat" in st.session_state and st.button("💾 Archiver dans Sheets"):
        onglet = connecter_et_obtenir_onglet(st.session_state.get("dernier_perso", "SAGA"))
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row(
                [date_now, st.session_state["dernier_resultat"], "ARCHIVISTE STABLE V16.5"]
            )
            st.success("✅ Diagnostic archivé dans Google Sheets.")

if st.sidebar.button("🗑️ Reset"):
    st.session_state.db = {"chapitres": [], "ready": False}
    st.rerun()
