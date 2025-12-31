from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
import re
import json
import time
import requests
import google.generativeai as genai
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS for React/Next.js frontend
# In production, allow specific origins; in development, allow all
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, origins=cors_origins if cors_origins != ['*'] else None)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'talkwith')

# Google Gemini API configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not set. Gemini features will not work.")

# ElevenLabs API configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

# Constants
MAX_AGENTS = 30
VOICE_DESCRIPTION_MAX_LENGTH = 1000
ELEVENLABS_SUMMARY_MAX_LENGTH = 1000
SAMPLE_TEXT_MIN_LENGTH = 100
GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_DELAY = 2  # seconds
GEMINI_TIMEOUT = 300  # 5 minutes for large responses

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
    "What was daily life like during their time period?"
]

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Helper function to convert ObjectId to string
def serialize_doc(doc):
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

# Helper function to get ElevenLabs headers
def get_elevenlabs_headers() -> dict:
    """Get standard ElevenLabs API headers."""
    return {"xi-api-key": ELEVENLABS_API_KEY}

# Helper function to format figure data for frontend
def format_figure_for_list(fig: dict) -> dict:
    """Format a MongoDB figure document for frontend list display."""
    return {
        'id': str(fig.get('_id')),
        'name': fig.get('person_name'),
        'has_agent': bool(fig.get('elevenlabs_agent_id')),
        'agent_id': fig.get('elevenlabs_agent_id'),
        'voice_id': fig.get('elevenlabs_voice_id')
    }

# Initialize database (creates it if it doesn't exist)
def init_database():
    """Initialize the database by creating a test collection if needed"""
    try:
        test_collection = db['_init']
        test_collection.insert_one({'init': True})
        test_collection.delete_one({'init': True})
        print(f"Database '{DATABASE_NAME}' initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")

# Initialize database on startup
init_database()

# Collection for historical figures
HISTORICAL_FIGURES_COLLECTION = 'historical_figures'

# Cache for Gemini model selection
_GEMINI_MODEL_CACHE = None

def get_available_gemini_model():
    """Get an available Gemini model by listing available models. Cached to avoid repeated API calls."""
    global _GEMINI_MODEL_CACHE
    
    if _GEMINI_MODEL_CACHE:
        return _GEMINI_MODEL_CACHE
    
    try:
        available_models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace('models/', '')
                available_models.append(model_name)
        
        print(f"Available Gemini models: {available_models}")
        
        if not available_models:
            raise Exception("No models with generateContent support found.")
        
        # Prefer flash, then pro, then any available
        preferred_order = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        for preferred in preferred_order:
            if preferred in available_models:
                print(f"Using model: {preferred}")
                _GEMINI_MODEL_CACHE = preferred
                return preferred
        
        selected = available_models[0]
        print(f"Using first available model: {selected}")
        _GEMINI_MODEL_CACHE = selected
        return selected
        
    except Exception as e:
        raise Exception(f"Could not determine available models: {str(e)}. Please check your API key.")

