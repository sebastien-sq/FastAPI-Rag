# 🚀 FastAPI RAG - API de Chat Intelligent avec Historique

API RAG (Retrieval-Augmented Generation) avec gestion des conversations et recherche sémantique dans des documents.

## 🛠️ Stack Technique

- **Backend** : FastAPI (Python)
- **Base de données** : Supabase (PostgreSQL)
- **Vector Store** : Pinecone
- **Embeddings** : Mistral AI (`mistral-embed`)
- **LLM** : Mistral AI (`mistral-small-2506`)

## ⚙️ Configuration

Créez un fichier `.env` à la racine du projet :

```env
# API Keys Mistral
MISTRAL_API_KEY=your_mistral_api_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_pinecone_index_name_here

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

## 📦 Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer Supabase (exécuter supabase_schema.sql dans votre dashboard)

# 3. Tester la configuration
python test_supabase_connection.py

# 4. Démarrer l'API
uvicorn main:app --reload
```

## Endpoints disponibles

### 1. Poser une question au RAG
**POST** `/ask`

```json
{
    "question": "Qui est le personnage principal d'Harry Potter ?",
    "username": "utilisateur1",
    "conversation_id": null
}
```

**Réponse :**
```json
{
    "answer": "Le personnage principal d'Harry Potter est Harry Potter lui-même...",
    "conversation_id": 1,
    "username": "utilisateur1"
}
```

### 2. Créer une nouvelle conversation
**POST** `/conversations`

```json
{
    "username": "utilisateur1",
    "title": "Questions sur Harry Potter"
}
```

### 3. Récupérer les conversations d'un utilisateur
**GET** `/conversations/{username}`

**Réponse :**
```json
{
    "conversations": [
        {
            "id": 1,
            "title": "Questions sur Harry Potter",
            "created_at": "2024-01-15 10:30:00"
        }
    ]
}
```

### 4. Récupérer les messages d'une conversation
**GET** `/conversations/{username}/{conversation_id}`

**Réponse :**
```json
{
    "messages": [
        {
            "role": "user",
            "content": "Qui est le personnage principal d'Harry Potter ?",
            "timestamp": "2024-01-15 10:30:00"
        },
        {
            "role": "assistant",
            "content": "Le personnage principal d'Harry Potter est Harry Potter lui-même...",
            "timestamp": "2024-01-15 10:30:05"
        }
    ]
}
```

### 5. Supprimer une conversation
**DELETE** `/conversations/{conversation_id}`

## Exemples d'utilisation avec curl

### Poser une question
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Qui est le personnage principal d'\''Harry Potter ?",
    "username": "utilisateur1"
  }'
```

### Continuer une conversation existante
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quel est le nom de son meilleur ami ?",
    "username": "utilisateur1",
    "conversation_id": 1
  }'
```

### Récupérer l'historique
```bash
curl -X GET "http://localhost:8000/conversations/utilisateur1"
```

## 🗄️ Base de données Supabase

Les tables suivantes sont créées dans Supabase :
- **users** : Gestion des utilisateurs
- **conversations** : Historique des conversations
- **messages** : Messages (questions/réponses)

## ✨ Fonctionnalités

- ✅ **RAG intelligent** : Recherche sémantique dans vos documents via Pinecone
- ✅ **Historique complet** : Conversations sauvegardées dans Supabase
- ✅ **Multi-utilisateurs** : Isolation des données par utilisateur
- ✅ **API RESTful** : Endpoints simples et documentés
- ✅ **Scalable** : Base de données cloud avec Supabase
- ✅ **CORS configuré** : Prêt pour le frontend

## 📚 Documentation

- **API** : http://localhost:8000/docs (Swagger UI automatique)
- **Schéma SQL** : Voir `supabase_schema.sql`
- **Test** : Utiliser `test_supabase_connection.py` pour vérifier la config
