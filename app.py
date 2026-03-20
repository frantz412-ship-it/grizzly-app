import os
import json
import gspread
import streamlit as st
import pdfplumber
import datetime
import google.generativeai as genai
from google.oauth2.service_account import Credentials
from docx import Document
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# --- 1. CONFIGURATION PRO ---
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé API manquante.")

# Les Commandements restent le socle immuable
VERROU_SAGA = """
COMMANDEMENTS DE FIDÉLITÉ (V16 - PRO ULTRA) :
1. NUANCE LINGUISTIQUE : "Le Fils" [fis] = Identité. "Les fils" [fil] = Liens/Auras de Léo.
2. ÉTATS FIXES : Jonas (17 ans, Brun), Léo (15 ans, Lumière), Zack (15 ans, Rouge/Noir).
3. L'OMBRE : "Ligne noire" dans les visions de Léo. Menace de corruption.
4. ZACK : Préfère "Zack" par ses amis. "Gaz" est une insulte de la Tribu. 
5. RELATIONS : Zack/Jade = Couple asexuel (Souveraineté).
6. RIGUEUR : Diagnostic basé sur les preuves. Si absent, écrire "Non mentionné".
"""

# --- 2. FONCTIONS ---

def connecter_et_obtenir_onglet(nom_onglet):
    try:
        json_info = json.loads(st.secrets["GCP_JSON_BRUT"], strict=False)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json_info, scopes=scope)
        client = gspread.authorize(creds)
        ss = client.open_by_key(SHEET_ID)
        try:
            return ss.worksheet(nom_onglet)
        except gspread.exceptions.WorksheetNotFound:
            nouvel_onglet = ss.add_worksheet(title=nom_onglet, rows="2000", cols="5")
            nouvel_onglet.append_row(["Date", "Diagnostic Pro", "Type"])
            return nouvel_onglet
    except Exception as e:
        st.error(f"Erreur Sheets : {e}")
        return None

def lire_tout(f):
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
    except Exception as e:
        return ""

def appel_ia_pro(prompt):
    # Passage au modèle PRO pour une analyse profonde
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.0)
    )
    return response.text

# --- 3. INTERFACE ---

st.set_page_config(page_title="L'Archiviste PRO ULTRA", layout="wide")
st.title("🛡️ L'Archiviste : Mode Pro (2M Tokens)")

fichiers = st.sidebar.file_uploader("Charger l'intégralité de la Saga", type=["pdf", "docx", "odt"], accept_multiple_files=True)
options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "Jade", "SAGA"]
nom_perso = st.sidebar.selectbox("Cible du Diagnostic Profond", options_cible)

if fichiers and st.button(f"🔍 Lancer Diagnostic Pro : {nom_perso}"):
    with st.spinner("Analyse profonde de la mémoire de la saga..."):
        
        # En version Pro, on ne coupe plus le texte. On prend TOUT.
        texte_integral = "\n".join([lire_tout(f) for f in fichiers])
        
        mission = f"""
        DIAGNOSTIC ULTRA-PRÉCIS : {nom_perso}. 
        Analyse l'évolution somatique et la souveraineté à travers tout le texte fourni.
        Vérifie la cohérence des relations et des fils d'aura.
        Signale toute contradiction avec les COMMANDEMENTS fournis.
        """

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nMANUSCRIT COMPLET : {texte_integral}"
        
        resultat = appel_ia_pro(prompt)
        st.session_state.resultat = resultat
        st.session_state.cible_actuelle = nom_perso

if "resultat" in st.session_state:
    st.divider()
    st.subheader(f"📖 Diagnostic Pro : {st.session_state.cible_actuelle}")
    st.markdown(st.session_state.resultat)
    
    if st.button(f"💾 Archiver dans l'onglet {st.session_state.cible_actuelle}"):
        onglet = connecter_et_obtenir_onglet(st.session_state.cible_actuelle)
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_now, st.session_state.resultat, "PRO ULTRA V16"])
            st.success("✅ Archive Pro synchronisée.")
