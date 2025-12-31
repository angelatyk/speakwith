from data.historical_figures_questions import HISTORICAL_FIGURE_QUESTIONS
from services.gemini_service import generate_elevenlabs_voice_summary


def build_historical_figure_document(person_name: str, gemini_data: dict) -> dict:
    """Builds the historical figure document for MongoDB storage."""
    answers = gemini_data.get("answers", {})
    elevenlabs_summary = generate_elevenlabs_voice_summary(answers)

    return {
        "person_name": person_name,
        "person_name_lower": person_name.lower().strip(),
        "questions": HISTORICAL_FIGURE_QUESTIONS,
        "answers": answers,
        "full_response": gemini_data.get("full_response", ""),
        "elevenlabs": elevenlabs_summary,
        "created_at": None,  # Will be set by MongoDB
    }
