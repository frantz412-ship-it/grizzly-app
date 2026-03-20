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

# --- 1. CONFIGURATION ET VÉRITÉS ABSOLUES ---
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

VERROU_SAGA = """
VÉRITÉS ABSOLUES ET PHYSIQUES :
- JONAS (Grizzly) : 17 ans, brun, regard 'fatigué raide', pantalons trop larges. Fils de la Survie.
- LÉO (Moineau) : 17 ans, cheveux clairs (presque blancs), Fils de Lumière. Guide.
- ZACK (Gaz) : 15 ans, plus petit, Éclair noir, posture fœtale. Enfant de trop.
- AUTYSSÉ (Cartographe) : Physique rigide, regard analytique. Fils de la Structure.

NUANCE LINGUISTIQUE CRUCIALE :
1. "Le Fils" (prononcé [fiss]) : Désigne l'identité, l'enfant (ex: Léo est le Fils de Lumière).
2. "Les fils" (prononcé [fil]) : Désigne les liens invisibles, les cordes, ou les fils de pensée que Léo manipule.
INTERDICTION : Ne jamais confondre l'identité du personnage et ses outils de pensée.
"""

# --- 2. FONCTIONS TECHNIQUES ---

def connecter_et_obtenir_onglet(nom_onglet):
    """Connexion et création d'onglet si manquant"""
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
        st.error(f"❌ Erreur de connexion : {e}")
        return None

def lire_manuscrit(f):
    """Lecteur universel : PDF, DOCX et ODT"""
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
st.sidebar.header("📁 Documents")
fichiers = st.sidebar.file_uploader("Charger manuscrits", type=["pdf", "docx", "odt"], accept_multiple_files=True)

options_cible = ["Jonas", "Léo", "Zack", "Autyssé", "SAGA"]
nom_perso = st.sidebar.selectbox("Cible de l'analyse", options_cible)

# Analyse
if fichiers and st.button(f"🚀 Lancer l'analyse : {nom_perso}"):
    with st.spinner(f"L'Archiviste étudie les fils de {nom_perso}..."):
        
        texte_brut = "\n".join([lire_manuscrit(f) for f in fichiers])
        
        if nom_perso == "SAGA":
            mission = "ANALYSE TRANSVERSALE : Cohérence du monde, thèmes (Reconstruction) et dynamique du groupe."
            contexte = texte_brut[:7000]
        else:
            mission = f"PORTRAIT PSYCHOLOGIQUE ET PHYSIQUE DE {nom_perso}. Analyse son état somatique et sa souveraineté."
            # On cherche les passages où le nom ou l'alias apparaît
            lignes = texte_brut.split('\n')
            contexte = "\n".join([l for l in lignes if nom_perso.lower() in l.lower()][:40])

        prompt = f"{VERROU_SAGA}\n\nMISSION : {mission}\n\nEXTRAITS : {contexte}"
        
        resultat = appel_ia(prompt)
        st.session_state.resultat = resultat
        st.session_state.cible_actuelle = nom_perso

# Affichage et Sauvegarde
if "resultat" in st.session_state:
    st.divider()
    st.subheader(f"📖 Résultat : {st.session_state.cible_actuelle}")
    st.markdown(st.session_state.resultat)
    
    if st.button(f"💾 Sauvegarder dans l'onglet {st.session_state.cible_actuelle}"):
        onglet = connecter_et_obtenir_onglet(st.session_state.cible_actuelle)
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_now, st.session_state.resultat, "Analyse"])
            st.success(f"✅ Analyse de {st.session_state.cible_actuelle} synchronisée !")
