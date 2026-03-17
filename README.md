# Assistant Mistral - Guide d'utilisation

## 🚀 Démarrage rapide

1. **Installer les dépendances**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Lancer l'application**:
   ```bash
   streamlit run app.py
   ```

3. **Utiliser l'app**:
   - Entrez votre clé API Mistral dans la barre latérale
   - Choisissez un modèle (mistral-tiny, mistral-small, mistral-medium)
   - Cliquez sur "🔗 Connecter" pour tester la connexion
   - Commencez à discuter !

## 🔧 Configuration

### Variables d'environnement (optionnel)
Vous pouvez définir votre clé API dans les variables d'environnement :
```bash
export MISTRAL_API_KEY="votre_clé_ici"
```

### Modèles disponibles
- **mistral-tiny**: Modèle rapide et léger
- **mistral-small**: Bon équilibre performance/qualité
- **mistral-medium**: Haute qualité (plus lent)

## 🐛 Dépannage

### "Mistral non installé"
```bash
pip install mistralai==1.2.6
```

### Erreur de connexion
- Vérifiez votre clé API Mistral
- Assurez-vous d'avoir une connexion internet
- Vérifiez les limites de quota de votre compte

### Erreur de streaming
- Le streaming peut échouer avec certaines configurations réseau
- L'app basculera automatiquement sur le mode non-streaming

## 🧪 Tests

Pour vérifier que tout fonctionne :
```bash
python test_app.py
```

## 📋 Fonctionnalités

- ✅ Interface Streamlit moderne
- ✅ Gestion d'erreurs robuste
- ✅ Streaming en temps réel
- ✅ Historique des conversations
- ✅ Support multi-modèles
- ✅ Test de connexion automatique
- ✅ Mode hors-ligne (sans Mistral)

## 🔄 API Mistral utilisée

L'app utilise la nouvelle API Mistral (v1.2.6) :
- `mistralai.Mistral()` pour le client
- `client.chat.complete()` pour les réponses simples
- `client.chat.stream()` pour le streaming

Compatible avec les modèles : mistral-tiny, mistral-small, mistral-medium.