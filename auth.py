"""
Module d'authentification utilisant Supabase Auth
"""
import os
from typing import Optional, Dict
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

# Schémas Pydantic pour les requêtes d'authentification
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    new_password: str

# Configuration du bearer token
security = HTTPBearer()

class SupabaseAuth:
    """Classe pour gérer l'authentification avec Supabase"""
    
    def __init__(self):
        """Initialise le client Supabase pour l'authentification"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Les variables d'environnement SUPABASE_URL et SUPABASE_ANON_KEY doivent être définies")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        
        # Client avec service_role pour bypasser RLS (pour opérations administratives)
        self.admin_client: Client = None
        if supabase_service_key:
            self.admin_client = create_client(supabase_url, supabase_service_key)
    
    def sign_up(self, email: str, password: str) -> Dict:
        """
        Inscription d'un nouvel utilisateur
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe de l'utilisateur
            
        Returns:
            Dict contenant les informations de l'utilisateur et le token d'accès
        """
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Échec de l'inscription. Vérifiez vos informations."
                )
            
            # Créer l'utilisateur dans la table users pour la compatibilité avec le système existant
            # Utiliser admin_client si disponible pour bypasser RLS
            try:
                db_client = self.admin_client if self.admin_client else self.client
                db_client.table('users').insert({
                    'username': email,
                    'auth_user_id': response.user.id
                }).execute()
            except Exception as e:
                print(f"Erreur lors de la création de l'utilisateur dans la table users: {e}")
            
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "created_at": response.user.created_at
                },
                "session": {
                    "access_token": response.session.access_token if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None,
                    "expires_at": response.session.expires_at if response.session else None
                }
            }
        except Exception as e:
            if "User already registered" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Un utilisateur avec cet email existe déjà."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors de l'inscription: {str(e)}"
            )
    
    def login(self, email: str, password: str) -> Dict:
        """
        Connexion d'un utilisateur existant
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe de l'utilisateur
            
        Returns:
            Dict contenant les informations de l'utilisateur et le token d'accès
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not response.user or not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou mot de passe incorrect."
                )
            
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "created_at": response.user.created_at
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Erreur lors de la connexion: {str(e)}"
            )
    
    def logout(self, token: str) -> Dict:
        """
        Déconnexion d'un utilisateur
        
        Args:
            token: Token d'accès de l'utilisateur
            
        Returns:
            Message de confirmation
        """
        try:
            # Configurer le token pour cette requête
            self.client.auth.sign_out()
            return {"message": "Déconnexion réussie"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors de la déconnexion: {str(e)}"
            )
    
    def get_user_from_token(self, token: str) -> Dict:
        """
        Récupère les informations de l'utilisateur à partir du token
        
        Args:
            token: Token d'accès JWT
            
        Returns:
            Dict contenant les informations de l'utilisateur
        """
        try:
            # Vérifier le token avec Supabase
            response = self.client.auth.get_user(token)
            
            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide ou expiré."
                )
            
            return {
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token invalide: {str(e)}"
            )
    
    def refresh_session(self, refresh_token: str) -> Dict:
        """
        Rafraîchit la session avec le refresh token
        
        Args:
            refresh_token: Token de rafraîchissement
            
        Returns:
            Nouvelle session avec access_token
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)
            
            if not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token de rafraîchissement invalide."
                )
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Erreur lors du rafraîchissement: {str(e)}"
            )
    
    def reset_password_request(self, email: str) -> Dict:
        """
        Envoie un email de réinitialisation de mot de passe
        
        Args:
            email: Email de l'utilisateur
            
        Returns:
            Message de confirmation
        """
        try:
            self.client.auth.reset_password_email(email)
            return {"message": "Email de réinitialisation envoyé. Vérifiez votre boîte mail."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors de la demande de réinitialisation: {str(e)}"
            )
    
    def update_password(self, token: str, new_password: str) -> Dict:
        """
        Met à jour le mot de passe de l'utilisateur
        
        Args:
            token: Token d'accès de l'utilisateur
            new_password: Nouveau mot de passe
            
        Returns:
            Message de confirmation
        """
        try:
            # Vérifier d'abord que l'utilisateur est authentifié
            self.get_user_from_token(token)
            
            # Mettre à jour le mot de passe
            self.client.auth.update_user({"password": new_password})
            
            return {"message": "Mot de passe mis à jour avec succès"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors de la mise à jour du mot de passe: {str(e)}"
            )

# Fonction de dépendance pour protéger les routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dépendance FastAPI pour récupérer l'utilisateur actuel depuis le token
    
    Args:
        credentials: Credentials HTTP Bearer
        
    Returns:
        Dict contenant les informations de l'utilisateur
    """
    auth = SupabaseAuth()
    token = credentials.credentials
    return auth.get_user_from_token(token)

