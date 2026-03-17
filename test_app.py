#!/usr/bin/env python3
"""
Test script pour valider l'app Mistral
"""
import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test des imports"""
    print("🔍 Test des imports...")
    try:
        import streamlit as st
        print("✅ Streamlit importé")
    except ImportError:
        print("❌ Streamlit non trouvé")
        return False

    try:
        import mistralai
        print("✅ Mistralai importé")
    except ImportError:
        print("❌ Mistralai non trouvé")
        return False

    return True

def test_mistral_api():
    """Test de l'API Mistral"""
    print("\n🔍 Test de l'API Mistral...")
    try:
        import mistralai
        client = mistralai.Mistral(api_key='test_key')
        print("✅ Client Mistral créé")

        # Test de la structure
        assert hasattr(client, 'chat'), "Client n'a pas de méthode chat"
        assert hasattr(client.chat, 'complete'), "Chat n'a pas de méthode complete"
        assert hasattr(client.chat, 'stream'), "Chat n'a pas de méthode stream"
        print("✅ Structure API valide")

        return True
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return False

def test_app_structure():
    """Test de la structure de l'app"""
    print("\n🔍 Test de la structure de l'app...")
    try:
        import app
        print("✅ App importée")

        # Vérifier les variables importantes
        assert hasattr(app, 'MISTRAL_AVAILABLE'), "MISTRAL_AVAILABLE manquant"
        print(f"✅ MISTRAL_AVAILABLE: {app.MISTRAL_AVAILABLE}")

        return True
    except Exception as e:
        print(f"❌ Erreur app: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test de l'app Mistral\n")

    tests = [
        ("Imports", test_imports),
        ("API Mistral", test_mistral_api),
        ("Structure App", test_app_structure),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erreur dans {name}: {e}")
            results.append((name, False))

    print("\n" + "="*50)
    print("📊 RÉSULTATS DES TESTS:")

    all_passed = True
    for name, passed in results:
        status = "✅ PASSÉ" if passed else "❌ ÉCHOUÉ"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*50)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("💡 L'app est prête à être utilisée.")
        print("   Lancez: streamlit run app.py")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("   Vérifiez les dépendances et la configuration.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())