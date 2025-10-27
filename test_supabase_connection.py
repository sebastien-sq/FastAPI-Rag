#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test de connexion à Supabase
Vérifie que :
- Les variables d'environnement sont bien configurées
- La connexion à Supabase fonctionne
- Les tables existent
"""

import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_env_variables():
    """Vérifie que les variables d'environnement sont définies"""
    print("=" * 60)
    print("1. VÉRIFICATION DES VARIABLES D'ENVIRONNEMENT")
    print("=" * 60)
    
    required_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),        
        "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
        "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
        "PINECONE_INDEX_NAME": os.getenv("PINECONE_INDEX_NAME"),
    }
    
    all_ok = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Masquer partiellement les clés sensibles
            if "KEY" in var_name or "SUPABASE" in var_name:
                display_value = var_value[:10] + "..." + var_value[-5:] if len(var_value) > 15 else "***"
            else:
                display_value = var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: MANQUANT")
            all_ok = False
    
    print()
    return all_ok

def test_supabase_connection():
    """Teste la connexion à Supabase"""
    print("=" * 60)
    print("2. TEST DE CONNEXION À SUPABASE")
    print("=" * 60)
    
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        print(f"🔗 Tentative de connexion à {supabase_url}...")
        client = create_client(supabase_url, supabase_key)
        print("✅ Connexion à Supabase réussie !")
        print()
        return client
    except ImportError:
        print("❌ Le package 'supabase' n'est pas installé.")
        print("   Exécutez: pip install -r requirements.txt")
        print()
        return None
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        print()
        return None

def test_tables(client):
    """Vérifie que les tables existent"""
    print("=" * 60)
    print("3. VÉRIFICATION DES TABLES")
    print("=" * 60)
    
    tables = ["users", "conversations", "messages"]
    all_ok = True
    
    for table in tables:
        try:
            # Tenter une requête simple pour vérifier l'existence de la table
            result = client.table(table).select("*").limit(1).execute()
            print(f"✅ Table '{table}' existe et est accessible {result}")
        except Exception as e:
            print(f"❌ Problème avec la table '{table}': {e}")
            all_ok = False
    
    print()
    return all_ok

def test_crud_operations(client):
    """Teste les opérations CRUD de base"""
    print("=" * 60)
    print("4. TEST DES OPÉRATIONS CRUD")
    print("=" * 60)
    
    test_username = "test_connection_user"
    
    try:
        # CREATE - Créer un utilisateur de test
        print(f"📝 Création de l'utilisateur '{test_username}'...")
        result = client.table('users').insert({'username': test_username}).execute()
        user_id = result.data[0]['id']
        print(f"✅ Utilisateur créé avec l'ID: {user_id}")
        
        # READ - Lire l'utilisateur
        print(f"📖 Lecture de l'utilisateur...")
        result = client.table('users').select('*').eq('username', test_username).execute()
        if result.data:
            print(f"✅ Utilisateur trouvé: {result.data[0]}")
        
        # UPDATE - Pas vraiment nécessaire pour ce test
        
        # DELETE - Nettoyer l'utilisateur de test
        print(f"🗑️  Suppression de l'utilisateur de test...")
        client.table('users').delete().eq('username', test_username).execute()
        print(f"✅ Utilisateur de test supprimé")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests CRUD : {e}")
        print()
        return False

def main():
    """Fonction principale"""
    print("\n" + "🚀 " * 20)
    print("TEST DE CONFIGURATION SUPABASE")
    print("🚀 " * 20 + "\n")
    
    # Test 1 : Variables d'environnement
    if not test_env_variables():
        print("❌ ÉCHEC : Les variables d'environnement ne sont pas toutes définies.")
        print("📝 Consultez le fichier 'ENV_VARIABLES.md' pour plus d'informations.")
        sys.exit(1)
    
    # Test 2 : Connexion Supabase
    client = test_supabase_connection()
    if not client:
        print("❌ ÉCHEC : Impossible de se connecter à Supabase.")
        print("📝 Vérifiez vos identifiants SUPABASE_URL et SUPABASE_KEY.")
        sys.exit(1)
    
    # Test 3 : Vérification des tables
    if not test_tables(client):
        print("❌ ÉCHEC : Les tables ne sont pas toutes présentes.")
        print("📝 Exécutez le script 'supabase_schema.sql' dans l'éditeur SQL de Supabase.")
        sys.exit(1)
    
    # Test 4 : Opérations CRUD
    if not test_crud_operations(client):
        print("❌ ÉCHEC : Les opérations CRUD ne fonctionnent pas correctement.")
        print("📝 Vérifiez les politiques RLS dans Supabase.")
        sys.exit(1)
    
    # Succès !
    print("=" * 60)
    print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS ! 🎉")
    print("=" * 60)
    print()
    print("✅ Votre configuration Supabase est correcte !")
    print("✅ Vous pouvez maintenant utiliser l'application.")
    print()
    print("Pour tester avec un utilisateur complet, exécutez :")
    print("  python create_test_user.py")
    print()
    print("Pour lancer l'application, exécutez :")
    print("  uvicorn main:app --reload")
    print()

if __name__ == "__main__":
    main()

