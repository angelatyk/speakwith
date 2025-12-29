#!/usr/bin/env python3
"""
Build a Vertex AI vector database from MongoDB historical figure data.
Extracts Q&A pairs and creates embeddings for semantic search.
"""
import os
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from typing import List, Dict
import json

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'talkwith')

# Vertex AI configuration
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

# Try to import Vertex AI, fallback to ChromaDB if not available
try:
    from google.cloud import aiplatform
    from vertexai.preview.language_models import TextEmbeddingModel
    VERTEX_AI_AVAILABLE = True
    if PROJECT_ID:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
except ImportError:
    print("Warning: Vertex AI not available. Using ChromaDB's default embeddings.")
    VERTEX_AI_AVAILABLE = False
except Exception as e:
    print(f"Warning: Vertex AI initialization failed: {e}. Using ChromaDB's default embeddings.")
    VERTEX_AI_AVAILABLE = False

def get_vertex_embedding(text: str) -> List[float]:
    """Get embedding from Vertex AI Text Embedding model"""
    if not VERTEX_AI_AVAILABLE:
        raise ValueError("Vertex AI is not available. Please set GOOGLE_CLOUD_PROJECT_ID.")
    
    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
    embeddings = model.get_embeddings([text])
    return embeddings[0].values

def extract_qa_pairs_from_mongodb() -> List[Dict]:
    """
    Extract all question-answer pairs from MongoDB historical figures.
    Returns a list of dictionaries with person_name, question, answer, and metadata.
    """
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db['historical_figures']
    
    qa_pairs = []
    
    # Get all historical figures
    figures = collection.find({})
    
    for figure in figures:
        person_name = figure.get('person_name', 'Unknown')
        person_id = str(figure.get('_id', ''))
        answers = figure.get('answers', {})
        questions = figure.get('questions', [])
        
        # Create Q&A pairs
        for question, answer in answers.items():
            if answer and answer.strip():  # Only include non-empty answers
                qa_pairs.append({
                    'person_name': person_name,
                    'person_id': person_id,
                    'question': question,
                    'answer': answer,
                    'text': f"Question: {question}\nAnswer: {answer}",  # Combined text for embedding
                    'metadata': {
                        'person_name': person_name,
                        'person_id': person_id,
                        'question': question
                    }
                })
    
    print(f"Extracted {len(qa_pairs)} Q&A pairs from MongoDB")
    return qa_pairs

def build_vector_database(use_vertex_ai: bool = True):
    """
    Build a vector database from MongoDB data.
    If use_vertex_ai is True and available, uses Vertex AI embeddings.
    Otherwise, uses ChromaDB's default embeddings.
    """
    # Extract data from MongoDB
    qa_pairs = extract_qa_pairs_from_mongodb()
    
    if not qa_pairs:
        print("No Q&A pairs found in MongoDB. Please add historical figures first.")
        return
    
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get or create collection
    collection_name = "historical_figures_qa"
    try:
        collection = chroma_client.get_collection(name=collection_name)
        print(f"Using existing collection: {collection_name}")
        # Clear existing data to rebuild
        chroma_client.delete_collection(name=collection_name)
        collection = chroma_client.create_collection(name=collection_name)
        print(f"Cleared and recreated collection: {collection_name}")
    except:
        collection = chroma_client.create_collection(name=collection_name)
        print(f"Created new collection: {collection_name}")
    
    # Process Q&A pairs in batches
    batch_size = 100
    total_batches = (len(qa_pairs) + batch_size - 1) // batch_size
    
    print(f"\nProcessing {len(qa_pairs)} Q&A pairs in {total_batches} batches...")
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(qa_pairs))
        batch = qa_pairs[start_idx:end_idx]
        
        print(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch)} items)...")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for idx, qa in enumerate(batch):
            doc_id = f"{qa['person_id']}_{hash(qa['question'])}"
            ids.append(doc_id)
            documents.append(qa['text'])
            metadatas.append(qa['metadata'])
            
            # Get embedding
            if use_vertex_ai and VERTEX_AI_AVAILABLE:
                try:
                    embedding = get_vertex_embedding(qa['text'])
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"Warning: Failed to get Vertex AI embedding: {e}")
                    print("Falling back to ChromaDB default embeddings for this batch...")
                    use_vertex_ai = False
                    embeddings = None
            else:
                embeddings = None  # Let ChromaDB generate embeddings
        
        # Add to collection
        if embeddings:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
        else:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
    
    print(f"\n✅ Vector database built successfully!")
    print(f"   Collection: {collection_name}")
    print(f"   Total documents: {len(qa_pairs)}")
    print(f"   Embeddings: {'Vertex AI' if use_vertex_ai and VERTEX_AI_AVAILABLE else 'ChromaDB default'}")
    print(f"   Location: ./chroma_db")

def query_vector_database(query_text: str, n_results: int = 5, person_name: str = None):
    """
    Query the vector database for similar Q&A pairs.
    
    Args:
        query_text: The search query
        n_results: Number of results to return
        person_name: Optional filter by person name
    """
    chroma_client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        collection = chroma_client.get_collection(name="historical_figures_qa")
    except:
        print("Vector database not found. Please run build_vector_database() first.")
        return []
    
    # Build query
    where = {}
    if person_name:
        where['person_name'] = person_name
    
    # Get embedding for query if using Vertex AI
    query_embedding = None
    if VERTEX_AI_AVAILABLE:
        try:
            query_embedding = get_vertex_embedding(query_text)
        except:
            pass
    
    # Query
    if query_embedding:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where if where else None
        )
    else:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where if where else None
        )
    
    return results

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'query':
        # Query mode
        query = sys.argv[2] if len(sys.argv) > 2 else "What was their personality like?"
        person = sys.argv[3] if len(sys.argv) > 3 else None
        
        print(f"Querying: {query}")
        if person:
            print(f"Filtering by person: {person}")
        
        results = query_vector_database(query, n_results=3, person_name=person)
        
        if results and results['documents']:
            print(f"\nFound {len(results['documents'][0])} results:\n")
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                print(f"{i}. {metadata['person_name']}")
                print(f"   Question: {metadata['question']}")
                print(f"   Answer: {doc[:200]}...")
                print()
        else:
            print("No results found.")
    else:
        # Build mode
        use_vertex = VERTEX_AI_AVAILABLE and PROJECT_ID is not None
        if use_vertex:
            print("Using Vertex AI embeddings...")
        else:
            print("Using ChromaDB default embeddings (Vertex AI not configured)")
            print("To use Vertex AI, set GOOGLE_CLOUD_PROJECT_ID in your .env file")
        
        build_vector_database(use_vertex_ai=use_vertex)

