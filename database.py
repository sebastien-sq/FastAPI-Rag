import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class ConversationDB:
    def __init__(self):
        """Initialise la connexion à Supabase"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Les variables d'environnement SUPABASE_URL et SUPABASE_ANON_KEY doivent être définies")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        
        # Client avec service_role pour bypasser RLS (optionnel)
        self.admin_client: Client = None
        if supabase_service_key:
            self.admin_client = create_client(supabase_url, supabase_service_key)
    
    def create_user(self, email: str) -> int:
        """Crée un nouvel utilisateur avec son email et retourne son ID"""
        try:
            # Valider le format email basique
            if '@' not in email or '.' not in email.split('@')[1]:
                raise ValueError(f"Format email invalide: {email}")
            
            # Utiliser admin_client si disponible pour bypasser RLS
            db_client = self.admin_client if self.admin_client else self.client
            
            # Vérifier si l'utilisateur existe déjà
            existing_user = db_client.table('users').select('id').eq('username', email).execute()
            
            if existing_user.data:
                return existing_user.data[0]['id']
            
            # Créer un nouvel utilisateur avec l'email
            result = db_client.table('users').insert({
                'username': email
            }).execute()
            
            return result.data[0]['id']
        except Exception as e:
            print(f"Erreur lors de la création de l'utilisateur: {e}")
            raise
    
    def create_conversation(self, user_id: int, title: str = None) -> int:
        """Crée une nouvelle conversation et retourne son ID"""
        try:
            # Utiliser admin_client si disponible pour bypasser RLS
            db_client = self.admin_client if self.admin_client else self.client
            
            result = db_client.table('conversations').insert({
                'user_id': user_id,
                'title': title
            }).execute()
            
            return result.data[0]['id']
        except Exception as e:
            print(f"Erreur lors de la création de la conversation: {e}")
            raise
    
    def add_message(self, conversation_id: int, role: str, content: str):
        """Ajoute un message à une conversation"""
        try:
            # Utiliser admin_client si disponible pour bypasser RLS
            db_client = self.admin_client if self.admin_client else self.client
            
            db_client.table('messages').insert({
                'conversation_id': conversation_id,
                'role': role,
                'content': content
            }).execute()
        except Exception as e:
            print(f"Erreur lors de l'ajout du message: {e}")
            raise
    
    def get_conversations(self, user_id: int) -> List[Dict]:
        """Récupère toutes les conversations d'un utilisateur"""
        try:
            # Utiliser admin_client si disponible pour bypasser RLS
            db_client = self.admin_client if self.admin_client else self.client
            
            result = db_client.table('conversations')\
                .select('id, title, created_at')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            conversations = []
            for row in result.data:
                conversations.append({
                    'id': row['id'],
                    'title': row['title'],
                    'created_at': row['created_at']
                })
            
            return conversations
        except Exception as e:
            print(f"Erreur lors de la récupération des conversations: {e}")
            raise
    
    def get_messages(self, conversation_id: int) -> List[Dict]:
        """Récupère tous les messages d'une conversation"""
        try:
            # Utiliser admin_client si disponible pour bypasser RLS
            db_client = self.admin_client if self.admin_client else self.client
            
            result = db_client.table('messages')\
                .select('role, content, timestamp')\
                .eq('conversation_id', conversation_id)\
                .order('timestamp', desc=False)\
                .execute()
            
            messages = []
            for row in result.data:
                messages.append({
                    'role': row['role'],
                    'content': row['content'],
                    'timestamp': row['timestamp']
                })
            
            return messages
        except Exception as e:
            print(f"Erreur lors de la récupération des messages: {e}")
            raise
    
    def get_user_by_username(self, email: str) -> Optional[int]:
        """Récupère l'ID d'un utilisateur par son email"""
        try:
            # Utiliser admin_client si disponible pour bypasser RLS
            db_client = self.admin_client if self.admin_client else self.client
            
            result = db_client.table('users')\
                .select('id')\
                .eq('username', email)\
                .execute()
            
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'utilisateur: {e}")
            raise
    
    def delete_conversation(self, conversation_id: int):
        """Supprime une conversation et tous ses messages"""
        try:
            # Utiliser admin_client si disponible pour bypasser RLS
            db_client = self.admin_client if self.admin_client else self.client
            
            # Supprimer d'abord les messages (grâce au CASCADE dans Supabase, cela peut être automatique)
            db_client.table('messages').delete().eq('conversation_id', conversation_id).execute()
            
            # Puis la conversation
            db_client.table('conversations').delete().eq('id', conversation_id).execute()
        except Exception as e:
            print(f"Erreur lors de la suppression de la conversation: {e}")
            raise
