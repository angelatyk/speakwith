#!/usr/bin/env python3
"""
Get a historical figure's profile from MongoDB.
Shows different ways to retrieve and display the data.
"""
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import json

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'talkwith')

def get_profile(person_name, format='full'):
    """Get historical figure profile from MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db['historical_figures']
    
    # Find by name (case-insensitive)
    person_lower = person_name.lower().strip()
    figure = collection.find_one({'person_name_lower': person_lower})
    
    if not figure:
        print(f"❌ {person_name} not found in database")
        return None
    
    # Convert ObjectId to string for JSON serialization
    if '_id' in figure:
        figure['_id'] = str(figure['_id'])
    
    if format == 'full':
        return figure
    elif format == 'summary':
        return {
            'person_name': figure.get('person_name'),
            'total_questions': len(figure.get('questions', [])),
            'total_answers': len(figure.get('answers', {})),
            'has_elevenlabs': 'elevenlabs' in figure and figure.get('elevenlabs'),
            '_id': figure.get('_id')
        }
    elif format == 'answers':
        return figure.get('answers', {})
    elif format == 'elevenlabs':
        return {
            'person_name': figure.get('person_name'),
            'elevenlabs': figure.get('elevenlabs', 'Not available')
        }
    
    return figure

def list_all_figures():
    """List all historical figures in the database"""
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db['historical_figures']
    
    figures = list(collection.find({}, {
        'person_name': 1,
        'person_name_lower': 1,
        '_id': 1
    }))
    
    for fig in figures:
        fig['_id'] = str(fig['_id'])
    
    return figures

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python get_profile.py <person_name> [format]")
        print("  python get_profile.py --list")
        print("\nFormats:")
        print("  full      - Complete profile (default)")
        print("  summary   - Just basic info")
        print("  answers   - Just Q&A pairs")
        print("  elevenlabs - Just voice profile")
        print("\nExamples:")
        print("  python get_profile.py 'Thomas Paine'")
        print("  python get_profile.py 'Thomas Paine' summary")
        print("  python get_profile.py 'Thomas Paine' elevenlabs")
        print("  python get_profile.py --list")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        figures = list_all_figures()
        print(f"\n📋 Found {len(figures)} historical figure(s):\n")
        for fig in figures:
            print(f"  - {fig['person_name']} (ID: {fig['_id']})")
        sys.exit(0)
    
    person_name = sys.argv[1]
    format_type = sys.argv[2] if len(sys.argv) > 2 else 'full'
    
    profile = get_profile(person_name, format_type)
    
    if profile:
        print(f"\n✅ Profile for: {person_name}\n")
        print(json.dumps(profile, indent=2, ensure_ascii=False))
    else:
        sys.exit(1)