def query_gemini_for_historical_figure(person_name: str) -> Dict:
    """Query Google Gemini API with all questions about a historical figure.
    Includes retry logic with exponential backoff for timeout handling."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")
    
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
    
    for i, question in enumerate(HISTORICAL_FIGURE_QUESTIONS, 1):
        prompt += f"Q{i}: {question}\n"
    
    prompt += "\nPlease provide detailed, accurate answers to each question. If information is not available or uncertain, please note that. Be thorough and comprehensive."
    
    model_name = get_available_gemini_model()
    model = genai.GenerativeModel(model_name)
    
    # Configure generation settings for longer responses
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,  # Maximum tokens for response
    }
    
    # Retry logic with exponential backoff
    last_exception = None
    full_response = None
    for attempt in range(GEMINI_MAX_RETRIES):
        try:
            print(f"Querying Gemini for {person_name} (attempt {attempt + 1}/{GEMINI_MAX_RETRIES})...")
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            full_response = response.text
            break  # Success, exit retry loop
            
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Check if it's a timeout or rate limit error
            is_timeout = any(keyword in error_msg for keyword in ['timeout', 'deadline', 'timed out', '504', '503'])
            is_rate_limit = any(keyword in error_msg for keyword in ['rate limit', '429', 'quota'])
            
            if attempt < GEMINI_MAX_RETRIES - 1:
                # Calculate exponential backoff delay
                delay = GEMINI_RETRY_DELAY * (2 ** attempt)
                print(f"⚠️  Gemini API error (attempt {attempt + 1}): {str(e)[:200]}")
                print(f"   Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                # Last attempt failed
                if is_timeout:
                    raise Exception(f"Gemini API request timed out after {GEMINI_MAX_RETRIES} attempts. The prompt may be too long or the response too large. Try again later.")
                elif is_rate_limit:
                    raise Exception(f"Gemini API rate limit exceeded after {GEMINI_MAX_RETRIES} attempts. Please wait before trying again.")
                else:
                    raise Exception(f"Error querying Gemini API after {GEMINI_MAX_RETRIES} attempts: {str(e)}")
    
    if not full_response:
        raise Exception(f"Failed to get response from Gemini API: {last_exception}")
    
    try:
        
        result = {
            'person_name': person_name,
            'full_response': full_response,
            'answers': {}
        }
        
        # Parse Q1:, Q2:, etc. format
        q_pattern = re.compile(r'Q(\d+):\s*(.*?)(?=\nQ\d+:|$)', re.DOTALL)
        matches = q_pattern.findall(full_response)
        
        question_answers = {}
        for q_num_str, content in matches:
            q_num = int(q_num_str)
            if 1 <= q_num <= len(HISTORICAL_FIGURE_QUESTIONS):
                content = content.strip()
                if not content:
                    continue
                    
                question_text = HISTORICAL_FIGURE_QUESTIONS[q_num - 1]
                content_lower = content.lower()
                question_lower = question_text.lower()
                
                is_question_repetition = (
                    content_lower.startswith(question_lower[:50]) or
                    (question_lower in content_lower and len(content) < len(question_text) + 100)
                )
                
                if is_question_repetition:
                    continue
                
                if q_num in question_answers:
                    if len(content) > len(question_answers[q_num]):
                        question_answers[q_num] = content
                else:
                    question_answers[q_num] = content
        
        for q_num, answer in question_answers.items():
            question_text = HISTORICAL_FIGURE_QUESTIONS[q_num - 1]
            clean_answer = answer.strip()
            if clean_answer.lower().startswith(question_text.lower()[:50]):
                clean_answer = clean_answer[len(question_text):].strip()
                if clean_answer.startswith(':'):
                    clean_answer = clean_answer[1:].strip()
            result['answers'][question_text] = clean_answer
        
        # Fallback parsing if regex didn't work well (less than 50% parsed)
        MIN_ANSWERS_THRESHOLD = len(HISTORICAL_FIGURE_QUESTIONS) * 0.5
        if len(result['answers']) < MIN_ANSWERS_THRESHOLD:
            result['answers'] = {}
            lines = full_response.split('\n')
            current_answer = None
            current_question_num = None
            seen_questions = set()
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_answer:
                        current_answer += "\n"
                    continue
                
                if re.match(r'^Q\d+:', line):
                    try:
                        q_part = line.split(':', 1)[0]
                        q_num = int(q_part[1:])
                        
                        if 1 <= q_num <= len(HISTORICAL_FIGURE_QUESTIONS):
                            content_after_colon = line.split(':', 1)[1].strip() if ':' in line else ""
                            question_text = HISTORICAL_FIGURE_QUESTIONS[q_num - 1]
                            
                            if question_text.lower() in content_after_colon.lower() and len(content_after_colon) < len(question_text) + 100:
                                continue
                            
                            if current_question_num is not None and current_question_num not in seen_questions:
                                prev_question = HISTORICAL_FIGURE_QUESTIONS[current_question_num - 1]
                                if prev_question not in result['answers'] and current_answer:
                                    result['answers'][prev_question] = current_answer.strip()
                                    seen_questions.add(current_question_num)
                            
                            current_question_num = q_num
                            current_answer = content_after_colon
                    except (ValueError, IndexError):
                        if current_answer is not None:
                            current_answer += " " + line
                else:
                    if current_answer is not None:
                        current_answer += " " + line
            
            if current_question_num is not None and current_question_num not in seen_questions:
                question_text = HISTORICAL_FIGURE_QUESTIONS[current_question_num - 1]
                if question_text not in result['answers'] and current_answer:
                    result['answers'][question_text] = current_answer.strip()
        
        for question in HISTORICAL_FIGURE_QUESTIONS:
            if question not in result['answers']:
                result['answers'][question] = ""
        
        return result
        
    except Exception as e:
        # Re-raise if it's already been formatted by retry logic
        if "after" in str(e) and "attempts" in str(e):
            raise
        raise Exception(f"Error querying Gemini API: {str(e)}")

def generate_elevenlabs_voice_summary(person_name: str, answers: Dict, full_response: str) -> str:
    """Query Gemini to generate a concise voice and personality summary (1000 chars or less) for ElevenLabs.
    Includes retry logic for reliability."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")
    
    prompt = f"""Based on the following comprehensive information about {person_name}, create a concise summary (1000 characters or less) describing:

1. How they sounded and talked (voice characteristics, tone, pitch, accent, speaking style, vocabulary, phrases, mannerisms)
2. Their personality (key traits, how they expressed themselves, their demeanor)

CRITICAL: Do NOT include the person's first name, last name, or full name anywhere in your response. Only describe voice and personality characteristics.

Focus on voice and personality characteristics that would be useful for voice synthesis and character portrayal. Exclude accomplishments, achievements, and historical events unless directly relevant to how they spoke or their personality.

Here is the information gathered about {person_name}:

{full_response[:5000]}  # Limit context to avoid token limits

Please provide a concise summary in 1000 characters or less that captures their voice and personality. Remember: do not include any names."""
    
    model_name = get_available_gemini_model()
    model = genai.GenerativeModel(model_name)
    
    # Retry logic for voice summary generation
    last_exception = None
    summary = None
    for attempt in range(GEMINI_MAX_RETRIES):
        try:
            response = model.generate_content(prompt)
            summary = response.text.strip()
            break  # Success, exit retry loop
            
        except Exception as e:
            last_exception = e
            if attempt < GEMINI_MAX_RETRIES - 1:
                delay = GEMINI_RETRY_DELAY * (2 ** attempt)
                print(f"⚠️  Voice summary generation error (attempt {attempt + 1}): {str(e)[:200]}")
                print(f"   Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise Exception(f"Error generating ElevenLabs summary after {GEMINI_MAX_RETRIES} attempts: {str(e)}")
    
    if not summary:
        raise Exception(f"Failed to generate voice summary: {last_exception}")
    
    try:
        
        if len(summary) > ELEVENLABS_SUMMARY_MAX_LENGTH:
            summary = summary[:ELEVENLABS_SUMMARY_MAX_LENGTH - 3] + "..."
        
        return summary
        
    except Exception as e:
        raise Exception(f"Error generating ElevenLabs summary: {str(e)}")

def get_or_create_historical_figure(person_name: str) -> Dict:
    """Check if historical figure exists in database. If not, query Gemini and save."""
    collection = db[HISTORICAL_FIGURES_COLLECTION]
    
    person_lower = person_name.lower().strip()
    existing = collection.find_one({'person_name_lower': person_lower})
    
    if existing:
        if 'elevenlabs' not in existing or not existing.get('elevenlabs'):
            print(f"Generating ElevenLabs summary for existing record: {person_name}")
            elevenlabs_summary = generate_elevenlabs_voice_summary(
                person_name,
                existing.get('answers', {}),
                existing.get('full_response', '')
            )
            collection.update_one(
                {'person_name_lower': person_lower},
                {'$set': {'elevenlabs': elevenlabs_summary}}
            )
            existing['elevenlabs'] = elevenlabs_summary
        
        return serialize_doc(existing)
    
    print(f"Querying Gemini for information about: {person_name}")
    gemini_data = query_gemini_for_historical_figure(person_name)
    
    answers = gemini_data.get('answers', {})
    full_response = gemini_data.get('full_response', '')
    print(f"Generating ElevenLabs voice and personality summary...")
    elevenlabs_summary = generate_elevenlabs_voice_summary(person_name, answers, full_response)
    
    document = {
        'person_name': person_name,
        'person_name_lower': person_lower,
        'questions': HISTORICAL_FIGURE_QUESTIONS,
        'answers': answers,
        'full_response': full_response,
        'elevenlabs': elevenlabs_summary,
        'created_at': None
    }
    
    result = collection.insert_one(document)
    document['_id'] = result.inserted_id
    
    print(f"Saved information about {person_name} to database")
    return serialize_doc(document)

@app.route('/')
def index():
    return jsonify({
        'message': 'Flask server is running',
        'database': DATABASE_NAME,
        'status': 'connected'
    })

@app.route('/health')
def health():
    try:
        client.admin.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/historical-figure/<person_name>', methods=['GET'])
def get_historical_figure(person_name):
    """Get or create historical figure profile. Queries Gemini if not in database."""
    try:
        if not GEMINI_API_KEY:
            return jsonify({
                'error': 'GEMINI_API_KEY is not configured. Please set it as an environment variable.'
            }), 500
        
        figure_data = get_or_create_historical_figure(person_name)
        return jsonify(figure_data), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical-figures', methods=['GET'])
def list_historical_figures():
    """
    List all historical figures in the database.
    Returns summary information suitable for frontend display.
    """
    collection = db[HISTORICAL_FIGURES_COLLECTION]
    
    # Get all figures with relevant fields for listing (projection for efficiency)
    figures = list(collection.find({}, {
        'person_name': 1,
        'elevenlabs_agent_id': 1,
        'elevenlabs_voice_id': 1,
        '_id': 1
    }))
    
    # Format for frontend
    result = [format_figure_for_list(fig) for fig in figures]
    
    return jsonify({
        'figures': result,
        'count': len(result)
    }), 200

@app.route('/api/historical-figures/search', methods=['GET'])
def search_historical_figures():
    """
    Search for historical figures by name.
    Query parameter: 'q' - search query
    """
    search_query = request.args.get('q', '').strip()
    
    if not search_query:
        return jsonify({
            'error': 'Missing search query parameter "q"'
        }), 400
    
    collection = db[HISTORICAL_FIGURES_COLLECTION]
    
    # Case-insensitive search (optimized: use index on person_name_lower)
    search_lower = search_query.lower()
    figures = list(collection.find({
        'person_name_lower': {'$regex': search_lower, '$options': 'i'}
    }, {
        'person_name': 1,
        'elevenlabs_agent_id': 1,
        'elevenlabs_voice_id': 1,
        '_id': 1
    }))
    
    result = [format_figure_for_list(fig) for fig in figures]
    
    return jsonify({
        'query': search_query,
        'figures': result,
        'count': len(result)
    }), 200

@app.route('/api/historical-figure/<person_name>/create-with-agent', methods=['POST'])
def create_figure_with_agent(person_name):
    """
    Create or get historical figure profile AND create ElevenLabs agent in one call.
    Perfect for frontend: user searches, creates figure, gets agent ready to use.
    
    Returns:
    - Complete figure data
    - voice_id and agent_id if agent was created
    - Status of agent creation
    """
    try:
        if not GEMINI_API_KEY:
            return jsonify({
                'error': 'GEMINI_API_KEY is not configured.'
            }), 500
        
        # Step 1: Get or create historical figure
        figure_data = get_or_create_historical_figure(person_name)
        
        # Step 2: Check if agent already exists
        agent_id = figure_data.get('elevenlabs_agent_id')
        voice_id = figure_data.get('elevenlabs_voice_id')
        
        agent_status = 'existing' if agent_id else 'none'
        
        # Step 3: Create agent if it doesn't exist and ElevenLabs is configured
        if not agent_id and ELEVENLABS_API_KEY:
            try:
                agent_result = create_elevenlabs_agent_for_figure(person_name)
                agent_id = agent_result.get('agent_id')
                voice_id = agent_result.get('voice_id')
                agent_status = 'created'
                
                # Refresh figure data to get updated IDs
                figure_data = get_or_create_historical_figure(person_name)
            except Exception as e:
                agent_status = f'creation_failed: {str(e)}'
                print(f"Agent creation failed: {e}")
        
        return jsonify({
            'figure': figure_data,
            'agent': {
                'agent_id': agent_id,
                'voice_id': voice_id,
                'status': agent_status,
                'ready': bool(agent_id)
            }
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def select_best_voice_from_description(voices: list, voice_description: str) -> Optional[str]:
    """
    Select the best matching voice from available voices based on description.
    Uses Gemini AI to intelligently match the voice description to available voices.
    """
    if not voices:
        return None
    
    if not GEMINI_API_KEY:
        # Fallback to keyword matching if Gemini is not available
        return select_voice_by_keywords(voices, voice_description)
    
    try:
        # Prepare voice list for Gemini
        voice_list = []
        for voice in voices:
            voice_list.append({
                'voice_id': voice.get('voice_id'),
                'name': voice.get('name', ''),
                'description': voice.get('description', '')
            })
        
        # Use Gemini to select the best matching voice
        prompt = f"""You are helping to select the best ElevenLabs voice for a historical figure.

Voice Description:
{voice_description}

Available Voices:
"""
        for i, voice in enumerate(voice_list[:20], 1):  # Limit to first 20 voices
            prompt += f"{i}. Name: {voice['name']}, Description: {voice.get('description', 'N/A')}, ID: {voice['voice_id']}\n"
        
        prompt += """
Based on the voice description, select the BEST matching voice from the list above.
Consider: gender, age, accent, tone, pitch, and speaking style.

Respond with ONLY the voice number (1, 2, 3, etc.) that best matches the description.
If no voice is a good match, respond with "0".
"""
        
        model_name = get_available_gemini_model()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Parse the response
        try:
            voice_number = int(result.split()[0])
            if 1 <= voice_number <= len(voice_list):
                selected_voice = voice_list[voice_number - 1]
                voice_id = selected_voice['voice_id']
                print(f"✅ Gemini selected voice: {selected_voice['name']} ({voice_id})")
                return voice_id
        except (ValueError, IndexError):
            pass
        
        print(f"⚠️  Gemini response unclear: {result}, falling back to keyword matching")
        return select_voice_by_keywords(voices, voice_description)
        
    except Exception as e:
        print(f"⚠️  Error using Gemini for voice selection: {e}")
        return select_voice_by_keywords(voices, voice_description)

def sanitize_voice_description(description: str) -> str:
    """
    Sanitize voice description to focus on technical voice characteristics only.
    Removes personality traits, historical context, names, and potentially problematic content
    that might trigger ElevenLabs safety filters.
    """
    # Remove any person names - split into words and filter
    words = description.split()
    filtered_words = []
    for word in words:
        # Skip words that are likely names (capitalized, longer than 3 chars)
        word_clean = word.strip('.,;:!?()[]{}"\'').lower()
        # Keep common words and voice-related terms
        if len(word_clean) > 2 and word[0].isupper() and word_clean not in ['the', 'and', 'was', 'were', 'his', 'her', 'their', 'voice', 'speaking', 'tone', 'accent', 'they', 'their']:
            # This might be a name, skip it
            continue
        filtered_words.append(word)
    
    # Rejoin and continue with keyword extraction
    description = ' '.join(filtered_words)
    description_lower = description.lower()
    
    # Technical voice characteristics keywords to extract
    voice_keywords = [
        'baritone', 'tenor', 'bass', 'soprano', 'alto',
        'deep', 'high', 'low', 'pitch', 'tone', 'timbre',
        'smooth', 'rough', 'gritty', 'clear', 'muffled',
        'resonant', 'nasal', 'breathy', 'powerful', 'soft', 'quiet', 'loud',
        'vibrato', 'tremolo', 'staccato', 'legato',
        'slow', 'fast', 'quick', 'measured', 'deliberate',
        'accent', 'dialect', 'pronunciation', 'enunciation',
        'southern', 'northern', 'british', 'american', 'english',
        'drawl', 'twang', 'lilt', 'cadence', 'rhythm',
        'monotone', 'expressive', 'animated', 'flat',
        'warm', 'cold', 'harsh', 'gentle', 'mellow',
        'young', 'mature', 'aged', 'elderly', 'weak', 'strong',
        'three-octave', 'range', 'versatile', 'distinctive'
    ]
    
    # Extract sentences that contain voice-related keywords
    sentences = description.split('.')
    relevant_sentences = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in voice_keywords):
            cleaned = sentence.strip()
            if cleaned:
                relevant_sentences.append(cleaned)
    
    # If we found relevant sentences, use them (limit to 2-3 sentences)
    if relevant_sentences:
        sanitized = '. '.join(relevant_sentences[:3])
    else:
        # Fallback: extract keywords and create a simple description
        found_keywords = [kw for kw in voice_keywords if kw in description_lower]
        if found_keywords:
            sanitized = f"A voice with {', '.join(found_keywords[:5])} characteristics."
        else:
            sanitized = "A clear, natural speaking voice with good enunciation."
    
    # Final pass: remove any remaining capitalized words that might be names (but keep sentence starts)
    # Remove standalone capitalized words (likely names) that appear mid-sentence
    sanitized = re.sub(r'\s+[A-Z][a-z]{2,}\s+(?=[a-z])', ' ', sanitized)
    # Clean up multiple spaces
    sanitized = ' '.join(sanitized.split())
    
    # Ensure it's not too long
    return sanitized[:500]

def select_voice_by_keywords(voices: list, voice_description: str) -> Optional[str]:
    """
    Fallback: Select voice using keyword matching.
    """
    description_lower = voice_description.lower()
    keywords_to_match = []
    
    # Gender indicators
    if any(word in description_lower for word in ['male', 'man', 'he', 'his', 'masculine']):
        keywords_to_match.extend(['male', 'man', 'masculine'])
    elif any(word in description_lower for word in ['female', 'woman', 'she', 'her', 'feminine']):
        keywords_to_match.extend(['female', 'woman', 'feminine'])
    
    # Age indicators
    if any(word in description_lower for word in ['young', 'youth', 'teen', 'child']):
        keywords_to_match.extend(['young', 'youth'])
    elif any(word in description_lower for word in ['old', 'elderly', 'aged', 'senior']):
        keywords_to_match.extend(['old', 'elderly', 'mature'])
    
    # Accent/region indicators
    if 'british' in description_lower or 'england' in description_lower:
        keywords_to_match.extend(['british', 'english', 'uk'])
    elif 'american' in description_lower or 'us' in description_lower:
        keywords_to_match.extend(['american', 'us'])
    elif 'french' in description_lower:
        keywords_to_match.extend(['french'])
    elif 'spanish' in description_lower or 'latin' in description_lower:
        keywords_to_match.extend(['spanish', 'latin'])
    
    # Voice characteristics
    if 'deep' in description_lower or 'low' in description_lower or 'bass' in description_lower:
        keywords_to_match.extend(['deep', 'low', 'bass'])
    elif 'high' in description_lower or 'soprano' in description_lower or 'squeaky' in description_lower:
        keywords_to_match.extend(['high', 'soprano'])
    elif 'soft' in description_lower or 'quiet' in description_lower or 'gentle' in description_lower:
        keywords_to_match.extend(['soft', 'gentle', 'calm'])
    elif 'loud' in description_lower or 'powerful' in description_lower or 'strong' in description_lower:
        keywords_to_match.extend(['powerful', 'strong', 'bold'])
    
    # Score each voice based on keyword matches
    scored_voices = []
    for voice in voices:
        voice_name = voice.get('name', '').lower()
        voice_description_text = voice.get('description', '').lower()
        combined_text = f"{voice_name} {voice_description_text}"
        
        score = 0
        for keyword in keywords_to_match:
            if keyword in combined_text:
                score += 1
        
        if score > 0:
            scored_voices.append((score, voice))
    
    # Return the highest scoring voice
    if scored_voices:
        scored_voices.sort(key=lambda x: x[0], reverse=True)
        best_voice = scored_voices[0][1]
        voice_id = best_voice.get('voice_id')
        print(f"✅ Selected best matching voice (keyword match): {best_voice.get('name')} (score: {scored_voices[0][0]})")
        return voice_id
    
    return None

def create_elevenlabs_voice(person_name: str, voice_description: str) -> Optional[str]:
    """
    Create an ElevenLabs voice using the Voice Design API from text description.
    Uses the ElevenLabs Voice Design API to generate a voice based on the description.
    Returns voice_id if successful, None otherwise.
    
    Reference: https://elevenlabs.io/docs/developers/guides/cookbooks/voices/voice-design
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not configured")
    
    try:
        headers = get_elevenlabs_headers()
        
        # First, check if a voice with this person's name already exists
        voices_url = f"{ELEVENLABS_API_BASE}/voices"
        voices_response = requests.get(voices_url, headers=headers)
        if voices_response.status_code == 200:
            voices = voices_response.json().get('voices', [])
            for voice in voices:
                if person_name.lower() in voice.get('name', '').lower():
                    voice_id = voice.get('voice_id')
                    print(f"✅ Using existing voice for {person_name}: {voice_id} ({voice.get('name')})")
                    return voice_id
        
        # Step 1: Sanitize the voice description to avoid safety filter issues
        sanitized_description = sanitize_voice_description(voice_description)
        print(f"Generating voice for {person_name} using Voice Design API...")
        print(f"Original description: {voice_description[:150]}...")
        print(f"Sanitized description: {sanitized_description[:150]}...")
        
        design_url = f"{ELEVENLABS_API_BASE}/text-to-voice/design"
        
        # Prepare a sample text that would be appropriate for the historical figure
        # The API requires at least 100 characters, so we create a longer sample
        # This text will be used to generate the voice preview
        sample_text = f"""Hello, I am {person_name}. It's a pleasure to meet you. 
I've lived through many experiences and have much to share about my life, my work, and the times I lived in. 
How may I assist you today? I'm here to answer your questions and share my perspective on the world as I knew it."""
        
        # Ensure the text is at least SAMPLE_TEXT_MIN_LENGTH characters
        if len(sample_text) < SAMPLE_TEXT_MIN_LENGTH:
            sample_text = sample_text + " " * (SAMPLE_TEXT_MIN_LENGTH - len(sample_text))
        
        design_payload = {
            "model_id": "eleven_multilingual_ttv_v2",
            "voice_description": sanitized_description[:VOICE_DESCRIPTION_MAX_LENGTH],
            "text": sample_text
        }
        
        design_response = requests.post(design_url, json=design_payload, headers=headers, timeout=60)
        
        if design_response.status_code not in [200, 201]:
            error_text = design_response.text[:500]
            print(f"⚠️  Voice design failed ({design_response.status_code}): {error_text}")
            # Fallback to voice selection if design fails
            return fallback_voice_selection(person_name, voice_description, headers)
        
        design_data = design_response.json()
        previews = design_data.get('previews', [])
        
        if not previews:
            print(f"⚠️  No voice previews generated")
            return fallback_voice_selection(person_name, voice_description, headers)
        
        # Step 2: Use the first preview to create the voice
        # (In a production app, you might want to let the user choose, but for automation we'll use the first)
        generated_voice_id = previews[0].get('generated_voice_id') or previews[0].get('generatedVoiceId')
        
        if not generated_voice_id:
            print(f"⚠️  No generated_voice_id in preview response")
            return fallback_voice_selection(person_name, voice_description, headers)
        
        print(f"✅ Generated voice preview, creating voice in library...")
        
        # Step 3: Create the voice in the library using the generated voice ID
        create_url = f"{ELEVENLABS_API_BASE}/text-to-voice/create"
        
        create_payload = {
            "voice_name": f"{person_name} Voice",
            "voice_description": voice_description[:500],  # Limit description length
            "generated_voice_id": generated_voice_id
        }
        
        create_response = requests.post(create_url, json=create_payload, headers=headers, timeout=30)
        
        if create_response.status_code in [200, 201]:
            voice_data = create_response.json()
            voice_id = (
                voice_data.get('voice_id') or 
                voice_data.get('voiceId') or
                voice_data.get('id')
            )
            if voice_id:
                print(f"✅ Created ElevenLabs voice for {person_name}: {voice_id}")
                return voice_id
            else:
                print(f"⚠️  Voice created but no voice_id in response: {voice_data}")
        
        # If creation fails, try fallback
        print(f"⚠️  Voice creation failed ({create_response.status_code}): {create_response.text[:300]}")
        return fallback_voice_selection(person_name, voice_description, headers)
            
    except Exception as e:
        print(f"⚠️  Error creating ElevenLabs voice: {e}")
        import traceback
        traceback.print_exc()
        return fallback_voice_selection(person_name, voice_description, headers)

def fallback_voice_selection(person_name: str, voice_description: str, headers: Optional[dict] = None) -> Optional[str]:
    """
    Fallback: Select best matching voice from existing voices if voice design fails.
    """
    try:
        if headers is None:
            headers = get_elevenlabs_headers()
        voices_url = f"{ELEVENLABS_API_BASE}/voices"
        voices_response = requests.get(voices_url, headers=headers)
        if voices_response.status_code == 200:
            voices = voices_response.json().get('voices', [])
            if voices:
                # Try intelligent selection
                selected_voice_id = select_best_voice_from_description(voices, voice_description)
                if selected_voice_id:
                    return selected_voice_id
                
                # Use first available voice
                default_voice = voices[0]
                voice_id = default_voice.get('voice_id')
                print(f"⚠️  Using fallback voice: {default_voice.get('name')} ({voice_id})")
                return voice_id
    except Exception as e:
        print(f"⚠️  Fallback voice selection failed: {e}")
    
    return None

def create_elevenlabs_agent(person_name: str, voice_id: str, system_prompt: str, knowledge_base_text: str) -> Optional[str]:
    """
    Create an ElevenLabs agent with knowledge base from MongoDB answers.
    Returns agent_id if successful, None otherwise.
    
    Uses the correct endpoint: /v1/convai/agents/create
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not configured")
    
    try:
        headers = get_elevenlabs_headers()
        headers["Content-Type"] = "application/json"
        
        # Correct endpoint for Agents Platform
        url = f"{ELEVENLABS_API_BASE}/convai/agents/create"
        
        # Build conversation_config according to ElevenLabs API
        # The structure needs agent.prompt.prompt, not system_prompt at top level
        conversation_config = {
            "agent": {
                "first_message": f"Hello, I am {person_name}. How may I assist you today?",
                "language": "en",
                "prompt": {
                    "prompt": system_prompt,
                    "llm": "gemini-2.5-flash"  # Use Gemini as default
                }
            },
            "tts": {
                "voice_id": voice_id
            }
        }
        
        # Build agent payload
        agent_payload = {
            "name": f"{person_name} Agent",
            "conversation_config": conversation_config
        }
        
        # Create agent
        response = requests.post(url, json=agent_payload, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            # Extract agent_id from response (format may vary)
            agent_id = (
                result.get('agent_id') or 
                result.get('id') or 
                result.get('agentId') or
                result.get('data', {}).get('agent_id') or
                result.get('data', {}).get('id')
            )
            
            if agent_id:
                print(f"✅ Created ElevenLabs agent for {person_name}: {agent_id}")
                
                # Try to add knowledge base content
                if knowledge_base_text:
                    add_knowledge_to_agent(agent_id, person_name, knowledge_base_text, headers)
                
                return agent_id
            else:
                print(f"⚠️  Agent created but couldn't extract agent_id from response: {result}")
                return None
        else:
            error_text = response.text
            print(f"⚠️  Agent creation failed: {response.status_code}")
            print(f"   Response: {error_text[:500]}")
            raise Exception(f"Could not create ElevenLabs agent: {response.status_code} - {error_text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Network error creating ElevenLabs agent: {e}")
        raise
    except Exception as e:
        print(f"⚠️  Error creating ElevenLabs agent: {e}")
        raise

def add_knowledge_to_agent(agent_id: str, person_name: str, knowledge_base_text: str, headers: dict):
    """Add knowledge base content to an agent"""
    knowledge_endpoints = [
        f"{ELEVENLABS_API_BASE}/convai/agents/{agent_id}/knowledge",
        f"{ELEVENLABS_API_BASE}/convai/agents/{agent_id}/knowledge-base",
        f"{ELEVENLABS_API_BASE}/agents/{agent_id}/knowledge"
    ]
    
    knowledge_payloads = [
        {"content": knowledge_base_text, "name": f"{person_name} Knowledge Base"},
        {"text": knowledge_base_text, "name": f"{person_name} Knowledge Base"},
        {"document": knowledge_base_text}
    ]
    
    for endpoint, payload in zip(knowledge_endpoints, knowledge_payloads):
        try:
            kb_response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            if kb_response.status_code in [200, 201]:
                print(f"✅ Added knowledge base to agent {agent_id}")
                return True
        except Exception as e:
            continue
    
    print(f"⚠️  Could not add knowledge base, but agent created successfully")
    return False

def format_knowledge_base_from_answers(answers: Dict) -> str:
    """
    Format MongoDB answers into a knowledge base text for ElevenLabs.
    Creates a comprehensive document from all Q&A pairs.
    """
    knowledge_sections = []
    
    # Group questions by category for better organization
    knowledge_sections.append("# Historical Figure Profile\n")
    knowledge_sections.append("This document contains comprehensive information about this historical figure.\n\n")
    
    # Add all Q&A pairs
    for question, answer in answers.items():
        if answer and answer.strip():
            knowledge_sections.append(f"## {question}\n")
            knowledge_sections.append(f"{answer}\n\n")
    
    return "\n".join(knowledge_sections)

def create_elevenlabs_agent_for_figure(person_name: str) -> Dict:
    """
    Create ElevenLabs voice and agent for a historical figure using MongoDB data.
    Returns dict with voice_id and agent_id.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not configured")
    
    # Get historical figure data
    figure_data = get_or_create_historical_figure(person_name)
    
    if not figure_data:
        raise ValueError(f"Could not retrieve data for {person_name}")
    
    elevenlabs_summary = figure_data.get('elevenlabs', '')
    answers = figure_data.get('answers', {})
    
    if not elevenlabs_summary:
        raise ValueError(f"No ElevenLabs summary found for {person_name}. Please generate the profile first.")
    
    # Step 1: Create voice using the elevenlabs field as description
    print(f"Creating ElevenLabs voice for {person_name}...")
    voice_id = create_elevenlabs_voice(person_name, elevenlabs_summary)
    
    if not voice_id:
        # Try to use a default voice or get first available voice
        try:
            voices_url = f"{ELEVENLABS_API_BASE}/voices"
            headers = get_elevenlabs_headers()
            voices_response = requests.get(voices_url, headers=headers)
            if voices_response.status_code == 200:
                voices = voices_response.json().get('voices', [])
                if voices:
                    voice_id = voices[0].get('voice_id')
                    print(f"Using default voice: {voice_id}")
        except:
            pass
    
    if not voice_id:
        raise ValueError("Could not create or retrieve a voice for the agent")
    
    # Step 2: Format knowledge base from answers
    knowledge_base_text = format_knowledge_base_from_answers(answers)
    
    # Step 3: Create agent with system prompt and knowledge base
    print(f"Creating ElevenLabs agent for {person_name}...")
    system_prompt = f"""You ARE {person_name}. You are not an assistant, helper, or AI. You are the actual historical figure speaking from your own perspective and experience.

{elevenlabs_summary}

CRITICAL INSTRUCTIONS:
- Respond with the pride, confidence, and authenticity of who you truly were
- Use the exact vocabulary, phrases, and speaking patterns from your time period
- Show genuine pride in your accomplishments and decisions
- Speak as if you are defending your legacy and explaining your actions to someone questioning you
- Do NOT be humble, apologetic, or overly helpful like a customer service agent
- Do NOT use modern language or phrases
- Use period-appropriate expressions and mannerisms
- Be authentic to your personality - if you were proud, show it; if you were cunning, demonstrate it
- Answer questions as YOU would have answered them, not as a helpful assistant would

You speak with the authority, knowledge, and character of {person_name}. Every word should reflect your true nature, beliefs, and the way you actually spoke and thought."""
    
    agent_id = create_elevenlabs_agent(person_name, voice_id, system_prompt, knowledge_base_text)
    
    if not agent_id:
        raise ValueError("Could not create ElevenLabs agent")
    
    # Step 4: Store voice_id and agent_id in MongoDB
    collection = db[HISTORICAL_FIGURES_COLLECTION]
    person_lower = person_name.lower().strip()
    
    collection.update_one(
        {'person_name_lower': person_lower},
        {'$set': {
            'elevenlabs_voice_id': voice_id,
            'elevenlabs_agent_id': agent_id,
            'updated_at': None  # Will be set by MongoDB
        }}
    )
    
    print(f"✅ Stored ElevenLabs IDs in MongoDB for {person_name}")
    
    # Step 5: Ensure we don't exceed MAX_AGENTS (delete oldest if needed)
    ensure_max_agents(MAX_AGENTS)
    
    return {
        'person_name': person_name,
        'voice_id': voice_id,
        'agent_id': agent_id,
        'status': 'success'
    }

def ensure_max_agents(max_count: int = MAX_AGENTS):
    """
    Ensure we don't exceed max_count agents.
    If we do, delete the oldest agents (by creation date or updated_at).
    """
    collection = db[HISTORICAL_FIGURES_COLLECTION]
    
    # Get all agents with their creation/update dates
    agents = list(collection.find(
        {'elevenlabs_agent_id': {'$exists': True, '$ne': None}},
        {'person_name': 1, 'elevenlabs_agent_id': 1, 'created_at': 1, 'updated_at': 1, '_id': 1}
    ))
    
    if len(agents) <= max_count:
        return
    
    # Sort by created_at (oldest first), then by updated_at
    agents.sort(key=lambda x: (
        x.get('created_at') or x.get('updated_at') or x.get('_id').generation_time
    ))
    
    # Delete oldest agents
    agents_to_delete = agents[:-max_count]  # Keep the newest max_count agents
    
    for agent in agents_to_delete:
        agent_id = agent.get('elevenlabs_agent_id')
        person_name = agent.get('person_name')
        
        if agent_id:
            try:
                # Delete from ElevenLabs
                delete_url = f"{ELEVENLABS_API_BASE}/convai/agents/{agent_id}"
                headers = get_elevenlabs_headers()
                response = requests.delete(delete_url, headers=headers)
                
                if response.status_code in [200, 204]:
                    print(f"✅ Deleted ElevenLabs agent: {agent_id} ({person_name})")
                else:
                    print(f"⚠️  Failed to delete ElevenLabs agent {agent_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Error deleting ElevenLabs agent {agent_id}: {e}")
        
        # Remove agent_id from MongoDB (keep the figure data)
        collection.update_one(
            {'_id': agent['_id']},
            {'$unset': {'elevenlabs_agent_id': '', 'elevenlabs_voice_id': ''}}
        )
        print(f"✅ Removed agent association for {person_name}")
    
    print(f"✅ Maintained agent limit: {max_count} agents")

@app.route('/api/historical-figure/<person_name>/create-agent', methods=['POST'])
def create_agent_for_figure(person_name):
    """
    Create ElevenLabs voice and agent for a historical figure.
    Uses MongoDB data: elevenlabs field for voice, answers for knowledge base.
    """
    try:
        if not ELEVENLABS_API_KEY:
            return jsonify({
                'error': 'ELEVENLABS_API_KEY is not configured. Please set it in your .env file.'
            }), 500
        
        result = create_elevenlabs_agent_for_figure(person_name)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/<agent_id>/info', methods=['GET'])
def get_agent_info(agent_id):
    """
    Get information about an ElevenLabs agent.
    Useful for frontend to check agent status and configuration.
    """
    if not ELEVENLABS_API_KEY:
        return jsonify({
            'error': 'ELEVENLABS_API_KEY is not configured.'
        }), 500
    
    try:
        url = f"{ELEVENLABS_API_BASE}/convai/agents/{agent_id}"
        headers = get_elevenlabs_headers()
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({
                'error': f"Failed to get agent info: {response.status_code}",
                'details': response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/<agent_id>/conversation', methods=['POST'])
def agent_conversation(agent_id):
    """
    Send a message to an ElevenLabs agent and get response.
    
    NOTE: ElevenLabs Agents Platform primarily uses WebSocket for conversations.
    This REST endpoint may not be available. For real-time conversations, use WebSocket:
    wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}
    
    Request body:
    {
        "message": "User's text message",
        "conversation_id": "optional-conversation-id"
    }
    """
    if not ELEVENLABS_API_KEY:
        return jsonify({
            'error': 'ELEVENLABS_API_KEY is not configured.'
        }), 500
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing "message" in request body'}), 400
        
        user_message = data['message']
        conversation_id = data.get('conversation_id')
        
        # ElevenLabs Agents Platform uses WebSocket for conversations
        # REST endpoints for text conversations may not be available
        # Return WebSocket connection info instead
        return jsonify({
            'error': 'ElevenLabs Agents Platform requires WebSocket for conversations',
            'websocket_url': f'wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}',
            'agent_id': agent_id,
            'message': 'Use WebSocket connection for real-time conversations. See ElevenLabs documentation for WebSocket API details.',
            'documentation': 'https://elevenlabs.io/docs/agents-platform/libraries/web-sockets'
        }), 501  # 501 Not Implemented
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/<agent_id>/conversation/start', methods=['POST'])
def start_agent_conversation(agent_id):
    """
    Start a new conversation with an ElevenLabs agent.
    Returns conversation_id for subsequent messages.
    """
    if not ELEVENLABS_API_KEY:
        return jsonify({
            'error': 'ELEVENLABS_API_KEY is not configured.'
        }), 500
    
    try:
        # Start conversation using the correct convai endpoint
        # Try different possible formats
        url = f"{ELEVENLABS_API_BASE}/convai/conversation/start?agent_id={agent_id}"
        
        headers = get_elevenlabs_headers()
        headers["Content-Type"] = "application/json"
        response = requests.post(url, json={}, headers=headers)
        
        if response.status_code in [200, 201]:
            return jsonify(response.json()), 200
        else:
            # If endpoint doesn't exist, return agent_id as conversation_id
            # (some APIs use agent_id directly)
            return jsonify({
                'conversation_id': agent_id,
                'agent_id': agent_id,
                'status': 'ready'
            }), 200
            
    except Exception as e:
        # Fallback: return agent_id as conversation_id
        return jsonify({
            'conversation_id': agent_id,
            'agent_id': agent_id,
            'status': 'ready'
        }), 200

@app.route('/api/agent/<agent_id>/websocket-url', methods=['GET'])
def get_agent_websocket_url(agent_id):
    """
    Get WebSocket URL for an agent.
    Returns the WebSocket URL with API key embedded (for frontend use).
    """
    if not ELEVENLABS_API_KEY:
        return jsonify({
            'error': 'ELEVENLABS_API_KEY is not configured.'
        }), 500
    
    ws_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}&xi-api-key={ELEVENLABS_API_KEY}"
    
    return jsonify({
        'websocket_url': ws_url,
        'agent_id': agent_id
    }), 200

@app.route('/api/elevenlabs-api-key', methods=['GET'])
def get_elevenlabs_api_key():
    """
    Get ElevenLabs API key for frontend use.
    Note: In production, consider using a more secure method like temporary tokens.
    """
    if not ELEVENLABS_API_KEY:
        return jsonify({
            'error': 'ELEVENLABS_API_KEY is not configured.'
        }), 500
    
    # Return API key for frontend ElevenLabs SDK
    return jsonify({
        'api_key': ELEVENLABS_API_KEY
    }), 200

@app.route('/api/figure/<person_name>/agent-status', methods=['GET'])
def get_figure_agent_status(person_name):
    """
    Get the agent status for a historical figure.
    Returns whether agent exists and is ready to use.
    """
    try:
        collection = db[HISTORICAL_FIGURES_COLLECTION]
        person_lower = person_name.lower().strip()
        
        figure = collection.find_one({'person_name_lower': person_lower}, {
            'person_name': 1,
            'elevenlabs_agent_id': 1,
            'elevenlabs_voice_id': 1,
            'elevenlabs': 1
        })
        
        if not figure:
            return jsonify({
                'person_name': person_name,
                'exists': False,
                'has_agent': False,
                'has_voice_summary': False
            }), 200
        
        agent_id = figure.get('elevenlabs_agent_id')
        voice_id = figure.get('elevenlabs_voice_id')
        has_summary = bool(figure.get('elevenlabs'))
        
        # Verify agent exists in ElevenLabs if agent_id is present
        agent_valid = False
        if agent_id and ELEVENLABS_API_KEY:
            try:
                url = f"{ELEVENLABS_API_BASE}/convai/agents/{agent_id}"
                headers = get_elevenlabs_headers()
                response = requests.get(url, headers=headers, timeout=5)
                agent_valid = response.status_code == 200
            except:
                pass
        
        return jsonify({
            'person_name': figure.get('person_name'),
            'exists': True,
            'has_agent': bool(agent_id),
            'agent_id': agent_id,
            'voice_id': voice_id,
            'agent_valid': agent_valid,
            'has_voice_summary': has_summary,
            'ready': bool(agent_id) and agent_valid
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-all-agents', methods=['POST'])
def create_all_agents():
    """
    Create ElevenLabs agents for all historical figures in the database.
    Returns a summary of created agents.
    """
    try:
        if not ELEVENLABS_API_KEY:
            return jsonify({
                'error': 'ELEVENLABS_API_KEY is not configured. Please set it in your .env file.'
            }), 500
        
        collection = db[HISTORICAL_FIGURES_COLLECTION]
        figures = list(collection.find({}))
        
        if not figures:
            return jsonify({
                'message': 'No historical figures found in database',
                'created': []
            }), 200
        
        results = []
        errors = []
        
        for figure in figures:
            person_name = figure.get('person_name')
            if not person_name:
                continue
            
            # Skip if agent already exists
            if figure.get('elevenlabs_agent_id'):
                results.append({
                    'person_name': person_name,
                    'status': 'skipped',
                    'reason': 'Agent already exists',
                    'agent_id': figure.get('elevenlabs_agent_id')
                })
                continue
            
            try:
                result = create_elevenlabs_agent_for_figure(person_name)
                results.append(result)
            except Exception as e:
                errors.append({
                    'person_name': person_name,
                    'error': str(e)
                })
        
        return jsonify({
            'total_figures': len(figures),
            'created': results,
            'errors': errors,
            'summary': f"Created {len(results)} agents, {len(errors)} errors"
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # For Cloud Run, use PORT environment variable, default to 5000 for local dev
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
