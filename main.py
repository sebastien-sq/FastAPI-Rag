from fastapi import FastAPI, HTTPException
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mistralai import Mistral
from pinecone import Pinecone
from dotenv import load_dotenv
from database import ConversationDB
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
app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour les requêtes
class QuestionRequest(BaseModel):
    question: str
    username: str = "default_user"
    conversation_id: int = None

class ConversationRequest(BaseModel):
    username: str
    title: str = None

@app.post("/ingest")
def ingest(file: UploadFile = File(...)):
    return {"message": "File uploaded successfully"}

@app.post("/delete")
def delete(index_name: str):
    return {"message": "Index deleted successfully"}

@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        # Créer ou récupérer l'utilisateur
        user_id = db.create_user(request.username)
        
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
                "username": request.username
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
            "username": request.username
        }
    
    except Exception as e:
        return {"error": f"Erreur lors du traitement: {str(e)}"}

# Endpoints pour l'historique des conversations
@app.get("/conversations/{username}")
def get_conversations(username: str):
    """Récupère toutes les conversations d'un utilisateur"""
    try:
        user_id = db.get_user_by_username(username)
        if not user_id:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        conversations = db.get_conversations(user_id)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{username}/{conversation_id}")
def get_conversation_messages(username: str, conversation_id: int):
    """Récupère tous les messages d'une conversation"""
    try:
        user_id = db.get_user_by_username(username)
        if not user_id:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        messages = db.get_messages(conversation_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations")
def create_conversation(request: ConversationRequest):
    """Crée une nouvelle conversation"""
    try:
        user_id = db.create_user(request.username)
        conversation_id = db.create_conversation(user_id, request.title)
        return {
            "conversation_id": conversation_id,
            "username": request.username,
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