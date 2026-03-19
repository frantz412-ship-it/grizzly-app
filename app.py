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
from dotenv import load_dotenv

# --- 1. CHARGEMENT & CONFIGURATION ---
load_dotenv()

# ID de votre feuille Google Sheet (déjà configuré)
SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

# Verrou de vérité pour empêcher l'IA d'inverser les personnages
VERROU_SAGA = """
VÉRITÉS ABSOLUES À RESPECTER :
- JONAS est le GRIZZLY (Protecteur, Chasseur).
- LÉO est le MOINEAU (Guide, Fils de lumière).
- ZACK est GAZ (Survivant, Couple asexuel avec Jade).
- AUTYSSÉ est le CARTOGRAPHE (TSA, Profil Colonnes).
INTERDICTION : Ne jamais inventer de soeur (Mira) ou de lieux non cités.
"""

# --- 2. FONCTIONS TECHNIQUES ---

def connecter_gsheet():
    """Établit la connexion avec Google Sheets via credentials.json"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Assurez-vous que credentials.json est dans le dossier grizzly-app
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        st.error(f"❌ Erreur de connexion Cloud : {e}")
        return None

def extraire_texte(f):
    """Lit le contenu des fichiers PDF, DOCX et ODT"""
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
    """Envoie la requête à Mistral avec gestion d'erreurs robuste"""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return "❌ Clé API manquante dans le fichier .env"
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "mistral-large-latest", 
        "messages": [{"role": "user", "content": prompt}], 
        "temperature": 0.0
    }
    
    try:
        r = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status() # Déclenche une erreur si 401, 404, 500
        data = r.json()
        
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            return f"⚠️ Format de réponse inconnu : {data}"
            
    except requests.exceptions.HTTPError as http_err:
        if r.status_code == 401:
            return "❌ Erreur 401 : Votre clé Mistral est invalide ou mal copiée dans le fichier .env."
        return f"❌ Erreur HTTP {r.status_code} : {r.text}"
    except Exception as e:
        return f"❌ Erreur technique : {str(e)}"

# --- 3. INTERFACE STREAMLIT ---

st.set_page_config(page_title="L'Archiviste V6.7", layout="wide")
st.title("🛡️ L'Archiviste : Gestion de Saga")

# Diagnostic de clé (visible uniquement pour debug)
with st.expander("🔍 État du système"):
    key = os.getenv("MISTRAL_API_KEY", "")
    st.write(f"Clé API chargée : {'✅ Oui' if key else '❌ Non'}")
    st.write(f"Longueur de la clé : {len(key)} caractères")

# Barre latérale
st.sidebar.header("📁 Sources & Historique")
fichiers = st.sidebar.file_uploader("Charger manuscrits (PDF, ODT, DOCX)", accept_multiple_files=True)
nom_perso = st.sidebar.selectbox("Personnage à analyser", ["Zack", "Léo", "Jonas", "Autyssé"])

if st.sidebar.button(f"📥 Récupérer Bible Cloud ({nom_perso})"):
    sheet = connecter_gsheet()
    if sheet:
        records = sheet.get_all_records()
        histo = next((r['Bible_Contenu'] for r in reversed(records) if r['Personnage'] == nom_perso), "Nouveau profil.")
        st.session_state.historique = histo
        st.sidebar.success("Dernière version chargée !")

# Zone principale
if fichiers:
    st.info(f"{len(fichiers)} fichiers chargés. Prêt pour l'analyse de {nom_perso}.")
    
    if st.button(f"🚀 Lancer l'Analyse Evolutive ({nom_perso})"):
        with st.spinner("Lecture des fichiers et analyse en cours..."):
            # Extraction du texte
            alias_map = {
                "Zack": ["Zack", "Gaz", "Loulou"],
                "Léo": ["Léo", "Moineau", "Leo"],
                "Jonas": ["Jonas", "Grizzly", "Jojo"],
                "Autyssé": ["Autyssé", "Auty", "Autysse"]
            }
            
            passages = []
            for f in fichiers:
                texte_complet = extraire_texte(f).replace("’", "'")
                # On cherche les paragraphes qui contiennent le nom ou les alias
                lignes = texte_complet.split('\n')
                for ligne in lignes:
                    if any(re.search(r'\b' + re.escape(alias) + r'\b', ligne, re.IGNORECASE) for alias in alias_map[nom_perso]):
                        if len(ligne.strip()) > 50: # On ignore les lignes trop courtes
                            passages.append(ligne.strip())

            # Préparation du prompt
            historique_existant = st.session_state.get('historique', "Aucun historique disponible.")
            contexte_manuscrit = "\n\n".join(passages[:25]) # On limite pour ne pas saturer l'IA
            
            prompt_final = f"""
            {VERROU_SAGA}
            
            CONTEXTE HISTORIQUE (Bible précédente) :
            {historique_existant}
            
            NOUVEAUX ÉLÉMENTS DU MANUSCRIT :
            {contexte_manuscrit}
            
            MISSION :
            Tu es l'archiviste expert. Mets à jour la Bible de {nom_perso}. 
            Analyse son évolution psychologique, ses traumas et sa montée en souveraineté.
            Structure ta réponse par sections : 1. Origine, 2. État Somatique, 3. Évolution Narrative.
            """
            
            resultat = appel_ia(prompt_final)
            st.session_state.derniere_bible = resultat

# Affichage des résultats
if "derniere_bible" in st.session_state:
    st.divider()
    st.subheader(f"📖 Bible mise à jour : {nom_perso}")
    st.markdown(st.session_state.derniere_bible)
    
    if st.button("💾 Envoyer cette version sur Google Sheets"):
        sheet = connecter_gsheet()
        if sheet:
            maintenant = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            sheet.append_row([nom_perso, maintenant, st.session_state.derniere_bible])
            st.success("Synchronisation avec le Cloud réussie !")
