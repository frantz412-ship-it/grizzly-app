import os
import re
import requests
import gspread
import json
import streamlit as st
import pdfplumber
import io
import datetime
from google.oauth2.service_account import Credentials
from docx import Document
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# --- 1. CONFIGURATION MAÎTRE ---
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

VERROU_SAGA = """
VÉRITÉS ABSOLUES À RESPECTER :
- JONAS est le GRIZZLY (Protecteur, Chasseur).
- LÉO est le MOINEAU (Guide, Fils de lumière).
- ZACK est GAZ (Survivant, Couple asexuel avec Jade).
- AUTYSSÉ est le CARTOGRAPHE (TSA, Profil Colonnes).
INTERDICTION : Ne jamais inventer de famille ou de lieux non cités dans le manuscrit.
"""

# --- 2. FONCTIONS TECHNIQUES ---

def connecter_gsheet():
    """Connexion via le bloc JSON complet pour éviter les erreurs PEM/Padding"""
    try:
        # On récupère le texte brut du JSON dans les secrets
        json_string = st.secrets["GCP_JSON_BRUT"]
        # Transformation en dictionnaire Python
        creds_info = json.loads(json_string, strict=False)
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        return client.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        st.error(f"❌ Erreur de connexion Cloud : {e}")
        return None

def extraire_texte(f):
    """Lecteur universel : PDF, DOCX et ODT"""
    try:
        if f.name.endswith(".pdf"):
            with pdfplumber.open(f) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
        elif f.name.endswith(".docx"):
            doc = Document(f)
            return "\n".join([p.text for p in doc.paragraphs])
        elif f.name.endswith(".odt"):
            return "\n".join([extractText(p) for p in load(f).getElementsByType(P)])
        return ""
    except Exception as e:
        st.error(f"Erreur de lecture sur {f.name} : {e}")
        return ""

def appel_ia(prompt):
    """Appel Mistral via le secret MISTRAL_API_KEY"""
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "mistral-large-latest", 
            "messages": [{"role": "user", "content": prompt}], 
            "temperature": 0.2
        }
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status() 
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Erreur IA : {str(e)}"

# --- 3. INTERFACE STREAMLIT ---

st.set_page_config(page_title="L'Archiviste V8.0", layout="wide")
st.title("🛡️ L'Archiviste : Mémoire de la Saga")

# Sidebar
st.sidebar.header("📁 Configuration")
fichiers = st.sidebar.file_uploader("Charger manuscrits", type=["pdf", "odt", "docx"], accept_multiple_files=True)

options_cible = ["Zack", "Léo", "Jonas", "Autyssé", "SAGA (Vue d'ensemble)"]
nom_perso = st.sidebar.selectbox("Cible de l'analyse", options_cible)

if st.sidebar.button(f"📥 Charger Historique ({nom_perso})"):
    sheet = connecter_gsheet()
    if sheet:
        with st.spinner("Récupération du Cloud..."):
            records = sheet.get_all_records()
            histo = next((r['Bible_Contenu'] for r in reversed(records) if r['Personnage'] == nom_perso), "Nouveau profil.")
            st.session_state.historique = histo
            st.sidebar.success("Historique chargé !")

# Traitement Principal
if fichiers:
    if st.button(f"🚀 Lancer l'analyse : {nom_perso}"):
        with st.spinner("Analyse en cours..."):
            
            # Gestion des passages selon la cible
            alias_map = {
                "Zack": ["Zack", "Gaz", "Loulou"],
                "Léo": ["Léo", "Moineau", "Leo"],
                "Jonas": ["Jonas", "Grizzly"],
                "Autyssé": ["Autyssé", "Auty", "Autysse"]
            }
            
            tous_extraits = []
            for f in fichiers:
                tous_extraits.append(extraire_texte(f).replace("’", "'"))
            
            texte_complet = "\n".join(tous_extraits)
            
            if nom_perso == "SAGA (Vue d'ensemble)":
                passages_cibles = texte_complet[:5000] # On prend les 5000 premiers caractères pour la vue globale
                mission = """
                MISSION : ANALYSE TRANSVERSALE DE LA SAGA.
                1. Thématiques : Reconstruction, Consentement, Froid.
                2. Monde : Règles de la Tribu, lieux marquants.
                3. Équilibre : Comment les 4 protagonistes interagissent-ils ici ?
                """
            else:
                lignes = texte_complet.split('\n')
                passages_cibles = [l.strip() for l in lignes if any(a.lower() in l.lower() for a in alias_map[nom_perso]) and len(l) > 40]
                passages_cibles = "\n".join(passages_cibles[:30])
                mission = f"""
                MISSION : PORTRAIT PSYCHOLOGIQUE DE {nom_perso}.
                1. État Somatique : Réactions du corps, sensorialité.
                2. Souveraineté : Limites, refus, reprises de contrôle.
                3. Évolution interne dans ces chapitres.
                """

            historique_existant = st.session_state.get('historique', "Pas d'historique connu.")
            
            prompt_final = f"""
            {VERROU_SAGA}
            ---
            HISTORIQUE PRÉCÉDENT :
            {historique_existant}
            ---
            EXTRAITS DU MANUSCRIT :
            {passages_cibles}
            ---
            {mission}
            """
            
            resultat = appel_ia(prompt_final)
            st.session_state.derniere_bible = resultat

# Affichage et Sauvegarde
if "derniere_bible" in st.session_state:
    st.divider()
    st.subheader(f"📖 Résultat pour : {nom_perso}")
    st.markdown(st.session_state.derniere_bible)
    
    if st.button("💾 Sauvegarder sur Google Sheets"):
        sheet = connecter_gsheet()
        if sheet:
            maintenant = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            sheet.append_row([nom_perso, maintenant, st.session_state.derniere_bible])
            st.success("✅ Synchronisation réussie !")
