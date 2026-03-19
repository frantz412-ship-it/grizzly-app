import os
import re
import requests
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText
import io
import datetime

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

# --- 2. FONCTIONS TECHNIQUES (MODE CLOUD) ---
def connecter_gsheet():
    try:
        # On extrait les secrets dans un dictionnaire standard
        creds_dict = {k: v for k, v in st.secrets["gcp_service_account"].items()}
        
        if "private_key" in creds_dict:
            # On nettoie TOUT : les \n écrits, les espaces et les guillemets
            pk = creds_dict["private_key"]
            pk = pk.replace("\\n", "\n") # Change les \n texte en vrais sauts de ligne
            pk = pk.strip() # Enlève les espaces autour
            creds_dict["private_key"] = pk

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Utilisation directe du dictionnaire nettoyé
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID).sheet1
        
    except Exception as e:
        st.error(f"❌ Erreur PEM persistante : {e}")
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
            "temperature": 0.0
        }
        
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status() 
        data = r.json()
        return data["choices"][0]["message"]["content"]
            
    except Exception as e:
        return f"❌ Erreur IA : {str(e)}"

# --- 3. INTERFACE UTILISATEUR STREAMLIT ---

st.set_page_config(page_title="L'Archiviste V7.1", layout="wide")
st.title("🛡️ L'Archiviste : Mémoire de la Saga")

# Barre latérale
st.sidebar.header("📁 Sources & Historique")
fichiers = st.sidebar.file_uploader("Charger manuscrits", type=["pdf", "odt", "docx"], accept_multiple_files=True)
nom_perso = st.sidebar.selectbox("Personnage à traiter", ["Zack", "Léo", "Jonas", "Autyssé"])

if st.sidebar.button(f"📥 Charger Historique Cloud ({nom_perso})"):
    sheet = connecter_gsheet()
    if sheet:
        with st.spinner("Récupération de la dernière Bible..."):
            records = sheet.get_all_records()
            histo = next((r['Bible_Contenu'] for r in reversed(records) if r['Personnage'] == nom_perso), "Nouveau profil.")
            st.session_state.historique = histo
            st.sidebar.success("Dernière version chargée !")

# Zone principale
if fichiers:
    st.info(f"✅ {len(fichiers)} fichiers prêts pour l'analyse de {nom_perso}.")
    
    if st.button(f"🚀 Analyser & Mettre à jour {nom_perso}"):
        with st.spinner("L'archiviste traite vos chapitres..."):
            alias_map = {
                "Zack": ["Zack", "Gaz", "Loulou"],
                "Léo": ["Léo", "Moineau", "Leo"],
                "Jonas": ["Jonas", "Grizzly"],
                "Autyssé": ["Autyssé", "Auty", "Autysse"]
            }
            
            passages = []
            for f in fichiers:
                texte_brut = extraire_texte(f).replace("’", "'")
                lignes = texte_brut.split('\n')
                for ligne in lignes:
                    if any(re.search(r'\b' + re.escape(alias) + r'\b', ligne, re.IGNORECASE) for alias in alias_map[nom_perso]):
                        if len(ligne.strip()) > 50:
                            passages.append(ligne.strip())

            historique_existant = st.session_state.get('historique', "Pas d'historique connu.")
            contexte_manuscrit = "\n\n".join(passages[:25])
            
            prompt_final = f"{VERROU_SAGA}\n\nHISTO: {historique_existant}\n\nEXTRAITS: {contexte_manuscrit}\n\nMISSION: Mise à jour Bible."
            
            resultat = appel_ia(prompt_final)
            st.session_state.derniere_bible = resultat

if "derniere_bible" in st.session_state:
    st.divider()
    st.subheader(f"📖 Bible mise à jour : {nom_perso}")
    st.markdown(st.session_state.derniere_bible)
    
    if st.button("💾 Sauvegarder sur Google Sheets"):
        sheet = connecter_gsheet()
        if sheet:
            maintenant = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            sheet.append_row([nom_perso, maintenant, st.session_state.derniere_bible])
            st.success("✅ Synchronisation réussie !")
