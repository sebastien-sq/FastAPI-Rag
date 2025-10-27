from fastapi import FastAPI, HTTPException, Depends
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mistralai import Mistral
from pinecone import Pinecone
from dotenv import load_dotenv
from database import ConversationDB
from auth import (
    SupabaseAuth, 
    SignUpRequest, 
    LoginRequest, 
    PasswordResetRequest, 
    UpdatePasswordRequest,
    get_current_user
)
import os

load_dotenv()
mistral_api_key = os.getenv("MISTRAL_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_index = os.getenv("PINECONE_INDEX_NAME")

# Initialiser les clients
client = Mistral(api_key=mistral_api_key)
pc = Pinecone(api_key=pinecone_api_key)  
index = pc.Index(pinecone_index)  
db = ConversationDB()
auth = SupabaseAuth()
app = FastAPI()



# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
          "https://fastapi-rag-jwjn.onrender.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "https://react-rag-interface.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour les requêtes
class QuestionRequest(BaseModel):
    question: str
    email: str  # Email de l'utilisateur
    conversation_id: int = None

class ConversationRequest(BaseModel):
    email: str  # Email de l'utilisateur
    title: str = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ==================== ROUTES D'AUTHENTIFICATION ====================

@app.post("/auth/signup")
def signup(request: SignUpRequest):
    """
    Inscription d'un nouvel utilisateur avec email et mot de passe
    
    Returns:
        - user: Informations de l'utilisateur créé
        - session: Token d'accès et de rafraîchissement
    """
    try:
        result = auth.sign_up(request.email, request.password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
def login(request: LoginRequest):
    """
    Connexion d'un utilisateur existant
    
    Returns:
        - user: Informations de l'utilisateur
        - session: Token d'accès et de rafraîchissement
    """
    try:
        result = auth.login(request.email, request.password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """
    Déconnexion de l'utilisateur actuel
    Nécessite un token Bearer dans les headers
    """
    try:
        result = auth.logout(current_user.get("id"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/refresh")
def refresh_token(request: RefreshTokenRequest):
    """
    Rafraîchit le token d'accès avec un refresh token
    
    Args:
        refresh_token: Token de rafraîchissement obtenu lors de la connexion
    
    Returns:
        Nouvelle session avec access_token et refresh_token
    """
    try:
        result = auth.refresh_session(request.refresh_token)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/reset-password")
def reset_password(request: PasswordResetRequest):
    """
    Envoie un email de réinitialisation de mot de passe
    
    Args:
        email: Email de l'utilisateur
    
    Returns:
        Message de confirmation
    """
    try:
        result = auth.reset_password_request(request.email)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/update-password")
def update_password(
    request: UpdatePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Met à jour le mot de passe de l'utilisateur connecté
    Nécessite un token Bearer dans les headers
    
    Args:
        new_password: Nouveau mot de passe
    
    Returns:
        Message de confirmation
    """
    try:
        # Le token est déjà vérifié par get_current_user
        result = auth.update_password(current_user.get("id"), request.new_password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur connecté
    Nécessite un token Bearer dans les headers
    
    Returns:
        Informations de l'utilisateur
    """
    return current_user

# ==================== ROUTES EXISTANTES ====================

@app.post("/ingest")
def ingest(file: UploadFile = File(...)):
    return {"message": "File uploaded successfully"}

@app.post("/delete")
def delete(index_name: str):
    return {"message": "Index deleted successfully"}

@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        # Créer ou récupérer l'utilisateur par email
        user_id = db.create_user(request.email)
        
        # Créer une nouvelle conversation si nécessaire
        if request.conversation_id is None:
            conversation_id = db.create_conversation(user_id, request.question[:50])
        else:
            conversation_id = request.conversation_id
        
        # Enregistrer la question de l'utilisateur
        db.add_message(conversation_id, "user", request.question)
        
        # Créer l'embedding de la requête
        query_embedding = client.embeddings.create(
            model="mistral-embed",
            inputs=[request.question]  
        ).data[0].embedding
        
        # Recherche par similarité dans Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )
        
        if not results['matches']:
            answer = "Aucun document pertinent trouvé."
            db.add_message(conversation_id, "assistant", answer)
            return {
                "answer": answer,
                "conversation_id": conversation_id,
                "email": request.email
            }
        
        # Construire le contexte
        context = "\n".join([match['metadata']['text'] for match in results['matches']])
        
        prompt = f"""Based on the following context, answer the question:

Context: {context}

Question: {request.question}

Answer:"""

        response = client.chat.complete(
            model="mistral-small-2506",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content
        
        # Enregistrer la réponse de l'assistant
        db.add_message(conversation_id, "assistant", answer)

        return {
            "answer": answer,
            "conversation_id": conversation_id,
            "email": request.email
        }
    
    except Exception as e:
        return {"error": f"Erreur lors du traitement: {str(e)}"}

# Endpoints pour l'historique des conversations
@app.get("/conversations/{email}")
def get_conversations(email: str):
    """Récupère toutes les conversations d'un utilisateur par email"""
    try:
        user_id = db.get_user_by_username(email)
        if not user_id:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        conversations = db.get_conversations(user_id)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{email}/{conversation_id}")
def get_conversation_messages(email: str, conversation_id: int):
    """Récupère tous les messages d'une conversation par email"""
    try:
        user_id = db.get_user_by_username(email)
        if not user_id:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        messages = db.get_messages(conversation_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations")
def create_conversation(request: ConversationRequest):
    """Crée une nouvelle conversation pour un utilisateur"""
    try:
        user_id = db.create_user(request.email)
        conversation_id = db.create_conversation(user_id, request.title)
        return {
            "conversation_id": conversation_id,
            "email": request.email,
            "title": request.title
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int):
    """Supprime une conversation"""
    try:
        db.delete_conversation(conversation_id)
        return {"message": "Conversation supprimée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "RAG API avec Mistral et Pinecone"}  

@app.get("/health")
def health():
    return {"status": "healthy"}