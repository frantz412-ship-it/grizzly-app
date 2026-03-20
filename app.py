import streamlit as st
import pandas as pd
import re
import os
import google.generativeai as genai
from datetime import datetime, timezone
from PyPDF2 import PdfReader
from docx import Document
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & CANON ---
st.set_page_config(page_title="Grizzly & Moineau - Lab", page_icon="📚", layout="wide")

CANON_DATA = {
    "Jonas": "ÂGE: 17 ans. Noms: Jonas. Surnoms: Grizzly, Grizz. Couple exclusif Léo. Aura: VERTE. Yeux verts, cheveux bruns, cicatrice gorge.",
    "Léo": "ÂGE: 15-17 ans. Noms: Léo. Surnoms: Moineau. Couple exclusif Jonas. Aura: BLEUE. Louve blanche, voit les fils.",
    "Zack": "ÂGE: 15 ans. Noms: Gaz (ancien), Albert (légal), Zackary/Zack (choisi). Surnoms: Gaz. Aura: ROUGE CHAUD. Ailes aux flancs, vol. Talismans: Louveteau pierre, sac fleur. NOTE: Appelle Luc 'Gremlin'.",
    "Jade": "Noms: Jade. Surnoms: Cheffe ou Matriarche de terrain. Aura: JAUNE/DORÉE. Fronde. Souveraineté, non-sacrificielle.",
    "Autyss": "Noms: Autyss. Surnoms: Chirurgien des colonnes, Compteur de poèmes. Aura: VIOLETTE. Colonnes/Diagrammes. Poésie pour le crucial.",
    "Luc": "Noms: Luc. Surnoms: Gremlin (donné par Zack). Rôle: Personnage secondaire.",
    "SAGA": "Couple Jonas-Léo intouchable. Si flou = non. Corps passager, jamais outil. Consentement explicite. Cathédrale vs Voix."
}

# --- 2. INITIALISATION SESSION ---
if 'chapitres' not in st.session_state: st.session_state.chapitres = []
if 'analyses' not in st.session_state: st.session_state.analyses = []

# --- 3. FONCTIONS TECHNIQUES ---
def normaliser_texte(txt):
    replacements = {'’': "'", '«': '"', '»': '"', 'œ': 'oe', '…': '...'}
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt

def extraire_texte(file):
    try:
        if file.name.endswith('.pdf'):
            return " ".join([page.extract_text() or "" for page in PdfReader(file).pages])
        elif file.name.endswith('.docx'):
            return " ".join([p.text for p in Document(file).paragraphs])
    except Exception as e:
        st.error(f"Erreur lecture {file.name}: {e}")
    return ""

def decouper_chapitres(texte):
    parts = re.split(r'(?i)(chapitre\s+\d+)', texte)
    if len(parts) <= 1:
        return [{"titre": "Manuscrit Complet", "contenu": texte}]
    
    chapitres = []
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            chapitres.append({"titre": parts[i], "contenu": parts[i+1]})
    return chapitres

# --- 4. CONNEXION IA (Utilisation de Gemini 1.5 Flash) ---
model = None
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # CORRECTION : Utilisation d'un modèle existant et stable
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"⚠️ Erreur config Gemini : {e}")

# --- 5. SIDEBAR : GESTION DES FICHIERS ---
with st.sidebar:
    st.header("📂 Manuscrit")
    files = st.file_uploader("Importer Tomes (PDF/DOCX)", accept_multiple_files=True)
    
    if st.button("🚀 Traiter les fichiers"):
        if not files:
            st.warning("Sélectionne au moins un fichier.")
        else:
            with st.spinner("Décodage de la Saga..."):
                all_text = ""
                for f in files:
                    all_text += f"\n\n[TOME: {f.name}]\n\n"
                    all_text += extraire_texte(f)
                st.session_state.chapitres = decouper_chapitres(normaliser_texte(all_text))
            st.success(f"{len(st.session_state.chapitres)} sections détectées.")

    if st.button("🗑️ Reset Application"):
        st.session_state.chapitres, st.session_state.analyses = [], []
        st.rerun()

# --- 6. STATION D'ANALYSE ---
st.title("🔬 Laboratoire Grizzly & Moineau")

if st.session_state.chapitres:
    col_sel, col_outils = st.columns([1, 2])
    
    with col_sel:
        perso = st.selectbox("Personnage à scanner", list(CANON_DATA.keys()))
        filtre = [c for c in st.session_state.chapitres if perso.lower() in c['contenu'].lower() or perso == "SAGA"]
        st.caption(f"{len(filtre)} chapitres correspondent.")
        selection = st.multiselect("Chapitres à envoyer à l'IA", filtre, format_func=lambda x: x['titre'])

    with col_outils:
        st.subheader("Boutons d'analyse")
        btns = st.columns(4)
        config_outils = {
            "🧠 Psyché": "Trauma, évolution psychologique et émotions.",
            "⚔️ Physique": "Traits physiques, Aura et manifestations de pouvoir.",
            "🕸️ Liens": "Fils bleus, relations de groupe et complicité.",
            "🕵️ Incohérences": "Contradictions avec le Canon fixé."
        }

        for i, (label, focus) in enumerate(config_outils.items()):
            if btns[i].button(label):
                if not model: st.error("IA non connectée.")
                elif not selection: st.error("Choisis au moins un chapitre !")
                else:
                    contexte = "\n\n".join([f"### {c['titre']}\n{c['contenu'][:10000]}" for c in selection])
                    prompt = f"""
                    RÔLE : Expert narratif de la Saga 'Grizzly et Moineau'.
                    RÉFÉRENCE CANON POUR {perso} : {CANON_DATA[perso]}
                    
                    MANUSCRIT À ANALYSER :
                    {contexte}
                    
                    CONSIGNES :
                    1. Focus analyse : {focus}
                    2. Si info absente -> "Non mentionné dans le manuscrit."
                    3. Si contradiction -> "INCOHÉRENCE DÉTECTÉE" + citation courte.
                    4. RESPECTER LE CANON COMME UNE LOI ABSOLUE.
                    5. Format Markdown.
                    """
                    try:
                        with st.spinner(f"Analyse de {perso} en cours..."):
                            resp = model.generate_content(prompt, generation_config={"temperature": 0.2})
                            txt_ia = getattr(resp, "text", "") or "_Réponse vide de l'IA._"
                            
                            st.session_state.analyses.insert(0, {
                                "id": datetime.now(timezone.utc).timestamp(),
                                "date": datetime.now().strftime("%H:%M"),
                                "perso": perso, "type": label, "texte": txt_ia
                            })
                    except Exception as e:
                        st.error(f"Erreur Gemini : {e}")

# --- 7. HISTORIQUE & ARCHIVAGE ---
st.divider()
for ana in st.session_state.analyses:
    unique_key = f"{ana['id']}-{ana['perso']}-{ana['type']}"
    
    with st.expander(f"📌 {ana['type']} - {ana['perso']} ({ana['date']})", expanded=True):
        st.markdown(ana['texte'])
        
        if st.button(f"💾 Archiver {ana['perso']}", key=f"btn-{unique_key}"):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    existing = conn.read(worksheet=ana['perso'])
                except:
                    existing = pd.DataFrame()
                
                new_row = pd.DataFrame([ana])
                final_df = pd.concat([existing, new_row], ignore_index=True)
                
                conn.update(worksheet=ana['perso'], data=final_df)
                st.success(f"Archivé dans l'onglet '{ana['perso']}' !")
            except Exception as e:
                st.error(f"Erreur GSheets : {e}")
                
