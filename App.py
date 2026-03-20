import os
import re
import streamlit as st
import google.generativeai as genai
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# ==========================================
# 0. CONFIGURATION & CANON OFFICIEL
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

CONSTANTES_SAGA = {
    "Jonas": (
        "ÂGE: ~17 ans. Surnom: Grizzly. Orientation: Gay. Couple exclusif: Léo (Moineau). "
        "AURA: VERTE (phosphorescente). Manifestation: 'Colère' (créature verte, yeux charbon). "
        "CAPACITÉS: Chasseur expert, tir précis, survie. TALISMAN: Boîte de métal. "
        "TRAITS: Cicatrice gorge, épaules étroites. THÈMES: Culpabilité, Protection."
    ),
    "Léo": (
        "ÂGE: 15-17 ans. Surnom: Moineau. Orientation: Bisexuel. Couple exclusif: Jonas (Grizzly). "
        "AURA: BLEUE (liens lumineux). Manifestation: La Louve de lumière blanche. "
        "CAPACITÉS: Voit les fils, arrêt du temps (crise). TALISMAN: Louve intérieure. "
        "TRAITS: Cheveux blonds, cicatrice lèvre. THÈMES: Visionnaire, Gardien."
    ),
    "Zack": (
        "ÂGE: 15 ans. Nom: Zackary (Albert d'origine). Surnom: Gaz. Orientation: Découverte active. "
        "AURA: ROUGE CHAUD (braise - JAMAIS noir). CAPACITÉS: Ailes/Membranes, vol, électrostatique. "
        "TRAITS: Yeux reflets noisette-rouille, corps mince, cicatrices ailes. "
        "TALISMANS: Louveteau de pierre + sac fleur brodée + breloque. THÈMES: Consentement, Identité."
    ),
    "Jade": (
        "RÔLE: Matriarche, stabilité. ORIENTATION: Lien avec Zack (rythme lent). "
        "AURA: JAUNE/DORÉE. ARME: Fronde. TRAITS: Posture droite, tactique. "
        "THÈMES: Apprendre à dire non, protection des vulnérables."
    ),
    "Autyss": (
        "RÔLE: Stratège, 'chirurgien'. AURA: VIOLETTE. CAPACITÉS: Colonnes mentales, sutures. "
        "BESOINS: Constantes sensorielles (fleur brodée, pierre, eau chaude). TALISMAN: Sac de Zack (prêté). "
        "TRAITS: Dissociation contrôlée, s'exprime en poèmes. THÈMES: Raison vs Chaos."
    ),
    "SAGA": (
        "THÈMES: Reconstruction post-trauma, Souveraineté ('corps passager, jamais outil'), Consentement. "
        "RÈGLES DU GROUPE: Jonas-Léo intouchable; si flou = non; pas de sexe en secret; jalousie nommée. "
        "LIEUX: Badlands, Village Soleil, Forge. ANTAGONISTES: Cathédrale, Luceduort."
    )
}

# ==========================================
# 1. MOTEUR IA (RELIANCE GEMINI 3 FLASH)
# ==========================================
def appel_ia(prompt):
    # On utilise le modèle confirmé Gemini 3 Flash pour sa finesse d'analyse
    try:
        model = genai.GenerativeModel("gemini-3-flash-preview")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Erreur IA : {e}"

# ==========================================
# 2. LOGIQUE DE TRIAGE ET ANALYSE
# ==========================================
def extraire_passages_perso(texte, nom_perso, fenetre=1200):
    nom_perso = nom_perso.lower()
    matches = [m.start() for m in re.finditer(re.escape(nom_perso), texte.lower())]
    passages = []
    # On prend les 35 occurrences les plus denses pour une vue 360°
    for m in matches[:35]:
        start, end = max(0, m - fenetre), min(len(texte), m + fenetre)
        passages.append(texte[start:end])
    return "\n\n--- EXTRAIT DU MANUSCRIT ---\n\n".join(passages)

# ==========================================
# 3. INTERFACE STREAMLIT
# ==========================================
st.set_page_config(page_title="Archiviste V17.3 - Canon", layout="wide")
st.title("🛡️ L'Archiviste V17.3 : Gardien de Grizzly & Moineau")

st.sidebar.header("📁 Bibliothèque")
f_inputs = st.sidebar.file_uploader("Charger les fichiers de la Saga", type=["pdf", "docx", "odt"], accept_multiple_files=True)

if f_inputs and st.sidebar.button("🚀 Scanner l'Intégrale"):
    with st.spinner("Fusion des chapitres et conversion..."):
        full_txt = ""
        for f in f_inputs:
            if f.name.endswith(".pdf"):
                with pdfplumber.open(f) as pdf:
                    full_txt += "\n".join([p.extract_text() or "" for p in pdf.pages])
            elif f.name.endswith(".docx"):
                full_txt += "\n".join([p.text for p in Document(f).paragraphs])
            elif f.name.endswith(".odt"):
                full_txt += "\n".join([extractText(p) for p in load(f).getElementsByType(P)])
        st.session_state.txt_saga = full_txt.replace("’", "'")
        st.success("Toute la Saga est en mémoire.")

if "txt_saga" in st.session_state:
    target = st.sidebar.selectbox("Personnage à analyser", options=list(CONSTANTES_SAGA.keys()))
    
    if st.button(f"🔍 Générer la Fiche Canon de {target}"):
        with st.spinner(f"Extraction des données pour {target}..."):
            extraits = extraire_passages_perso(st.session_state.txt_saga, target)
            
            prompt = f"""
            [ANALYSE CANONIQUE - SAGA GRIZZLY ET MOINEAU]
            Tu es l'Archiviste Pro. Ta mission est de générer la fiche de {target} à partir des extraits fournis.
            
            CANON À RESPECTER (VÉRIFIE LA COHÉRENCE) :
            {CONSTANTES_SAGA[target]}
            
            CADRE GLOBAL DE LA SAGA :
            {CONSTANTES_SAGA['SAGA']}
            
            STRUCTURE DE TA RÉPONSE :
            1. PHYSIQUE & AURAS : Vérifie la couleur de l'aura et les manifestations (Colère/Louve).
            2. PSYCHOLOGIE : État émotionnel et évolution.
            3. DIAGNOSTIC DU TRAUMA : Analyse somatique (comment son corps réagit dans les extraits).
            4. TALISMANS & OBJETS : Est-ce que ses objets clés (ex: louveteau de pierre pour Zack) sont présents ?
            5. CONSENTEMENT & RÈGLES : Le personnage respecte-t-il les règles du groupe ?
            6. ÉCARTS AU CANON : Signale IMMÉDIATEMENT si une aura change de couleur par erreur ou si Zack est appelé 'Albert' sans raison narrative.

            TEXTE DU MANUSCRIT :
            {extraits}
            """
            resultat = appel_ia(prompt)
            st.markdown(resultat)
            st.download_button(f"💾 Exporter Fiche {target}", resultat, file_name=f"Fiche_{target}.txt")
          
