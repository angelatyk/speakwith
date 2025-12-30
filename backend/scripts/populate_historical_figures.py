from app import build_historical_figure_document
from data.historical_figures_questions import HISTORICAL_FIGURE_QUESTIONS
from gemini_service import (
    generate_elevenlabs_voice_summary,
    query_gemini_for_historical_figure,
)
from repositories import historical_figures as hf_repo

# List of historical figures to preload
PRELOAD_FIGURES = [
    "Leonardo da Vinci",
    "Cleopatra",
    "Albert Einstein",
    "Marie Curie",
    "Mahatma Gandhi",
    "Martin Luther King Jr.",
]

for person_name in PRELOAD_FIGURES:
    # Check if already exists
    existing = hf_repo.find_by_name(person_name)
    if existing:
        print(f"{person_name} already exists in database, skipping.")
        continue

    print(f"Querying Gemini for {person_name}...")
    gemini_data = query_gemini_for_historical_figure(person_name)
    answers = gemini_data.get("answers", {})
    elevenlabs_summary = generate_elevenlabs_voice_summary(answers)

    document = build_historical_figure_document(person_name, gemini_data)

    result = hf_repo.insert_figure(document)
    print(f"Saved {person_name} with ID {result.inserted_id}")
