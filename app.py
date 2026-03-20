import streamlit as st
import pandas as pd
import re
import os
import google.generativeai as genai
from datetime import datetime, timezone
from PyPDF2 import PdfReader
from docx import Document
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & CANON DÉFINITIF ---
st.set_page_config(page_title="Grizzly & Moineau - Lab", page_icon="📚", layout="wide")

CANON_DATA = {
    "Jonas": "ÂGE: 17 ans. Noms: Jonas. Surnoms: Grizzly, Grizz. Couple exclusif Léo. Aura: VERTE phosphorescente (Colère). Yeux verts, cheveux bruns, cicatrice gorge.",
    "Léo": "ÂGE: 15-17 ans. Noms: Léo. Surnoms: Moineau. Couple exclusif Jonas. Aura: BLEUE. Louve blanche de lumière (gardienne), voit les fils.",
    "Zack": "ÂGE: 15 ans. Noms: Gaz (ancien), Albert (légal), Zackary/Zack (choisi). Surnoms: Gaz. Aura: ROUGE CHAUD. Ailes aux flancs, vol. Talismans: Louveteau pierre, sac fleur. NOTE: Appelle Luc 'Gremlin'.",
    "Jade": "Noms: Jade. Surnoms: Cheffe ou Matriarche de terrain. Aura: JAUNE/DORÉE. Arme: Fronde. Souveraineté, non-sacrificielle.",
    "Autyss": "Noms: Autyss. Surnoms: Chirurgien des colonnes, Compteur de poèmes. Aura: VIOLETTE. Capacité: Colonnes/Diagrammes. Poésie pour le crucial.",
    "Luc": "Noms: Luc. Surnoms: Gremlin (donné par Zack). Rôle: Personnage secondaire, enjeux d'appartenance et de choix.",
    "SAGA": "Couple Jonas-Léo intouchable. Si flou = non. Corps passager, jamais outil. Consentement explicite. Cathédrale vs Voix."
}

# --- 2. MÉMOIRE DE L'APPLICATION ---
if "chapitres" not in st.session_state:
    st.session_state.chapitres = []
if "analyses" not in st.session_state:
    st.session_state.analyses = []

# --- 3. FONCTIONS TECHNIQUES ---
def normaliser_texte(txt: str) -> str:
    """Nettoie le texte pour éviter les bugs d'encodage."""
    replacements = {
        "’": "'",
        "«": '"',
        "»": '"',
        "œ": "oe",
        "…": "...",
    }
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt

def extraire_texte(file) -> str:
    """Extrait le texte d'un PDF ou d'un DOCX."""
    try:
        if file.name.endswith(".pdf"):
            return " ".join(
                [page.extract_text() or "" for page in PdfReader(file).pages]
            )
        elif file.name.endswith(".docx"):
            return " ".join([p.text for p in Document(file).paragraphs])
    except Exception as e:
        st.error(f"Erreur lecture {file.name}: {e}")
    return ""

def decouper_chapitres(texte: str):
    """
    Découpe en chapitres sur 'Chapitre X', insensible à la casse.
    Si aucun chapitre trouvé, renvoie un seul bloc.
    """
    parts = re.split(r"(?i)(chapitres+d+)", texte)
    if len(parts) <= 1:
        return [{"titre": "Manuscrit Complet", "contenu": texte}]

    chapitres = []
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            chapitres.append({"titre": parts[i], "contenu": parts[i + 1]})
    return chapitres

# --- 4. CONNEXION IA (même modèle que ton curl : gemini-flash-latest) ---
model = None
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # IMPORTANT : même nom que dans ton curl : models/gemini-flash-latest:generateContent
    model = genai.GenerativeModel(model_name="gemini-flash-latest")
except Exception as e:
    st.error(f"⚠️ Erreur config Gemini : {e}")

# --- 5. SIDEBAR : GESTION DES FICHIERS ---
with st.sidebar:
    st.header("📂 Manuscrit")
    files = st.file_uploader(
        "Importer Tomes (PDF/DOCX)", accept_multiple_files=True
    )

    if st.button("🚀 Traiter les fichiers"):
        if not files:
            st.warning("Sélectionne au moins un fichier.")
        else:
            with st.spinner("Décodage de la Saga..."):
                all_text = ""
                for f in files:
                    all_text += f"

[TOME: {f.name}]

