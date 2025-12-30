import os
import re
from typing import Dict, List

import google.generativeai as genai
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from mongo import check_connection, get_db

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Google Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not set. Gemini features will not work.")

# Historical figure questions - comprehensive list to paint a complete picture
HISTORICAL_FIGURE_QUESTIONS = [
    # Basic Information
    "What is their full name and any known aliases or nicknames?",
    "What is their date of birth and date of death (or current age if alive)?",
    "What time period did they live in (specific years and era)?",
    "Where were they born (city, country, region)?",
    "Where did they primarily live and work throughout their life?",
    "What was their nationality and cultural background?",
    # What They're Known For
    "What are they most famous or known for?",
    "What are their primary achievements or accomplishments?",
    "What profession, occupation, or role did they hold?",
    "What significant contributions did they make to their field or society?",
    "What works, inventions, or creations are they associated with?",
    "What historical events were they involved in or connected to?",
    # Physical Characteristics & Voice
    "What did they look like physically (height, build, distinctive features)?",
    "What was their typical appearance or style of dress?",
    "What did their voice sound like (tone, pitch, accent, quality)?",
    "Did they have any distinctive vocal characteristics or speech patterns?",
    "What was their speaking style (fast, slow, measured, animated)?",
    "Did they have any physical disabilities, conditions, or notable health issues?",
    # Personality & Character
    "What was their overall personality like?",
    "What were their key personality traits (both positive and negative)?",
    "How would you describe their temperament and demeanor?",
    "What were their core values and beliefs?",
    "What motivated them in life?",
    "How did they interact with others (social, reserved, charismatic, etc.)?",
    "What was their sense of humor like, if any?",
    # Quirks & Habits
    "What were their personal quirks, habits, or idiosyncrasies?",
    "Did they have any unusual routines, rituals, or daily practices?",
    "What were their hobbies, interests, or pastimes?",
    "Did they have any notable habits or mannerisms?",
    "What were their preferences in food, drink, or lifestyle?",
    "Did they have any superstitions or unusual beliefs?",
    # Scandals & Controversies
    "Were they involved in any scandals or controversies?",
    "What were the major controversies or criticisms surrounding them?",
    "Did they have any enemies or notable conflicts?",
    "What were the darker aspects or negative aspects of their character?",
    "Were there any legal issues, trials, or legal problems in their life?",
    # Vernacular & Speech Patterns
    "What was their typical vocabulary and word choice like?",
    "Did they use any distinctive phrases, catchphrases, or expressions?",
    "What was their accent or dialect?",
    "How formal or informal was their speech?",
    "Did they use any specific terminology, jargon, or specialized language?",
    "What was their writing style like (if they wrote)?",
    "Did they have any speech impediments or unique speech characteristics?",
    # Relationships & Social Life
    "Who were the important people in their life (family, friends, colleagues)?",
    "What was their family background and upbringing like?",
    "Did they have romantic relationships, marriages, or significant partnerships?",
    "Who were their mentors, influences, or people they admired?",
    "Who were their contemporaries or people they interacted with?",
    "What was their relationship with the public or their audience?",
    # Education & Background
    "What was their educational background?",
    "What was their socioeconomic background?",
    "What early life experiences shaped them?",
    "What challenges or obstacles did they face in their life?",
    # Legacy & Impact
    "What is their historical legacy and impact?",
    "How are they remembered today?",
    "What myths, misconceptions, or common misunderstandings exist about them?",
    # Communication & Expression
    "How did they prefer to communicate (written letters, speeches, conversations, etc.)?",
    "What were their most famous or memorable quotes or sayings?",
    "How did they express emotions (stoic, emotional, reserved, demonstrative)?",
    "Was there a difference between their public persona and private self?",
    "How did they handle criticism or negative feedback?",
    "What was their reaction to failure or setbacks?",
    "How did they celebrate success or achievements?",
    # Decision-Making & Work Style
    "How did they make important decisions (impulsive, methodical, consultative, intuitive)?",
    "What were their work habits (morning person, night owl, workaholic, balanced)?",
    "How did they approach problem-solving?",
    "What was their relationship with authority (rebel, conformist, leader, follower)?",
    "How adaptable were they to change and new circumstances?",
    # Psychological & Emotional Depth
    "What were their greatest fears or anxieties?",
    "What kept them awake at night or worried them most?",
    "What were their deepest regrets, if any?",
    "What brought them the most joy or satisfaction?",
    "How did they cope with stress or pressure?",
    "What were their coping mechanisms during difficult times?",
    # Philosophical & Spiritual
    "What were their philosophical views on life, death, and purpose?",
    "What were their spiritual or religious beliefs and practices?",
    "How did they view their place in the world or universe?",
    "What did they believe about human nature?",
    # Cultural & Intellectual
    "What was their relationship with the arts (music, literature, visual arts)?",
    "What books, authors, or intellectual works influenced them?",
    "How did they engage with the culture and society of their time?",
    "What was their relationship with technology or innovation of their era?",
    "Did they travel extensively? Where and how did travel influence them?",
    # Health & Aging
    "How did their health change over time?",
    "How did aging affect their work, personality, or outlook?",
    "What were their final years like?",
    "What were their last words or final thoughts (if documented)?",
    # Influence & Impact on Others
    "How did they influence or inspire people around them?",
    "What was their leadership style (if applicable)?",
    "How did they mentor or teach others?",
    "What was their impact on future generations?",
    # Context & Environment
    "What was the political climate during their lifetime?",
    "What major social or cultural movements were happening during their era?",
    "How did historical events of their time shape them?",
    "What was daily life like during their time period?",
]

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


