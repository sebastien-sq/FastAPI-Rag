from database import ConversationDB

# Créer une instance de la base de données
db = ConversationDB()

# Créer un utilisateur de test
username = "user_test"
user_id = db.create_user(username)
print(f"[OK] Utilisateur cree : {username} (ID: {user_id})")

# Optionnel : Créer une conversation de test
conversation_id = db.create_conversation(user_id, "Conversation de test")
print(f"[OK] Conversation creee : ID {conversation_id}")

# Ajouter des messages de test
db.add_message(conversation_id, "user", "Bonjour, c'est un message de test")
db.add_message(conversation_id, "assistant", "Ceci est une reponse de test")
print(f"[OK] Messages de test ajoutes")

print(f"\n[SUCCESS] Utilisateur de test '{username}' cree avec succes !")