"
                    all_text += extraire_texte(f)
                st.session_state.chapitres = decouper_chapitres(
                    normaliser_texte(all_text)
                )
            st.success(f"{len(st.session_state.chapitres)} sections détectées.")

    if st.button("🗑️ Reset Application"):
        st.session_state.chapitres = []
        st.session_state.analyses = []
        st.rerun()

# --- 6. STATION D'ANALYSE ---
st.title("🔬 Laboratoire Grizzly & Moineau")

if st.session_state.chapitres:
    col_sel, col_outils = st.columns([1, 2])

    with col_sel:
        perso = st.selectbox("Personnage à scanner", list(CANON_DATA.keys()))

        # Filtrage : chapitres qui contiennent le nom, ou tous si SAGA
        filtre = [
            c
            for c in st.session_state.chapitres
            if perso.lower() in c["contenu"].lower() or perso == "SAGA"
        ]
        st.caption(f"{len(filtre)} chapitres correspondent à {perso}.")
        selection = st.multiselect(
            "Chapitres à envoyer à l'IA",
            filtre,
            format_func=lambda x: x["titre"],
        )

    with col_outils:
        st.subheader("Outils d'analyse")
        btns = st.columns(4)
        config_outils = {
            "🧠 Psyché": "Trauma, évolution psychologique et émotions.",
            "⚔️ Physique": "Portrait physique, Aura et manifestations de pouvoir.",
            "🕸️ Liens": "Fils bleus, relations de groupe et complicité.",
            "🕵️ Incohérences": "Contradictions avec le Canon fixé.",
        }

        for i, (label, focus) in enumerate(config_outils.items()):
            if btns[i].button(label):
                if not model:
                    st.error("IA non connectée (modèle indisponible).")
                elif not selection:
                    st.error("Choisis au moins un chapitre !")
                else:
                    # On limite à 10 000 caractères par chapitre pour ne pas exploser le contexte
                    contexte = "

".join(
                        [
                            f"### {c['titre']}
{c['contenu'][:10000]}"
                            for c in selection
                        ]
                    )
                    prompt = f"""
RÔLE : Expert narratif de la Saga 'Grizzly et Moineau'.
RÉFÉRENCE CANON POUR {perso} : {CANON_DATA[perso]}

MANUSCRIT À ANALYSER :
{contexte}

CONSIGNES :
1. Focus analyse : {focus}
2. Si info absente des extraits -> écris exactement "Non mentionné dans le manuscrit."
3. Si le texte contredit le canon -> écris "INCOHÉRENCE DÉTECTÉE" + citation courte du texte.
4. RESPECTER LE CANON COMME UNE LOI ABSOLUE.
5. Format Markdown avec des sous-sections stables.
"""

                    try:
                        with st.spinner(f"Analyse de {perso} en cours..."):
                            resp = model.generate_content(
                                prompt,
                                generation_config={"temperature": 0.2},
                            )
                            txt_ia = getattr(resp, "text", "") or "_Réponse vide de l'IA._"

                            st.session_state.analyses.insert(
                                0,
                                {
                                    "id": datetime.now(
                                        timezone.utc
                                    ).timestamp(),
                                    "date": datetime.now().strftime(
                                        "%d/%m %H:%M"
                                    ),
                                    "perso": perso,
                                    "type": label,
                                    "texte": txt_ia,
                                },
                            )
                    except Exception as e:
                        st.error(f"Erreur Gemini : {e}")

# --- 7. HISTORIQUE & ARCHIVAGE ---
st.divider()
for ana in st.session_state.analyses:
    u_key = f"{ana['id']}-{ana['perso']}-{ana['type']}"

    with st.expander(
        f"📌 {ana['type']} - {ana['perso']} ({ana['date']})", expanded=True
    ):
        st.markdown(ana["texte"])

        if st.button(
            f"💾 Archiver {ana['perso']}", key=f"btn-{u_key}"
        ):
            try:
                conn = st.connection(
                    "gsheets", type=GSheetsConnection
                )
                try:
                    existing = conn.read(worksheet=ana["perso"])
                except Exception:
                    existing = pd.DataFrame()

                new_row = pd.DataFrame([ana])
                if existing is None or existing.empty:
                    final_df = new_row
                else:
                    final_df = pd.concat(
                        [existing, new_row], ignore_index=True
                    )

                conn.update(worksheet=ana["perso"], data=final_df)
                st.success(
                    f"Archivé dans l'onglet '{ana['perso']}' !"
                )
            except Exception as e:
                st.error(
                    f"Erreur GSheets (Vérifie tes identifiants de projet ou si l'onglet existe) : {e}"
)