def get_available_gemini_model():
    """
    Get an available Gemini model by listing available models.
    Returns the model name that works, or raises an exception.
    """
    try:
        # List all available models
        available_models = []
        for model in genai.list_models():
            if "generateContent" in model.supported_generation_methods:
                # Extract just the model name (remove 'models/' prefix if present)
                model_name = model.name.replace("models/", "")
                available_models.append(model_name)

        print(f"Available Gemini models: {available_models}")

        if not available_models:
            raise Exception("No models with generateContent support found.")

        # Prefer flash, then pro, then any available
        preferred_order = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        for preferred in preferred_order:
            if preferred in available_models:
                print(f"Using model: {preferred}")
                return preferred

        # Use the first available model
        selected = available_models[0]
        print(f"Using first available model: {selected}")
        return selected

    except Exception as e:
        raise Exception(
            f"Could not determine available models: {str(e)}. Please check your API key."
        )


def query_gemini_for_historical_figure(person_name: str) -> Dict:
    """
    Query Google Gemini API with all questions about a historical figure.
    Returns a dictionary with all question-answer pairs.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")

    # Create a structured prompt that asks for JSON-like format
    prompt = f"""You are an expert historian and biographer. I need comprehensive information about the historical figure: {person_name}

Please answer ALL of the following questions about {person_name} in detail. Be specific and accurate based on historical records and facts.

Format your response as follows:
For each question, provide the answer on a new line starting with "Q[number]: " followed by the answer.

Example format:
Q1: [Answer to question 1]
Q2: [Answer to question 2]
...

