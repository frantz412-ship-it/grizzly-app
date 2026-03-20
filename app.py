import os
import json
import requests
import gspread
import streamlit as st
import pdfplumber
import datetime
from google.oauth2.service_account import Credentials
from docx import Document

# --- 1. CONFIGURATION ET VERROUS ---
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

# Ce bloc est envoyé à l'IA pour garantir la cohérence
VERROU_SAGA = """
VÉRITÉS ABSOLUES ET PHYSIQUES :
- JONAS (Grizzly) : 17 ans, brun, regard 'fatigué raide', pantalons trop larges. Fils de la Survie.
- LÉO (Moineau) : 17 ans, cheveux clairs (presque blancs), Fils de Lumière. Guide.
- ZACK (Gaz) : 15 ans, plus petit, Éclair noir, posture fœtale. Enfant de trop.
- AUTYSSÉ (Cartographe) : Physique rigide, regard analytique. Fils de la Structure.

NUANCE LINGUISTIQUE CRUCIALE :
1. "Le Fils" (prononcé [fiss]) : Désigne l'identité, l'enfant, le garçon (ex: Léo est le Fils de Lumière).
2. "Les fils" (prononcé [fil]) : Désigne les liens invisibles, les cordes, ou les fils de pensée que Léo manipule.
NE JAMAIS CONFONDRE LES DEUX DANS L'ANALYSE.
"""

# --- 2. FONCTIONS DE CONNEXION ---

def connecter_et_obtenir_onglet(nom_onglet):
    """Connexion et création automatique de l'onglet si manquant"""
    try:
        json_info = json.loads(st.secrets["GCP_JSON_BRUT"], strict=False)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json_info, scopes=scope)
        client = gspread.authorize(creds)
        ss = client.open_by_key(SHEET_ID)
        
        try:
            return ss.worksheet(nom_onglet)
        except gspread.exceptions.WorksheetNotFound:
            # Création de l'onglet s'il n'existe pas
            nouvel_onglet = ss.add_worksheet(title=nom_onglet, rows="500", cols="10")
            nouvel_onglet.append_row(["Date", "Analyse", "Type"])
            return nouvel_onglet
    except Exception as e:
        st.error(f"❌ Erreur Google Sheets : {e}")
        return None

def appel_ia(prompt):
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "mistral-large-latest", 
            "messages": [{"role": "user", "content": prompt}], 
            "temperature": 0.2
        }
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erreur IA : {e}"

# --- 3. INTERFACE ---

st.set_page_config(page_title="L'Archiviste V9.0", layout="wide")
st.title("🛡️ L'Archiviste : Mémoire de la Saga")

# Sidebar
options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "SAGA"]
nom_perso = st.sidebar.selectbox("Entité à analyser", options_cible)
fichiers = st.sidebar.file_uploader("Charger manuscrits", type=["pdf", "docx"], accept_multiple_files=True)

# Logique d'analyse
if fichiers and st.button(f"🚀 Analyser {nom_perso}"):
    with st.spinner("L'Archiviste parcourt les fils du récit..."):
        
        # Extraction texte
        texte_complet = ""
        for f in fichiers:
            if f.name.endswith(".pdf"):
                with pdfplumber.open(f) as pdf:
                    texte_complet += "\n".join([p.extract_text() or "" for p in pdf.pages])
            else:
                doc = Document(f)
                texte_complet += "\n".join([p.text for p in doc.paragraphs])

        # Construction de la mission
        if nom_perso == "SAGA":
            mission = "ANALYSE GLOBALE : Thèmes (Reconstruction, Fils invisibles), Monde et Cohérence."
            contexte = texte_complet[:6000]
        else:
            mission = f"PORTRAIT PHYSIQUE ET PSYCHOLOGIQUE DE {nom_perso}. Analyse son état somatique et sa souveraineté."
            # Filtre simple pour garder les passages pertinents
            lignes = texte_complet.split('\n')
            contexte = "\n".join([l for l in lignes if nom_perso.lower() in l.lower()][:40])

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nEXTRAITS : {contexte}"
        
        resultat = appel_ia(prompt)
        st.session_state.resultat = resultat

# Affichage et Sauvegarde
if "resultat" in st.session_state:
    st.markdown(f"### 📖 Analyse de {nom_perso}")
    st.write(st.session_state.resultat)
    
    if st.button("💾 Sauvegarder dans l'onglet dédié"):
        onglet = connecter_et_obtenir_onglet(nom_perso)
        if onglet:
            date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_str, st.session_state.resultat, "Analyse Complète"])
            st.success(f"✅ Enregistré dans l'onglet '{nom_perso}' !")
