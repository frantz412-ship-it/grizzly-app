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

# --- 1. CONFIGURATION ET COMMANDEMENTS DE LA SAGA ---
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

VERROU_SAGA = """
COMMANDEMENTS DE FIDÉLITÉ (V14) :

1. L'IDENTITÉ DE ZACK :
   - Nom officiel : Zackary. 
   - Préférence : Il préfère se faire appeler ZACK par ses amis (Jonas, Léo, Jade, Autyssé).
   - Stigmate : "Gaz" est une insulte de la Tribu. Zack ne l'utilise jamais pour lui-même.

2. LES VISIONS DE LÉO (15 ans) :
   - L'OMBRE : Elle apparaît sous la forme d'une LIGNE NOIRE dans les fils de vision de Léo. C'est la menace, la corruption ou le vide.
   - LES FILS (Liens) : Jonas (Brun/Terre), Zack (Rouge/Noir), Autyssé (Bleu/Froid).
   - [FEW-SHOT EXEMPLE] :
     ❌ INCORRECT : "Léo voit une ligne noire dans son aura, c'est son passé."
     ✅ CORRECT : "Léo perçoit l'Ombre comme une ligne noire qui tente de grignoter les fils du groupe."

3. CARTOGRAPHIE DES RELATIONS :
   - JONAS / ZACK : Relation protecteur/protégé. Zack admire Jonas mais craint l'intrusion physique.
   - LÉO / ZACK : Relation guide/suiveur. Zack suit la lumière de Léo mais craint de rompre le fil.
   - AUTYSSÉ / ZACK : Opposition Structure vs Chaos. Autyssé analyse, Zack ressent. Tension et besoin mutuel.
   - ZACK / JADE : Couple asexuel. Bastion de sécurité absolue et de souveraineté.

4. PHYSIQUE :
   - Jonas (17 ans), Léo (15 ans), Zack (15 ans). Respecter ces âges dans les analyses somatiques.
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
            "temperature": 0.0 # Précision maximale
        }
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erreur IA : {e}"

# --- 3. INTERFACE ---

st.set_page_config(page_title="L'Archiviste V14.0", layout="wide")
st.title("🛡️ L'Archiviste : L'Ombre et les Fils")

st.sidebar.header("📁 Manuscrits")
fichiers = st.sidebar.file_uploader("Charger chapitres", type=["pdf", "docx", "odt"], accept_multiple_files=True)

options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "Jade", "SAGA"]
nom_perso = st.sidebar.selectbox("Cible de l'analyse", options_cible)

if fichiers and st.button(f"🚀 Générer Fiche Complète : {nom_perso}"):
    with st.spinner(f"Analyse des relations pour {nom_perso}..."):
        
        texte_brut = "\n".join([lire_manuscrit(f) for f in fichiers])
        
        if nom_perso == "SAGA":
            mission = """
            ANALYSE DE LA SAGA :
            1. Présence de l'Ombre (la ligne noire dans les visions).
            2. Solidité des liens (fils) entre les membres du groupe.
            3. Évolution de la souveraineté collective face à la Tribu.
            """
            contexte = texte_brut[:8000]
        else:
            mission = f"""
            FICHE PERSONNAGE RÉELLE : {nom_perso}.
            1. PHYSIQUE ET SOMATIQUE : État du corps (Respecter l'âge et les raideurs).
            2. RELATIONS : Analyse du lien spécifique avec les autres membres du groupe (Jonas, Léo, Zack, Autyssé, Jade).
            3. VISION DES FILS : État de son fil d'aura et proximité de l'Ombre (ligne noire).
            4. SOUVERAINETÉ : Moments de contrôle intérieur.
            NOTE : Zack préfère 'Zack' pour ses amis. Zackary est son nom officiel.
            """
            lignes = texte_brut.split('\n')
            contexte = "\n".join([l for l in lignes if nom_perso.lower() in l.lower()][:50])

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nEXTRAITS : {contexte}"
        
        resultat = appel_ia(prompt)
        st.session_state.resultat = resultat
        st.session_state.cible_actuelle = nom_perso

if "resultat" in st.session_state:
    st.divider()
    st.subheader(f"📖 Fiche Certifiée : {st.session_state.cible_actuelle}")
    st.markdown(st.session_state.resultat)
    
    if st.button(f"💾 Archiver dans l'onglet {st.session_state.cible_actuelle}"):
        onglet = connecter_et_obtenir_onglet(st.session_state.cible_actuelle)
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_now, st.session_state.resultat, "V14 - Ombre & Relations"])
            st.success(f"✅ Analyse de {st.session_state.cible_actuelle} enregistrée.")
