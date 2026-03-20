import os
import json
import datetime

import streamlit as st
import gspread
import pdfplumber
from google.oauth2.service_account import Credentials
from docx import Document
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# Nouveau SDK Gemini
from google import genai
from google.genai import types

# --- 1. CONFIGURATION PRO ---

SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

# Configuration de Gemini via google-genai
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    api_key_env = os.getenv("GEMINI_API_KEY")
    if not api_key_env:
        st.error("Clé GEMINI_API_KEY manquante (st.secrets ou .env).")
    client = genai.Client(api_key=api_key_env)

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
    """Connexion à Google Sheets + création d'onglet si nécessaire."""
    try:
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
            nouvel_onglet.append_row(["Date", "Diagnostic Pro", "Type"])
            return nouvel_onglet
    except Exception as e:
        st.error(f"Erreur Sheets : {e}")
        return None

def lire_tout(f):
    """Lit PDF, DOCX ou ODT et renvoie tout le texte concaténé."""
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

def appel_ia_pro(prompt: str) -> str:
    """
    Analyse profonde via Gemini (google-genai).
    Modèle : gemini-2.0-pro si disponible, sinon gemini-2.0-flash.
    """
    model_name = "gemini-2.0-pro"
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=8192,
            ),
        )
        return response.text or ""
    except Exception:
        # fallback flash si le pro n'est pas dispo sur le compte
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=8192,
                ),
            )
            return response.text or ""
        except Exception as e:
            return f"❌ Erreur Gemini (Archiviste PRO ULTRA) : {e}"

# --- 3. INTERFACE ---

st.set_page_config(page_title="L'Archiviste PRO ULTRA", layout="wide")
st.title("🛡️ L'Archiviste : Mode Pro (2M Tokens, Gemini SDK)")

fichiers = st.sidebar.file_uploader(
    "Charger l'intégralité de la Saga",
    type=["pdf", "docx", "odt"],
    accept_multiple_files=True,
)
options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "Jade", "SAGA"]
nom_perso = st.sidebar.selectbox("Cible du Diagnostic Profond", options_cible)

if fichiers and st.button(f"🔍 Lancer Diagnostic Pro : {nom_perso}"):
    with st.spinner("Analyse profonde de la mémoire de la saga..."):
        # Version Pro : on prend TOUT
        texte_integral = "\n".join([lire_tout(f) for f in fichiers])

        mission = f"""
        DIAGNOSTIC ULTRA-PRÉCIS : {nom_perso}. 
        Analyse l'évolution somatique et la souveraineté à travers tout le texte fourni.
        Vérifie la cohérence des relations et des fils d'aura.
        Signale toute contradiction avec les COMMANDEMENTS fournis dans une section finale "ÉCARTS PAR RAPPORT AU CANON".
        Si une information n'est pas clairement présente dans le manuscrit, écris : "Non mentionné dans le manuscrit." sans inventer.
        """

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nMANUSCRIT COMPLET :\n{texte_integral}"

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
            onglet.append_row(
                [date_now, st.session_state.resultat, "PRO ULTRA V16 (Gemini SDK)"]
            )
            st.success("✅ Archive Pro synchronisée.")
