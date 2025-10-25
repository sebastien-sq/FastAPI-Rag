# Guide d'utilisation de l'API RAG avec historique des conversations

## Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Démarrer l'API
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

## Base de données SQLite

La base de données `conversations.db` est créée automatiquement avec les tables :
- `users` : Utilisateurs
- `conversations` : Conversations
- `messages` : Messages des conversations

## Fonctionnalités

✅ **Historique complet** : Toutes les questions et réponses sont sauvegardées
✅ **Multi-utilisateurs** : Chaque utilisateur a son propre historique
✅ **Conversations persistantes** : Les conversations continuent même après redémarrage
✅ **Recherche contextuelle** : Le RAG utilise les documents uploadés dans Pinecone
✅ **API RESTful** : Interface simple pour intégrer dans d'autres applications
