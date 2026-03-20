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
PROTOCOLE DE DIAGNOSTIC (STRICT) :
1. INTERDICTION D'INVENTION : Ne déduis jamais une apparence (yeux, habits, cheveux) ou un passé si l'extrait ne le cite pas explicitement. Écris "Non mentionné".
2. MISSION DE DIAGNOSTIC : Ton rôle est de diagnostiquer les faits présents.
   - Observation : Ce qui est écrit.
   - Diagnostic : Ce que cela révèle sur l'état somatique ou la souveraineté.
3. VÉRITÉS FIXES :
   - AGES : Jonas (17 ans), Léo (15 ans), Zack (15 ans).
   - IDENTITÉ : Zackary (officiel), Zack (amis). "Gaz" est une INSULTE, pas un pouvoir.
   - VISIONS : Léo voit des "fils" [fil] d'auras. L'Ombre est une "ligne noire".
   - AURAS : Jonas (Brun), Zack (Rouge/Noir), Autyssé (Bleu).
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
            nouvel_onglet.append_row(["Date", "Diagnostic", "Type"])
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
            "temperature": 0.0 # Suppression de toute créativité
        }
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erreur IA : {e}"

# --- 3. INTERFACE ---

st.set_page_config(page_title="L'Archiviste V15.0", layout="wide")
st.title("🛡️ L'Archiviste : Diagnostic de la Saga")

st.sidebar.header("📁 Manuscrits")
fichiers = st.sidebar.file_uploader("Charger chapitres", type=["pdf", "docx", "odt"], accept_multiple_files=True)

options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "Jade", "SAGA"]
nom_perso = st.sidebar.selectbox("Cible du diagnostic", options_cible)

if fichiers and st.button(f"🚀 Établir Diagnostic : {nom_perso}"):
    with st.spinner(f"Analyse factuelle de {nom_perso}..."):
        
        texte_brut = "\n".join([lire_manuscrit(f) for f in fichiers])
        
        if nom_perso == "SAGA":
            mission = """
            DIAGNOSTIC SAGA :
            1. État des Fils : Santé des liens d'auras.
            2. Menace : Localisation et impact de l'Ombre (ligne noire).
            3. Souveraineté Collective : Capacité du groupe à résister à la Tribu.
            """
            contexte = texte_brut[:8000]
        else:
            mission = f"""
            DIAGNOSTIC FACTUEL : {nom_perso}.
            1. PHYSIQUE (OBSERVATION) : Uniquement ce qui est explicitement décrit. (Si rien : "Information absente").
            2. ÉTAT SOMATIQUE (DIAGNOSTIC) : Réaction du corps aux événements (froid, peur, contact).
            3. RELATIONS (DIAGNOSTIC) : État du lien avec les autres (Fils de Lumière, Grizzly, Jade, Autyssé).
            4. SOUVERAINETÉ (DIAGNOSTIC) : Moments où le personnage reprend son territoire intérieur.
            5. FIL D'AURA : Couleur et proximité de la ligne noire (Ombre).
            """
            lignes = texte_brut.split('\n')
            contexte = "\n".join([l for l in lignes if nom_perso.lower() in l.lower()][:50])

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nEXTRAITS : {contexte}"
        
        resultat = appel_ia(prompt)
        st.session_state.resultat = resultat
        st.session_state.cible_actuelle = nom_perso

if "resultat" in st.session_state:
    st.divider()
    st.subheader(f"📖 Diagnostic Certifié : {st.session_state.cible_actuelle}")
    st.markdown(st.session_state.resultat)
    
    if st.button(f"💾 Archiver dans l'onglet {st.session_state.cible_actuelle}"):
        onglet = connecter_et_obtenir_onglet(st.session_state.cible_actuelle)
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_now, st.session_state.resultat, "Diagnostic V15"])
            st.success(f"✅ Diagnostic de {st.session_state.cible_actuelle} enregistré.")
