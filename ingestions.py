import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from mistralai import Mistral
from pinecone import Pinecone
import time
import random

load_dotenv()
mistral_api_key = os.getenv("MISTRAL_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_index = os.getenv("PINECONE_INDEX_NAME")

# Initialiser les clients
client = Mistral(api_key=mistral_api_key)
vectorstore = None



def create_embeddings_in_batches(client, texts, batch_size=5, delay_between_batches=1.0):
    """Créer les embeddings par lots avec gestion du rate limit"""
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(texts) + batch_size - 1)//batch_size
        
        print(f"Processing batch {batch_num}/{total_batches}")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                embeddings_response = client.embeddings.create(
                    model="mistral-embed",
                    inputs=batch  # Correction: 'input' pas 'inputs'
                )
                batch_embeddings = [embedding.embedding for embedding in embeddings_response.data]
                all_embeddings.extend(batch_embeddings)
                print(f"✓ Batch {batch_num} completed successfully")
                break
                
            except Exception as e:
                error_msg = str(e)
                retry_count += 1
                
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    wait_time = delay_between_batches * (2 ** retry_count) + random.uniform(0, 1)
                    print(f"⚠ Rate limit hit on batch {batch_num}. Waiting {wait_time:.1f}s before retry {retry_count}/{max_retries}")
                    time.sleep(wait_time)
                    
                elif "too many tokens" in error_msg.lower():
                    if batch_size > 1:
                        print(f"⚠ Too many tokens. Reducing batch size from {batch_size} to {batch_size//2}")
                        return create_embeddings_in_batches(client, texts, batch_size//2, delay_between_batches)
                    else:
                        print(f"✗ Cannot reduce batch size further. Error: {e}")
                        raise e
                        
                else:
                    if retry_count < max_retries:
                        wait_time = delay_between_batches * retry_count
                        print(f"⚠ Error on batch {batch_num}: {e}. Retrying in {wait_time:.1f}s")
                        time.sleep(wait_time)
                    else:
                        print(f"✗ Max retries reached for batch {batch_num}. Error: {e}")
                        raise e
        
        if batch_num < total_batches:
            time.sleep(delay_between_batches)
    
    return all_embeddings

try:
    # Loading documents
    print("Loading documents...")
    loader = PyPDFLoader("data/harrypotter.pdf")
    documents = loader.load()
    print("Documents loaded successfully")

    # Split du document en chunks
    print("Splitting documents into chunks...")
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Documents split into {len(chunks)} chunks successfully")

    # Créer les embeddings avec Mistral
    print("Creating embeddings with Mistral...")
    texts = [chunk.page_content for chunk in chunks]
    embeddings_list = create_embeddings_in_batches(client, texts, batch_size=5)
    print(f"Created {len(embeddings_list)} embeddings successfully")
    
    # Initialiser Pinecone et envoyer les données
    print("Connecting to Pinecone...")
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index(pinecone_index)
    
    # Préparer les données pour Pinecone
    print("Uploading to Pinecone...")
    vectors_to_upload = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
        metadata = {
            "text": chunk.page_content,
            "source": chunk.metadata.get("source", "unknown")
        }
        vectors_to_upload.append({
            "id": f"doc_{i}",
            "values": embedding,
            "metadata": metadata
        })
    
    # Upload par lots de 100
    for i in range(0, len(vectors_to_upload), 100):
        batch = vectors_to_upload[i:i+100]
        index.upsert(vectors=batch)
        print(f"Uploaded batch {i//100 + 1}/{(len(vectors_to_upload) + 99)//100}")
    
    print("Documents added to Pinecone successfully")
    
    # Créer le vectorstore pour les requêtes
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=pinecone_index,
        embedding=None  # On utilisera Mistral pour les queries
    )

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test du RAG avec Mistral
if vectorstore:
    print("Testing the RAG system...")
    query = "What is the main character of the Harry Potter series?"
    
    # Créer l'embedding de la requête
    query_embedding = client.embeddings.create(
        model="mistral-embed",
        inputs=[query]
    ).data[0].embedding
    
    # Recherche par similarité dans Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=10,
        include_metadata=True
    )
    
    print(f"Found {len(results['matches'])} relevant documents")
    
    # Construire le contexte
    context = "\n".join([match['metadata']['text'] for match in results['matches']])
    
    prompt = f"""Based on the following context, answer the question:

Context: {context}

Question: {query}

Answer:"""

    response = client.chat.completions.create(
        model="mistral-small-2506",
        messages=[{"role": "user", "content": prompt}]
    )

    print(f"Question: {query}")
    print(f"Answer: {response.choices[0].message.content}")
else:
    print("Vectorstore not created, cannot test RAG")