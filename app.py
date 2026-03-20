import os
import re
import json
import datetime

import streamlit as st
import pdfplumber
from docx import Document
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

import gspread
from google.oauth2.service_account import Credentials

# SDK Gemini 2.0/3
from google import genai
from google.genai import types

# ==========================================
# 0. CONFIG GEMINI (NUAGE)
# ==========================================

if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    api_key_env = os.getenv("GEMINI_API_KEY")
    if not api_key_env:
        st.error("GEMINI_API_KEY manquante dans les Secrets Streamlit.")
    client = genai.Client(api_key=api_key_env)

# ==========================================
# 1. CONSTANTES (CANON INTÉGRAL)
# ==========================================

CONSTANTES_SAGA = {
    "Jonas": """ÂGE: ~17 ans. Surnom: Grizzly. Orientation: Gay. Couple exclusif avec Léo (Moineau).
Aura: VERTE (phosphorescent, braise froide). Manifestation: 'Colère' (créature verte, yeux charbon).
Capacités: chasseur expert, tir méthodique. Traits: cicatrice gorge, épaules étroites.
Talisman: petite boîte de métal. Thèmes: culpabilité, protection.""",

    "Léo": """ÂGE: ~15-17 ans. Surnom: Moineau. Orientation: Bisexuel. Couple exclusif avec Jonas (Grizzly).
Aura: BLEUE (liens de lumière). Manifestation: La Louve de lumière blanche (gardienne).
Capacités: voit les fils, peut 'arrêter le temps' en crise. Traits: cheveux blonds, cicatrice lèvre.
Talisman: la Louve de lumière. Thèmes: vision, lien du groupe.""",

    "Zack": """ÂGE: 15 ans (T2). Nom: Zackary (Albert d'origine). Surnom: Gaz (ancien).
Orientation: découverte active. Aura: ROUGE CHAUD (braise - JAMAIS noir).
Capacités: membranes/ailes, vol, électrostatique (gaz + étincelle = combustion).
Traits: yeux reflets noisette-rouille, corps mince, cicatrices d'ailes.
Talismans: louveteau de pierre + sac fleur brodée + breloque. Thèmes: consentement, identité.""",

    "Jade": """Rôle: cheffe/matriarche. Orientation: lien avec Zack (rythme lent).
Aura: JAUNE/DORÉE. Arme: fronde. Traits: posture droite, tactique.
Thèmes: ne pas s'effacer, souveraineté du non et du oui.""",

    "Autyss": """Rôle: stratège, 'chirurgien'. Aura: VIOLETTE.
Capacités: analyse tactique, dissociation contrôlée, soins. Besoins: constantes sensorielles.
Talisman: sac de Zack (prêté). Traits: s'exprime en poèmes.
Thèmes: colonnes vs chaos, ressentir sans disséquer.""",

    "SAGA": """Thèmes: Reconstruction post-trauma ('corps passager, jamais outil').
L'Ombre, la Cathédrale, la Voix.
Règles du groupe (T3): base Jonas–Léo intouchable; si flou = non; jalousie nommée; pas de sexe en secret.
Lieux: Badlands, Village Soleil, Forge.""",
}

# ==========================================
# 2. GOOGLE SHEETS (ARCHIVAGE)
# ==========================================

SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

def connecter_et_obtenir_onglet(nom_onglet):
    try:
        if "GCP_JSON_BRUT" not in st.secrets:
            return None
        json_info = json.loads(st.secrets["GCP_JSON_BRUT"], strict=False)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json_info, scopes=scope)
        client_gs = gspread.authorize(creds)
        ss = client_gs.open_by_key(SHEET_ID)
        try:
            return ss.worksheet(nom_onglet)
        except gspread.exceptions.WorksheetNotFound:
            nouvel_onglet = ss.add_worksheet(title=nom_onglet, rows="2000", cols="5")
            nouvel_onglet.append_row(["Date", "Diagnostic", "Type"])
            return nouvel_onglet
    except Exception as e:
        st.error(f"Erreur Sheets : {e}")
        return None

# ==========================================
# 3. MOTEUR IA
# ==========================================

