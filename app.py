import streamlit as st
import json
from docx import Document
import time

# --- 1. IMPORTATION ROBUSTE DES IA ---
# Pour Google
try:
    from google import genai
except ImportError:
    st.error("Erreur : La bibliothèque 'google-genai' est manquante.")

# Pour Mistral (on teste les deux noms de classe possibles en 2026)
try:
    from mistralai import Mistral
except ImportError:
    try:
        from mistralai.client import MistralClient as Mistral
    except ImportError:
        st.error("Erreur : La bibliothèque 'mistralai' est manquante ou mal installée.")

# --- 2. CONFIGURATION DES CLIENTS ---
try:
    # Client Google
    client_google = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    # Client Mistral
    client_mistral = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
except Exception as e:
    st.warning("⚠️ Une ou plusieurs clés API sont manquantes dans les Secrets.")

# --- 3. CONFIGURATION UI ---
st.set_page_config(page_title="Grizzly et Moineau - Hub Multi-IA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .tag { 
        display: inline-block; padding: 4px 12px; border-radius: 20px; 
        background: #1e293b; border: 1px solid #38bdf8; 
        margin: 4px; color: #38bdf8; font-size: 0.85rem; 
    }
    h1, h2, h3 { color: #38bdf8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FONCTIONS ---
def read_docx(file):
    doc = Document(file)
    return '\n'.join([p.text for p in doc.paragraphs])

def analyser_bloc(texte, moteur):
    prompt = f"Analyse cet extrait de 'Grizzly et Moineau'. Extraits en JSON : personnages, capacites, armes, traumas, lieux, resume. Texte : {texte}"
    
    if "Gemini" in moteur:
        response = client_google.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    else:
        # Pour Mistral Large
        response = client_mistral.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        # On gère si la réponse est un objet ou une string
        content = response.choices[0].message.content
        return json.loads(content) if isinstance(content, str) else content

# --- 5. INTERFACE ---
st.title("📚 Grizzly et Moineau : Hub d'Analyse")

with st.sidebar:
    st.header("⚙️ Configuration")
    moteur_choisi = st.radio(
        "Choisir l'Intelligence Artificielle :",
        ["Google Gemini 2.0", "Mistral AI (Large)"]
    )

uploaded_file = st.file_uploader("Charger un chapitre (.docx)", type="docx")

if uploaded_file:
    full_text = read_docx(uploaded_file)
    # Découpage par blocs de 5000 caractères
    morceaux = [full_text[i:i+5000] for i in range(0, len(full_text), 5000)]
    
    if st.button(f"🚀 ANALYSER AVEC {moteur_choisi.upper()}"):
        resultats_globaux = {
            "personnages": set(), "capacites": set(), "armes": set(), 
            "traumas": set(), "lieux": set(), "resumes": []
        }
        
        progress = st.progress(0)
        for idx, bloc in enumerate(morceaux):
            try:
                data = analyser_bloc(bloc, moteur_choisi)
                for k in ["personnages", "capacites", "armes", "traumas", "lieux"]:
                    if k in data and isinstance(data[k], list):
                        resultats_globaux[k].update(data[k])
                if "resume" in data:
                    resultats_globaux["resumes"].append(data["resume"])
                time.sleep(2) 
            except Exception as e:
                st.error(f"Erreur bloc {idx+1}: {e}")
            progress.progress((idx + 1) / len(morceaux))

        # AFFICHAGE
        st.subheader("📝 Résumé Global")
        st.info(" ".join(resultats_globaux["resumes"]))

        col1, col2 = st.columns(2)
        with col1:
            st.write("**👤 Personnages**")
            for p in sorted(resultats_globaux["personnages"]):
                st.markdown(f'<span class="tag">{p}</span>', unsafe_allow_html=True)
        with col2:
            st.write("**🧠 Thèmes & Traumas**")
            for t in sorted(resultats_globaux["traumas"]):
                st.markdown(f'<span class="tag">{t}</span>', unsafe_allow_html=True)
