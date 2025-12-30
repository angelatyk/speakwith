import os
import re
from typing import Dict

import google.generativeai as genai
from data.historical_figures_questions import HISTORICAL_FIGURE_QUESTIONS

# Google Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not set. Gemini features will not work.")


def get_available_gemini_model() -> str:
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