Questions:
"""

    # Add all questions to the prompt with clear numbering
    for i, question in enumerate(HISTORICAL_FIGURE_QUESTIONS, 1):
        prompt += f"Q{i}: {question}\n"

    prompt += "\nPlease provide detailed, accurate answers to each question. If information is not available or uncertain, please note that. Be thorough and comprehensive."

    try:
        # Get an available model
        model_name = get_available_gemini_model()
        model = genai.GenerativeModel(model_name)

        # Generate response
        response = model.generate_content(prompt)
        full_response = response.text

        # Parse the response to extract individual answers
        result = {
            "person_name": person_name,
            "full_response": full_response,
            "answers": {},
        }

        # Parse Q1:, Q2:, etc. format
        # Gemini often repeats the question, so we need to find the answer part
        # Use regex to find all Q[number]: patterns and their content
        q_pattern = re.compile(r"Q(\d+):\s*(.*?)(?=\nQ\d+:|$)", re.DOTALL)
        matches = q_pattern.findall(full_response)

        # Process matches - Gemini often has two Q1: entries: one with question, one with answer
        question_answers = {}
        for q_num_str, content in matches:
            q_num = int(q_num_str)
            if 1 <= q_num <= len(HISTORICAL_FIGURE_QUESTIONS):
                content = content.strip()
                if not content:  # Skip empty content
                    continue

                question_text = HISTORICAL_FIGURE_QUESTIONS[q_num - 1]

                # Check if this content is the question itself (Gemini repeats it)
                # Criteria: content is very similar to the question text
                content_lower = content.lower()
                question_lower = question_text.lower()

                # If content starts with or closely matches the question, it's likely the question repetition
                is_question_repetition = content_lower.startswith(
                    question_lower[:50]
                ) or (  # Starts with question
                    question_lower in content_lower
                    and len(content) < len(question_text) + 100
                )  # Contains question but short

                if is_question_repetition:
                    # This is the question being repeated, skip it
                    continue

                # If we already have an answer for this question, keep the longer one (longer = likely the answer)
                if q_num in question_answers:
                    if len(content) > len(question_answers[q_num]):
                        question_answers[q_num] = content
                else:
                    question_answers[q_num] = content

        # Convert to final format
        for q_num, answer in question_answers.items():
            question_text = HISTORICAL_FIGURE_QUESTIONS[q_num - 1]
            # Clean up the answer (remove any trailing question text if accidentally included)
            clean_answer = answer.strip()
            # Remove the question text if it appears at the start of the answer
            if clean_answer.lower().startswith(question_text.lower()[:50]):
                clean_answer = clean_answer[len(question_text) :].strip()
                if clean_answer.startswith(":"):
                    clean_answer = clean_answer[1:].strip()
            result["answers"][question_text] = clean_answer

        # If the regex approach didn't work well, try line-by-line parsing
        if (
            len(result["answers"]) < len(HISTORICAL_FIGURE_QUESTIONS) * 0.5
        ):  # Less than 50% parsed
            result["answers"] = {}
            lines = full_response.split("\n")
            current_answer = None
            current_question_num = None
            seen_questions = set()  # Track which question numbers we've seen

            for line in lines:
                line = line.strip()
                if not line:
                    if (
                        current_answer
                    ):  # Empty line might separate Q&A, but continue current answer
                        current_answer += "\n"
                    continue

                # Check if line starts with Q[number]:
                if re.match(r"^Q\d+:", line):
                    try:
                        # Extract question number
                        q_part = line.split(":", 1)[0]
                        q_num = int(q_part[1:])  # Remove 'Q' and get number

                        if 1 <= q_num <= len(HISTORICAL_FIGURE_QUESTIONS):
                            content_after_colon = (
                                line.split(":", 1)[1].strip() if ":" in line else ""
                            )
                            question_text = HISTORICAL_FIGURE_QUESTIONS[q_num - 1]

                            # Check if this line contains the question text (Gemini repeats it)
                            if (
                                question_text.lower() in content_after_colon.lower()
                                and len(content_after_colon) < len(question_text) + 100
                            ):
                                # This is the question being repeated, skip to next line
                                continue

                            # Save previous answer if exists
                            if (
                                current_question_num is not None
                                and current_question_num not in seen_questions
                            ):
                                prev_question = HISTORICAL_FIGURE_QUESTIONS[
                                    current_question_num - 1
                                ]
                                if (
                                    prev_question not in result["answers"]
                                    and current_answer
                                ):
                                    result["answers"][
                                        prev_question
                                    ] = current_answer.strip()
                                    seen_questions.add(current_question_num)

                            # Start new answer
                            current_question_num = q_num
                            current_answer = content_after_colon
                    except (ValueError, IndexError):
                        # Not a valid Q format, append to current answer
                        if current_answer is not None:
                            current_answer += " " + line
                else:
                    # Continue current answer
                    if current_answer is not None:
                        current_answer += " " + line

            # Save last answer
            if (
                current_question_num is not None
                and current_question_num not in seen_questions
            ):
                question_text = HISTORICAL_FIGURE_QUESTIONS[current_question_num - 1]
                if question_text not in result["answers"] and current_answer:
                    result["answers"][question_text] = current_answer.strip()

        # Ensure all questions have entries (even if empty)
        for question in HISTORICAL_FIGURE_QUESTIONS:
            if question not in result["answers"]:
                result["answers"][question] = ""

        return result

    except Exception as e:
        raise Exception(f"Error querying Gemini API: {str(e)}")


def generate_elevenlabs_voice_summary(answers: Dict) -> str:
    """
    Generate a concise voice summary (1000 chars or less) for ElevenLabs.
    Focuses on voice characteristics: pitch, accent, vernacular, mannerisms, key phrases.
    Excludes accomplishments and personality traits unrelated to voice.
    """
    # Voice-related question keys to extract
    voice_questions = [
        "What did their voice sound like (tone, pitch, accent, quality)?",
        "Did they have any distinctive vocal characteristics or speech patterns?",
        "What was their speaking style (fast, slow, measured, animated)?",
        "What was their typical vocabulary and word choice like?",
        "Did they use any distinctive phrases, catchphrases, or expressions?",
        "What was their accent or dialect?",
        "How formal or informal was their speech?",
        "Did they use any specific terminology, jargon, or specialized language?",
        "Did they have any speech impediments or unique speech characteristics?",
        "What were their most famous or memorable quotes or sayings?",
        "Did they have any notable habits or mannerisms?",  # May include speech mannerisms
    ]

    # Extract voice-related information
    voice_info = []
    for question in voice_questions:
        if question in answers and answers[question]:
            answer = answers[question].strip()
            if answer and answer.lower() not in [
                "n/a",
                "not available",
                "unknown",
                "uncertain",
            ]:
                voice_info.append(answer)

    # Combine into a summary
    if not voice_info:
        return "Voice characteristics not documented in historical records."

    # Create a concise summary
    combined = " ".join(voice_info)

    # If too long, truncate intelligently
    if len(combined) > 1000:
        # Try to cut at sentence boundaries
        truncated = combined[:1000]
        last_period = truncated.rfind(".")
        last_newline = truncated.rfind("\n")
        cut_point = max(last_period, last_newline)

        if cut_point > 800:  # Only use if we have enough content
            combined = truncated[: cut_point + 1]
        else:
            # Just truncate at word boundary
            truncated = combined[:997]
            last_space = truncated.rfind(" ")
            combined = truncated[:last_space] + "..."

    return combined.strip()


def get_or_create_historical_figure(person_name: str) -> Dict:
    """
    Check if historical figure exists in database. If not, query Gemini and save.
    Returns the historical figure document.
    """
    collection = db[HISTORICAL_FIGURES_COLLECTION]

    # Normalize person name for lookup (case-insensitive)
    person_lower = person_name.lower().strip()

    # Check if person exists in database
    existing = collection.find_one({"person_name_lower": person_lower})

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
    result = collection.insert_one(document)
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
