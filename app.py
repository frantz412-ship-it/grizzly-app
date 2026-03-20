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

# --- 1. CONFIGURATION ET COMMANDEMENTS DE FER ---
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

VERROU_SAGA = """
COMMANDEMENTS ABSOLUS DE LA SAGA (À RESPECTER STRICTEMENT) :

1. LA MÉCANIQUE DES FILS DE LÉO :
   - LÉO est le "Fils [fis] de Lumière" (Identité).
   - LÉO voit et ressent des "fils [fil]" (Liens/Auras). 
   - Chaque personnage est un FIL de couleur spécifique dans la vision de Léo :
     * JONAS : Fil de terre/brun (Grizzly).
     * ZACK : Fil rouge/noir (Éclair/Aura flamboyante).
     * AUTYSSÉ : Fil bleu/froid (Structure/Colonnes).
   - CES FILS sont le lien naturel et rapide qui unit le groupe. Léo les perçoit par CONCENTRATION.
   - [FEW-SHOT EXEMPLE] :
     ❌ INCORRECT : "Léo perd son lien de parenté (fils) avec Jonas."
     ✅ CORRECT : "Léo se concentre pour ressentir le fil brun de Jonas."

2. DISTINCTION VICTIME / AGRESSEUR (ZACK) :
   - Le refrain "Gaz... gaz... gaz..." est une INSULTE de la TRIBU. Zack le SUBIT.
   - [FEW-SHOT EXEMPLE] :
     ❌ INCORRECT : "Zack s'amuse à répéter son surnom Gaz."
     ✅ CORRECT : "Zack se fige, blessé par le refrain 'Gaz...' de ses agresseurs."

3. PORTRAITS PHYSIQUES (MIS À JOUR) :
   - JONAS : 17 ans, brun, pantalons trop larges, regard fatigué. Fils de la Survie.
   - LÉO : 15 ans (Correction), cheveux presque blancs, regard Fils de Lumière. Guide.
   - ZACK : 15 ans, petit, éclair noir, posture fœtale, pierre-louveteau. Enfant de trop.
   - AUTYSSÉ : Physique rigide, démarche cadencée, regard analytique. Fils de la Structure.
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
        st.error(f"❌ Erreur Sheets : {e}")
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
            "temperature": 0.1 
        }
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erreur IA : {e}"

# --- 3. INTERFACE ---

st.set_page_config(page_title="L'Archiviste V12.0", layout="wide")
st.title("🛡️ L'Archiviste : Gardien des Fils (Age Sync)")

# Sidebar
st.sidebar.header("📁 Documents")
fichiers = st.sidebar.file_uploader("Charger chapitres", type=["pdf", "docx", "odt"], accept_multiple_files=True)

options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "SAGA"]
nom_perso = st.sidebar.selectbox("Cible de l'analyse", options_cible)

if fichiers and st.button(f"🚀 Analyser : {nom_perso}"):
    with st.spinner(f"L'Archiviste synchronise les fils de {nom_perso}..."):
        
        texte_brut = "\n".join([lire_manuscrit(f) for f in fichiers])
        
        if nom_perso == "SAGA":
            mission = "ANALYSE TRANSVERSALE : Cohérence des auras et des liens (fils). Respecter l'âge de 15 ans pour Léo et Zack."
            contexte = texte_brut[:7000]
        else:
            mission = f"PORTRAIT PSYCHOLOGIQUE ET PHYSIQUE DE {nom_perso}. Analyse somatique (15 ans pour Léo/Zack, 17 pour Jonas)."
            lignes = texte_brut.split('\n')
            contexte = "\n".join([l for l in lignes if nom_perso.lower() in l.lower()][:40])

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nEXTRAITS : {contexte}"
        
        resultat = appel_ia(prompt)
        st.session_state.resultat = resultat
        st.session_state.cible_actuelle = nom_perso

# Affichage et Sauvegarde
if "resultat" in st.session_state:
    st.divider()
    st.subheader(f"📖 Fiche synchronisée : {st.session_state.cible_actuelle}")
    st.markdown(st.session_state.resultat)
    
    if st.button(f"💾 Sauvegarder dans l'onglet {st.session_state.cible_actuelle}"):
        onglet = connecter_et_obtenir_onglet(st.session_state.cible_actuelle)
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_now, st.session_state.resultat, "V12 Age Sync"])
            st.success(f"✅ Dossier {st.session_state.cible_actuelle} mis à jour avec succès !")
