import os
import re
from typing import Dict, List

import google.generativeai as genai
from bson import ObjectId
from data.historical_figures_questions import HISTORICAL_FIGURE_QUESTIONS
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from gemini_service import (
    generate_elevenlabs_voice_summary,
    get_available_gemini_model,
    query_gemini_for_historical_figure,
)
from mongo import check_connection, get_db
from repositories import historical_figures as hf_repo

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize database
db = get_db()
HISTORICAL_FIGURES_COLLECTION = "historical_figures"


def serialize_doc(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# Initialize database (creates it if it doesn't exist)
def init_database():
    """Initialize the database by creating a test collection if needed"""
    try:
        # Create the database by inserting and immediately deleting a test document
        # This ensures the database exists even if no collections are created yet
        test_collection = db["_init"]
        test_collection.insert_one({"init": True})
        test_collection.delete_one({"init": True})
        print(f"Database '{db.name}' initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")


# Initialize database on startup
init_database()

# Collection for historical figures
HISTORICAL_FIGURES_COLLECTION = "historical_figures"


def get_or_create_historical_figure(person_name: str) -> Dict:
    """
    Check if historical figure exists in database. If not, query Gemini and save.
    Returns the historical figure document.
    """
    collection = db[HISTORICAL_FIGURES_COLLECTION]

    # Normalize person name for lookup (case-insensitive)
    person_lower = person_name.lower().strip()

    # Check if person exists in database
    existing = hf_repo.find_by_name(person_name)

    if existing:
        # If existing record doesn't have elevenlabs summary, generate it
        if "elevenlabs" not in existing or not existing.get("elevenlabs"):
            print(f"Generating ElevenLabs summary for existing record: {person_name}")
            elevenlabs_summary = generate_elevenlabs_voice_summary(
                existing.get("answers", {})
            )
            collection.update_one(
                {"person_name_lower": person_lower},
                {"$set": {"elevenlabs": elevenlabs_summary}},
            )
            existing["elevenlabs"] = elevenlabs_summary

        return serialize_doc(existing)

    # Person not found, query Gemini
    print(f"Querying Gemini for information about: {person_name}")
    gemini_data = query_gemini_for_historical_figure(person_name)

    # Generate ElevenLabs voice summary
    answers = gemini_data.get("answers", {})
    elevenlabs_summary = generate_elevenlabs_voice_summary(answers)

    # Structure the data for storage
    document = {
        "person_name": person_name,
        "person_name_lower": person_lower,
        "questions": HISTORICAL_FIGURE_QUESTIONS,
        "answers": answers,
        "full_response": gemini_data.get("full_response", ""),
        "elevenlabs": elevenlabs_summary,
        "created_at": None,  # Will be set by MongoDB
    }

    # Insert into database
    result = hf_repo.insert_figure(document)
    document["_id"] = result.inserted_id

    print(f"Saved information about {person_name} to database")
    return serialize_doc(document)


@app.route("/")
def index():
    return jsonify(
        {
            "message": "Flask server is running",
            "database": get_db().name,
            "status": "connected",
        }
    )


@app.route("/health")
def health():
    if check_connection():
        return jsonify({"status": "healthy", "database": "connected"}), 200
    else:
        return (
            jsonify({"status": "unhealthy", "error": "Cannot connect to MongoDB"}),
            500,
        )


@app.route("/api/items", methods=["GET"])
def get_items():
    """Get all items from the collection"""
    collection_name = request.args.get("collection", "items")
    collection = db[collection_name]
    items = list(collection.find())
    return jsonify([serialize_doc(item) for item in items])


@app.route("/api/items", methods=["POST"])
def create_item():
    """Create a new item in the collection"""
    collection_name = request.args.get("collection", "items")
    collection = db[collection_name]
    data = request.get_json()
    result = collection.insert_one(data)
    return (
        jsonify(
            {"id": str(result.inserted_id), "message": "Item created successfully"}
        ),
        201,
    )


@app.route("/api/items/<item_id>", methods=["GET"])
def get_item(item_id):
    """Get a specific item by ID"""
    collection_name = request.args.get("collection", "items")
    collection = db[collection_name]
    try:
        item = collection.find_one({"_id": ObjectId(item_id)})
        if item:
            return jsonify(serialize_doc(item))
        return jsonify({"error": "Item not found"}), 404
    except Exception as e:
        return jsonify({"error": "Invalid ID format"}), 400


@app.route("/api/items/<item_id>", methods=["PUT"])
def update_item(item_id):
    """Update an item by ID"""
    collection_name = request.args.get("collection", "items")
    collection = db[collection_name]
    data = request.get_json()
    try:
        result = collection.update_one({"_id": ObjectId(item_id)}, {"$set": data})
        if result.matched_count:
            return jsonify({"message": "Item updated successfully"})
        return jsonify({"error": "Item not found"}), 404
    except Exception as e:
        return jsonify({"error": "Invalid ID format"}), 400


@app.route("/api/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item by ID"""
    collection_name = request.args.get("collection", "items")
    collection = db[collection_name]
    try:
        result = collection.delete_one({"_id": ObjectId(item_id)})
        if result.deleted_count:
            return jsonify({"message": "Item deleted successfully"})
        return jsonify({"error": "Item not found"}), 404
    except Exception as e:
        return jsonify({"error": "Invalid ID format"}), 400


# Historical Figure Endpoints
@app.route("/api/historical-figure/<person_name>", methods=["GET"])
def get_historical_figure(person_name):
    """
    Get or create historical figure profile.
    If person doesn't exist in database, queries Gemini API and saves the results.
    """
    try:
        if not GEMINI_API_KEY:
            return (
                jsonify(
                    {
                        "error": "GEMINI_API_KEY is not configured. Please set it as an environment variable."
                    }
                ),
                500,
            )

        figure_data = get_or_create_historical_figure(person_name)
        return jsonify(figure_data), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/historical-figures", methods=["GET"])
def list_historical_figures():
    """List all historical figures in the database"""
    collection = db[HISTORICAL_FIGURES_COLLECTION]
    figures = list(
        collection.find({}, {"person_name": 1, "person_name_lower": 1, "created_at": 1})
    )
    return jsonify([serialize_doc(fig) for fig in figures])


def generate_character_context(figure_data: Dict) -> str:
    """
    Generate a comprehensive character context from stored figure data
    for use in conversation simulation.
    """
    answers = figure_data.get("answers", {})

    # Key questions to include in character context
    context_sections = []

    # Basic identity
    if "What is their full name and any known aliases or nicknames?" in answers:
        context_sections.append(
            f"Name: {answers['What is their full name and any known aliases or nicknames?']}"
        )

    if "What time period did they live in (specific years and era)?" in answers:
        context_sections.append(
            f"Time Period: {answers['What time period did they live in (specific years and era)?']}"
        )

    # Personality and character
    personality_questions = [
        "What was their overall personality like?",
        "What were their key personality traits (both positive and negative)?",
        "How would you describe their temperament and demeanor?",
        "What were their core values and beliefs?",
        "What motivated them in life?",
        "How did they interact with others (social, reserved, charismatic, etc.)?",
        "What was their sense of humor like, if any?",
    ]

    personality_info = []
    for q in personality_questions:
        if q in answers and answers[q]:
            personality_info.append(answers[q])

    if personality_info:
        context_sections.append(
            f"Personality: {' '.join(personality_info[:3])}"
        )  # Limit to avoid token bloat

    # Voice and speech
    voice_questions = [
        "What did their voice sound like (tone, pitch, accent, quality)?",
        "What was their speaking style (fast, slow, measured, animated)?",
        "What was their typical vocabulary and word choice like?",
        "Did they use any distinctive phrases, catchphrases, or expressions?",
        "What was their accent or dialect?",
        "How formal or informal was their speech?",
        "Did they use any specific terminology, jargon, or specialized language?",
    ]

    voice_info = []
    for q in voice_questions:
        if q in answers and answers[q]:
            voice_info.append(answers[q])

    if voice_info:
        context_sections.append(f"Voice and Speech: {' '.join(voice_info[:3])}")

    # Background and context
    if "What was their profession, occupation, or role did they hold?" in answers:
        context_sections.append(
            f"Profession: {answers['What was their profession, occupation, or role did they hold?']}"
        )

    if "What are they most famous or known for?" in answers:
        context_sections.append(
            f"Known For: {answers['What are they most famous or known for?']}"
        )

    # Quirks and mannerisms
    if "What were their personal quirks, habits, or idiosyncrasies?" in answers:
        context_sections.append(
            f"Quirks: {answers['What were their personal quirks, habits, or idiosyncrasies?']}"
        )

    # Philosophical views
    if "What were their philosophical views on life, death, and purpose?" in answers:
        context_sections.append(
            f"Philosophy: {answers['What were their philosophical views on life, death, and purpose?']}"
        )

    return "\n".join(context_sections)


def simulate_conversation(
    person_name: str, user_message: str, conversation_history: List[Dict] = None
) -> str:
    """
    Simulate a conversation with a historical figure.
    Uses stored character data to generate in-character responses.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")

    # Get historical figure data
    figure_data = get_or_create_historical_figure(person_name)

    # Generate character context
    character_context = generate_character_context(figure_data)

    # Build conversation history string
    history_text = ""
    if conversation_history:
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_text += f"{role.capitalize()}: {content}\n"

    # Create the prompt
    prompt = f"""You are {person_name}. Respond as this historical figure would, based on the following information about them:

{character_context}

Important guidelines:
- Respond in character, using their voice, speaking style, vocabulary, and mannerisms
- Use their accent, dialect, and level of formality
- Reference their known phrases, expressions, and way of speaking
- Stay true to their personality, values, and beliefs
- If asked about something you wouldn't know (future events, modern technology), respond as they would have in their time
- Keep responses natural and conversational, not like a biography

{history_text}User: {user_message}

{person_name}:"""

    try:
        # Get model and generate response
        model_name = get_available_gemini_model()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise Exception(f"Error generating conversation response: {str(e)}")


def get_vector_db_collection():
    """Get or create ChromaDB collection for vector search"""
    try:
        import chromadb
        from chromadb.config import Settings

        chroma_client = chromadb.PersistentClient(
            path="./chroma_db", settings=Settings(anonymized_telemetry=False)
        )

        try:
            collection = chroma_client.get_collection(name="historical_figures_qa")
            return collection
        except:
            return None  # Collection doesn't exist yet
    except ImportError:
        return None


@app.route("/api/vector-search", methods=["POST"])
def vector_search():
    """
    Search the vector database for relevant Q&A pairs.

    Request body:
    {
        "query": "What was their personality like?",
        "person_name": "Leonardo da Vinci",  // Optional filter
        "n_results": 5  // Optional, default 5
    }
    """
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": 'Missing "query" in request body'}), 400

        query_text = data["query"]
        person_name = data.get("person_name")
        n_results = data.get("n_results", 5)

        collection = get_vector_db_collection()
        if not collection:
            return (
                jsonify(
                    {
                        "error": "Vector database not found. Please run build_vector_db.py first."
                    }
                ),
                404,
            )

        # Build query filter
        where = {}
        if person_name:
            where["person_name"] = person_name

        # Query (ChromaDB will use its default embeddings)
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where if where else None,
        )

        # Format results
        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for doc, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                (
                    results["distances"][0]
                    if "distances" in results
                    else [0] * len(results["documents"][0])
                ),
            ):
                formatted_results.append(
                    {
                        "person_name": metadata.get("person_name"),
                        "question": metadata.get("question"),
                        "answer": doc,
                        "relevance_score": (
                            1 - distance if "distances" in results else None
                        ),
                    }
                )

        return (
            jsonify(
                {
                    "query": query_text,
                    "results": formatted_results,
                    "count": len(formatted_results),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversation/<person_name>", methods=["POST"])
def conversation(person_name):
    """
    Simulate a conversation with a historical figure.

    Request body:
    {
        "message": "Your question or message",
        "history": [  // Optional: conversation history
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Greetings..."}
        ]
    }
    """
    try:
        if not GEMINI_API_KEY:
            return jsonify({"error": "GEMINI_API_KEY is not configured."}), 500

        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": 'Missing "message" in request body'}), 400

        user_message = data["message"]
        conversation_history = data.get("history", [])

        # Generate response
        response = simulate_conversation(
            person_name, user_message, conversation_history
        )

        # Build updated conversation history
        updated_history = conversation_history.copy() if conversation_history else []
        updated_history.append({"role": "user", "content": user_message})
        updated_history.append({"role": "assistant", "content": response})

        # Keep only last 10 messages (5 exchanges) to avoid token limits
        if len(updated_history) > 10:
            updated_history = updated_history[-10:]

        return (
            jsonify(
                {
                    "person": person_name,
                    "user_message": user_message,
                    "response": response,
                    "conversation_history": updated_history,  # Return full conversation so far
                }
            ),
            200,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
