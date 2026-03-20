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

# --- 1. CONFIGURATION ET COMMANDEMENTS (FEW-SHOT INCLUS) ---
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

VERROU_SAGA = """
COMMANDEMENTS DE LA SAGA (À RESPECTER STRICTEMENT) :

1. NUANCE LINGUISTIQUE (RÈGLE DU FILS) :
   - "Le Fils" [fiss] : Identité de Léo (Fils de Lumière), de Jonas (Fils de la Survie), etc.
   - "Les fils" [fil] : Liens invisibles, boussoles mentales, fils de pensée.
   - [FEW-SHOT EXEMPLE] :
     ❌ INCORRECT : "Léo est perdu car il n'est plus le Fils de Lumière."
     ✅ CORRECT : "Léo est perdu car ses fils de pensée (concentration) se cassent."

2. PERSPECTIVE VICTIME/AGRESSEUR :
   - Le refrain "Gaz... gaz... gaz..." est une INSULTE de la TRIBU.
   - Zack (Gaz) SUBIT ce mot comme une blessure. Il ne le dit jamais de lui-même.
   - [FEW-SHOT EXEMPLE] :
     ❌ INCORRECT : "Zack commence à dire Gaz... gaz... gaz..."
     ✅ CORRECT : "Zack se fige en entendant les moqueries 'Gaz... gaz...' de la Tribu."

3. PORTRAITS PHYSIQUES :
   - JONAS : 17 ans, brun, pantalons trop larges, regard fatigué.
   - LÉO : 17 ans, cheveux presque blancs (Fils de Lumière), guide.
   - ZACK : 15 ans, petit, éclair noir, posture fœtale.
   - AUTYSSÉ : Physique rigide, regard 'Colonnes'.
"""

# --- 2. FONCTIONS TECHNIQUES ---

def connecter_et_obtenir_onglet(nom_onglet):
    """Gère la connexion et crée l'onglet s'il n'existe pas"""
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
        st.error(f"❌ Erreur Google Sheets : {e}")
        return None

def lire_manuscrit(f):
    """Supporte PDF, DOCX et ODT"""
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
        st.error(f"Erreur sur {f.name} : {e}")
        return ""

def appel_ia(prompt):
    """Interroge l'IA avec les contraintes strictes"""
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "mistral-large-latest", 
            "messages": [{"role": "user", "content": prompt}], 
            "temperature": 0.1 # Température basse pour plus de rigueur
        }
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erreur IA : {e}"

# --- 3. INTERFACE UTILISATEUR ---

st.set_page_config(page_title="L'Archiviste V10.0", layout="wide")
st.title("🛡️ L'Archiviste : Gardien de la Saga")

# Sidebar
st.sidebar.header("📁 Documents")
fichiers = st.sidebar.file_uploader("Charger chapitres", type=["pdf", "docx", "odt"], accept_multiple_files=True)

options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "SAGA"]
nom_perso = st.sidebar.selectbox("Cible de l'analyse", options_cible)

# Analyse
if fichiers and st.button(f"🚀 Lancer l'analyse : {nom_perso}"):
    with st.spinner(f"L'Archiviste vérifie les fils de {nom_perso}..."):
        
        texte_brut = "\n".join([lire_manuscrit(f) for f in fichiers])
        
        if nom_perso == "SAGA":
            mission = """
            MISSION : ANALYSE TRANSVERSALE. 
            Vérifier la cohérence du monde et l'évolution des thèmes.
            RAPPEL : Léo est le guide via les fils (liens), ne pas confondre avec son identité de Fils.
            """
            contexte = texte_brut[:7000]
        else:
            mission = f"""
            MISSION : PORTRAIT PSYCHOLOGIQUE ET PHYSIQUE DE {nom_perso}.
            Analyse l'état somatique et la souveraineté.
            RAPPEL : Si c'est Zack, traite l'insulte 'Gaz' comme une agression externe.
            """
            # Extraction des passages clés
            lignes = texte_brut.split('\n')
            contexte = "\n".join([l for l in lignes if nom_perso.lower() in l.lower()][:40])

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nEXTRAITS : {contexte}"
        
        resultat = appel_ia(prompt)
        st.session_state.resultat = resultat
        st.session_state.cible_actuelle = nom_perso

# Affichage et Sauvegarde
if "resultat" in st.session_state:
    st.divider()
    st.subheader(f"📖 Analyse archivée : {st.session_state.cible_actuelle}")
    st.markdown(st.session_state.resultat)
    
    if st.button(f"💾 Sauvegarder dans l'onglet {st.session_state.cible_actuelle}"):
        onglet = connecter_et_obtenir_onglet(st.session_state.cible_actuelle)
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_now, st.session_state.resultat, "Analyse Verrouillée"])
            st.success(f"✅ Dossier {st.session_state.cible_actuelle} mis à jour !")
