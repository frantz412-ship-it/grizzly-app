import streamlit as st
import datetime
try:
    import ntplib
    NTP_AVAILABLE = True
except ImportError:
    NTP_AVAILABLE = False

# === Import Mistral ===
try:
    import mistralai
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

# === Configuration Streamlit ===
st.set_page_config(page_title="Mistral Chat", layout="wide")
st.title("💬 Assistant Mistral")

def sync_time():
    """Synchronise l'heure avec un serveur NTP"""
    if NTP_AVAILABLE:
        try:
            client = ntplib.NTPClient()
            response = client.request('pool.ntp.org', version=3)
            return datetime.datetime.fromtimestamp(response.tx_time)
        except Exception as e:
            st.error(f"Erreur de synchronisation NTP: {e}")
            return datetime.datetime.now()
    else:
        st.warning("NTP non disponible. Installez ntplib: pip install ntplib")
        return datetime.datetime.now()

# === Initialisation État Session ===
def init_session_state():
    """Initialise les variables de session"""
    if "client" not in st.session_state:
        st.session_state.client = None
    if "connected" not in st.session_state:
        st.session_state.connected = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "error" not in st.session_state:
        st.session_state.error = None

init_session_state()

# === Sidebar Configuration ===
with st.sidebar:
    st.subheader("⚙️ Configuration")
    
    if not MISTRAL_AVAILABLE:
        st.error("Mistral non installé. Exécutez: `pip install mistralai`")
    else:
        api_key = st.text_input("🔑 Clé API Mistral", type="password", key="api_key_input")
        model = st.selectbox("🤖 Modèle", ["mistral-tiny", "mistral-small", "mistral-medium"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔗 Connecter", use_container_width=True):
                if not api_key:
                    st.session_state.error = "Veuillez entrer une clé API"
                    st.error(st.session_state.error)
                else:
                    try:
                        client = mistralai.Mistral(api_key=api_key)
                        # Test connexion avec une requête simple
                        response = client.chat.complete(
                            model=model,
                            messages=[{"role": "user", "content": "Hello"}]
                        )
                        st.session_state.client = client
                        st.session_state.connected = True
                        st.session_state.error = None
                        st.success("✅ Connecté!")
                    except Exception as e:
                        st.session_state.error = str(e)
                        st.session_state.connected = False
                        st.error(f"Erreur: {str(e)[:100]}")
        
        with col2:
            if st.button("🔌 Déconnecter", use_container_width=True):
                st.session_state.client = None
                st.session_state.connected = False
                st.session_state.messages = []
                st.session_state.error = None
                st.rerun()
        
        # Status
        if st.session_state.connected:
            st.success("🟢 Connecté au modèle: " + model)
        else:
            st.warning("🔴 Non connecté")
    
    # Section Synchronisation Temps
    st.subheader("⏰ Synchronisation Temps")
    current_time = datetime.datetime.now()
    st.write(f"Heure actuelle: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if st.button("🔄 Synchroniser l'heure", use_container_width=True):
        synced_time = sync_time()
        st.success(f"Heure synchronisée: {synced_time.strftime('%Y-%m-%d %H:%M:%S')}")
        # Note: Cela ne change pas l'heure système, juste pour affichage

# === Chat Principal ===
if not MISTRAL_AVAILABLE:
    st.info("Installez Mistral pour activer le chat")
elif not st.session_state.connected:
    st.info("👈 Connectez-vous via la barre latérale pour commencer")
else:
    # Afficher historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "timestamp" in msg:
                timestamp_str = msg["timestamp"].strftime("%H:%M:%S")
                st.markdown(f"**{timestamp_str}** - {msg['content']}")
            else:
                st.markdown(msg["content"])
    
    # Entrée utilisateur
    if prompt := st.chat_input("Écrivez votre message..."):
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.datetime.now()
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Réponse Mistral
        with st.chat_message("assistant"):
            try:
                response_placeholder = st.empty()
                full_response = ""
                
                # Filtrer les messages pour l'API (seulement role et content)
                api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
                
                for chunk in st.session_state.client.chat.stream(
                    model=model,
                    messages=api_messages
                ):
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response,
                    "timestamp": datetime.datetime.now()
                })
            
            except Exception as e:
                st.error(f"Erreur: {str(e)}")
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()
