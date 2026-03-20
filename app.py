import os
import json
import requests
import gspread
import streamlit as st
import pdfplumber
import datetime
from google.oauth2.service_account import Credentials
from docx import Document
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# --- 1. LE CODE SOURCE DE LA VÉRITÉ (VERROUS) ---
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

VERROU_SAGA = """
COMMANDEMENTS DE FIDÉLITÉ ABSOLUE :

1. RÈGLE D'OR : Ne jamais inventer. Si une information (couleur, émotion, passé) n'est pas explicitement dans l'extrait ou dans ce verrou, écris "Non mentionné".
2. VISION DE LÉO (15 ans) : 
   - Il est le "Fils [fis] de Lumière". Il utilise sa concentration pour voir les "fils [fil]" (liens d'auras).
   - JONAS (17 ans) : Fil brun/terre. 
   - ZACK (15 ans) : Fil rouge/noir (Aura flamboyante).
   - AUTYSSÉ : Fil bleu/froid.
3. CONTEXTE ET ENVIRONNEMENT : Analyse toujours comment le lieu (froid, rivière, forêt, Tribu) dicte la posture du personnage.
4. LE STIGMATE DE ZACK : Le mot "Gaz" est une insulte de la Tribu. Zack ne possède pas de "pouvoir de gaz", il subit une réification. Son rire est une défense somatique.
"""

# --- 2. FONCTIONS TECHNIQUES ---

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
            nouvel_onglet = ss.add_worksheet(title=nom_onglet, rows="1000", cols="5")
            nouvel_onglet.append_row(["Date", "Analyse", "Type"])
            return nouvel_onglet
    except Exception as e:
        st.error(f"Erreur Sheets : {e}")
        return None

def lire_manuscrit(f):
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
        st.error(f"Erreur lecture {f.name} : {e}")
        return ""

def appel_ia(prompt):
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "mistral-large-latest", 
            "messages": [{"role": "user", "content": prompt}], 
            "temperature": 0.0 # Zéro fantaisie, précision chirurgicale
        }
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erreur IA : {e}"

# --- 3. INTERFACE ---

st.set_page_config(page_title="L'Archiviste V13.0", layout="wide")
st.title("🛡️ L'Archiviste : Fidélité au Récit")

st.sidebar.header("📁 Manuscrits")
fichiers = st.sidebar.file_uploader("Charger chapitres", type=["pdf", "docx", "odt"], accept_multiple_files=True)

options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "Jade", "SAGA"]
nom_perso = st.sidebar.selectbox("Cible de l'étude", options_cible)

if fichiers and st.button(f"🚀 Générer Fiche Réelle : {nom_perso}"):
    with st.spinner(f"Analyse contextuelle de {nom_perso}..."):
        
        texte_brut = "\n".join([lire_manuscrit(f) for f in fichiers])
        
        if nom_perso == "SAGA":
            mission = """
            ANALYSE DE COHÉRENCE SAGA.
            1. État du monde : Climat, menace, ressources.
            2. Dynamique des fils : État des liens d'auras entre les personnages.
            3. Thèmes : Reconstruction et Consentement.
            INTERDICTION : Ne pas inventer d'événements non décrits.
            """
            contexte = texte_brut[:8000]
        else:
            mission = f"""
            FICHE RÉELLE DE PERSONNAGE : {nom_perso}.
            1. APPARENCE PHYSIQUE : Uniquement ce qui est décrit (vêtements, traits, âge).
            2. ÉTAT SOMATIQUE : Réaction du corps à l'environnement (froid, peur, présence des autres).
            3. SOUVERAINETÉ : Analyse des moments où le personnage reprend son territoire intérieur.
            4. FIL D'AURA : Couleur et état perçu par Léo.
            IMPORTANT : Si un détail n'est pas présent, indique 'Information absente du texte'.
            """
            lignes = texte_brut.split('\n')
            contexte = "\n".join([l for l in lignes if nom_perso.lower() in l.lower()][:50])

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nEXTRAITS DU MANUSCRIT : {contexte}"
        
        resultat = appel_ia(prompt)
        st.session_state.resultat = resultat
        st.session_state.cible_actuelle = nom_perso

if "resultat" in st.session_state:
    st.divider()
    st.subheader(f"📖 Fiche Officielle : {st.session_state.cible_actuelle}")
    st.markdown(st.session_state.resultat)
    
    if st.button(f"💾 Archiver dans l'onglet {st.session_state.cible_actuelle}"):
        onglet = connecter_et_obtenir_onglet(st.session_state.cible_actuelle)
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_now, st.session_state.resultat, "Fiche Réelle V13"])
            st.success(f"✅ La fiche de {st.session_state.cible_actuelle} a été certifiée et enregistrée.")