def appel_ia(prompt: str, temperature: float = 0.1) -> str:
    try:
        # Priorité au modèle 3 Flash Preview s'il est disponible dans ton SDK
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=4096,
            ),
        )
        return response.text or ""
    except Exception:
        # Fallback sur 2.0 Flash si le 3 n'est pas encore mappé
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature, max_output_tokens=4096),
            )
            return response.text or ""
        except Exception as e:
            return f"❌ Erreur Gemini : {e}"

# ==========================================
# 4. GESTION DES FICHIERS
# ==========================================

def extraire_texte(f) -> str:
    try:
        if f.name.endswith(".pdf"):
            with pdfplumber.open(f) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
        elif f.name.endswith(".docx"):
            return "\n".join([p.text for p in Document(f).paragraphs])
        elif f.name.endswith(".odt"):
            return "\n".join([extractText(p) for p in load(f).getElementsByType(P)])
        return ""
    except Exception:
        return ""

def decouper_chapitres(texte: str):
    # CORRECTION : Utilisation de \s (espace) et \d (chiffre)
    pattern = r'(?i)chapitre\s+\d+'
    segments = re.split(pattern, texte)
    titres = re.findall(pattern, texte)
    chaps = []

    if len(segments) > 0 and len(segments[0].strip()) > 100:
        chaps.append({"titre": "Prologue", "contenu": segments[0].strip()})

    for i, t in enumerate(titres):
        if i + 1 < len(segments):
            chaps.append({"titre": t.strip(), "contenu": segments[i + 1].strip()})
    return chaps

# ==========================================
# 5. INTERFACE
# ==========================================

st.set_page_config(page_title="L'Archiviste V17.4", layout="wide")
st.title("🛡️ L'Archiviste : Gardien du Canon")

if "db" not in st.session_state:
    st.session_state.db = {"chapitres": [], "ready": False}

f_inputs = st.sidebar.file_uploader("Importer les Tomes", type=["pdf", "docx", "odt"], accept_multiple_files=True)

if f_inputs and not st.session_state.db["ready"]:
    if st.button("🚀 Scanner la Saga"):
        full_txt = ""
        for f in f_inputs:
            full_txt += extraire_texte(f) + "\n\n"
        full_txt = full_txt.replace("’", "'").replace("œ", "oe")
        st.session_state.db["chapitres"] = decouper_chapitres(full_txt)
        st.session_state.db["ready"] = True
        st.rerun()

if st.session_state.db["ready"]:
    perso = st.sidebar.selectbox("Cible", options=list(CONSTANTES_SAGA.keys()))
    
    indices = [i for i, c in enumerate(st.session_state.db["chapitres"]) if perso.lower() in c["contenu"].lower()]
    sel = st.multiselect("Chapitres", options=indices, format_func=lambda x: st.session_state.db["chapitres"][x]["titre"])

    if sel and st.button("🧠 Analyser"):
        txt_focus = "\n".join([st.session_state.db["chapitres"][i]["contenu"][:8000] for i in sel])
        prompt = f"""
[ANALYSE ARCHIVISTE V17.4]
PERSONNAGE : {perso}
CANON : {CONSTANTES_SAGA[perso]}

MISSION :
- Analyse le personnage sur ces extraits.
- Rapporte toute INCOHÉRENCE DÉTECTÉE (ex: aura noire pour Zack, objet manquant).
- Structure : Physique/Aura, Psyché/Trauma, Liens, Évolution.

TEXTE : {txt_focus}
"""
        with st.spinner("L'IA consulte les archives..."):
            resultat = appel_ia(prompt)
            st.markdown(resultat)
            st.session_state["dernier_resultat"] = resultat
            st.session_state["dernier_perso"] = perso

    if "dernier_resultat" in st.session_state and st.button("💾 Archiver dans Sheets"):
        onglet = connecter_et_obtenir_onglet(st.session_state.get("dernier_perso", "SAGA"))
        if onglet:
            date_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            onglet.append_row([date_now, st.session_state["dernier_resultat"], "V17.4"])
            st.success("✅ Diagnostic archivé.")

if st.sidebar.button("🗑️ Reset"):
    st.session_state.db = {"chapitres": [], "ready": False}
    st.rerun()
    
    
