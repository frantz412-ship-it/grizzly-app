import os
import re
import time
import pandas as pd
import streamlit as st
import google.generativeai as genai
from datetime import datetime, timezone
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & CANON ---
st.set_page_config(page_title="Grizzly & Moineau - Archiviste V17.5", layout="wide")

CANON_DATA = {
    "Jonas": "ÂGE: 17 ans. Grizzly. Couple exclusif Léo. Aura: VERTE phosphorescente (Colère). Yeux verts, cheveux bruns, cicatrice gorge.",
    "Léo": "ÂGE: 15-17 ans. Moineau. Couple exclusif Jonas. Aura: BLEUE. Louve blanche de lumière (gardienne), voit les fils.",
    "Zack": "ÂGE: 15 ans. Zackary/Zack (choisi). Aura: ROUGE CHAUD. Ailes aux flancs, vol. Talismans: Louveteau pierre, sac fleur.",
    "Jade": "Jade. Cheffe de terrain. Aura: JAUNE/DORÉE. Arme: Fronde. Souveraineté, non-sacrificielle.",
    "Autyss": "Autyss. Chirurgien des colonnes. Aura: VIOLETTE. Capacité: Colonnes/Diagrammes. Poésie.",
    "Luc": "Luc. Surnom: Gremlin. Personnage secondaire, enjeux d'appartenance.",
    "SAGA": "Couple Jonas-Léo intouchable. Si flou = non. Corps passager, jamais outil. Consentement explicite."
}

# --- 2. MÉMOIRE ---
if "chapitres" not in st.session_state:
    st.session_state.chapitres = []
if "analyses" not in st.session_state:
    st.session_state.analyses = []

# --- 3. FONCTIONS TECHNIQUES ---
def normaliser_texte(txt: str) -> str:
    replacements = {"’": "'", "«": '"', "»": '"', "œ": "oe", "…": "..."}
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt

def extraire_texte(file) -> str:
    try:
        if file.name.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
        elif file.name.endswith(".docx"):
            return "\n".join([p.text for p in Document(file).paragraphs])
        elif file.name.endswith(".odt"):
            odt_doc = load(file)
            return "\n".join([extractText(p) for p in odt_doc.getElementsByType(P)])
    except Exception as e:
        st.error(f"Erreur lecture {file.name}: {e}")
    return ""

def decouper_chapitres(texte: str):
    """Détecte Prologue, Épilogue et Chapitre (num.)"""
    pattern = r"(?i)(Prologue|Epilogue|Épilogue|Chapitre\s*[\(\s]*\d+[\.\s\)]*)"
    parts = re.split(pattern, texte)
    if len(parts) <= 1:
        return [{"titre": "Manuscrit Complet", "contenu": texte}]
    
    chapitres = []
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            chapitres.append({"titre": parts[i].strip(), "contenu": parts[i + 1].strip()})
    return chapitres

# --- 4. CONNEXION IA (Roc de Pierre) ---
def appel_ia_stable(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "❌ Clé API manquante dans les Secrets."
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Utilisation des modèles confirmés par ton diagnostic
    modeles = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
    for m_name in modeles:
        try:
            model = genai.GenerativeModel(m_name)
            resp = model.generate_content(prompt, generation_config={"temperature": 0.2})
            return resp.text
        except: continue
    return "❌ Aucun modèle n'a répondu."

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("📂 Bibliothèque")
    files = st.file_uploader("Charger Tomes (PDF/DOCX/ODT)", accept_multiple_files=True)
    
    if st.button("🚀 Scanner l'Intégrale"):
        if files:
            with st.spinner("Triage des manuscrits..."):
                all_text = ""
                for f in files:
                    all_text += f"\n\n[TOME: {f.name}]\n\n" + extraire_texte(f)
                st.session_state.chapitres = decouper_chapitres(normaliser_texte(all_text))
            st.success(f"{len(st.session_state.chapitres)} sections détectées.")
    
    if st.button("🗑️ Reset"):
        st.session_state.chapitres = []
        st.session_state.analyses = []
        st.rerun()

# --- 6. LABORATOIRE D'ANALYSE ---
st.title("🔬 Laboratoire Grizzly & Moineau")

if st.session_state.chapitres:
    col_sel, col_outils = st.columns([1, 2])
    
    with col_sel:
        perso = st.selectbox("Personnage cible", list(CANON_DATA.keys()))
        filtre = [c for c in st.session_state.chapitres if perso.lower() in c["contenu"].lower() or perso == "SAGA"]
        selection = st.multiselect("Chapitres à analyser", filtre, format_func=lambda x: x["titre"])

    with col_outils:
        st.subheader("Outils d'Analyse")
        btns = st.columns(4)
        config = {
            "🧠 Psyché": "Trauma, évolution et émotions.",
            "⚔️ Physique": "Portrait, Aura et manifestations somatiques.",
            "🕸️ Liens": "Relations, fils bleus et complicité.",
            "🕵️ Diagnostic": "Analyse médicale/traumatique et cohérence narrative."
        }
        
        for i, (label, focus) in enumerate(config.items()):
            if btns[i].button(label):
                if not selection:
                    st.error("Sélectionne au moins un chapitre !")
                else:
                    contexte = "\n\n".join([f"### {c['titre']}\n{c['contenu'][:8000]}" for c in selection])
                    prompt = f"CANON {perso}: {CANON_DATA[perso]}\n\nANALYSE: {focus}\n\nTEXTE:\n{contexte}"
                    
                    with st.spinner(f"Analyse de {perso}..."):
                        txt_ia = appel_ia_stable(prompt)
                        st.session_state.analyses.insert(0, {
                            "id": datetime.now(timezone.utc).timestamp(),
                            "date": datetime.now().strftime("%d/%m %H:%M"),
                            "perso": perso,
                            "type": label,
                            "texte": txt_ia
                        })

# --- 7. HISTORIQUE & GSHEETS ---
st.divider()
for ana in st.session_state.analyses:
    with st.expander(f"📌 {ana['type']} - {ana['perso']} ({ana['date']})", expanded=True):
        st.markdown(ana["texte"])
        if st.button(f"💾 Archiver {ana['perso']}", key=f"btn-{ana['id']}"):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                try: existing = conn.read(worksheet=ana["perso"])
                except: existing = pd.DataFrame()
                new_row = pd.DataFrame([ana])
                final_df = pd.concat([existing, new_row], ignore_index=True) if not existing.empty else new_row
                conn.update(worksheet=ana["perso"], data=final_df)
                st.success(f"Archivé dans l'onglet '{ana['perso']}' !")
            except Exception as e:
                st.error(f"Erreur GSheets : {e}")
