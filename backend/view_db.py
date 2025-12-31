#!/usr/bin/env python3
"""Simple script to view MongoDB data"""
from pymongo import MongoClient
import json
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'talkwith')

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db['historical_figures']

# Get all historical figures
figures = list(collection.find())

print(f"\n{'='*70}")
print(f"MongoDB Database: {DATABASE_NAME}")
print(f"Collection: historical_figures")
print(f"Total documents: {len(figures)}")
print(f"{'='*70}\n")

if not figures:
    print("No historical figures found in database.")
else:
    for idx, figure in enumerate(figures, 1):
        print(f"\n{'#'*70}")
        print(f"Document #{idx}")
        print(f"{'#'*70}")
        print(f"Person Name: {figure.get('person_name', 'N/A')}")
        print(f"MongoDB ID: {figure.get('_id')}")
        
        # Show number of questions answered
        answers = figure.get('answers', {})
        print(f"\nTotal Questions Answered: {len(answers)}")
        
        # Show all questions and answers
        print(f"\n{'─'*70}")
        print("QUESTIONS AND ANSWERS:")
        print(f"{'─'*70}")
        
        for i, (question, answer) in enumerate(answers.items(), 1):
            print(f"\n[{i}] {question}")
            print(f"    Answer: {answer}")
            print()
        
        # Show full response if available
        if figure.get('full_response'):
            print(f"\n{'─'*70}")
            print("FULL GEMINI RESPONSE:")
            print(f"{'─'*70}")
            print(figure.get('full_response')[:500] + "..." if len(figure.get('full_response', '')) > 500 else figure.get('full_response'))
        
        print(f"\n{'#'*70}\n")

# Also show other collections
print(f"\n{'='*70}")
print("Other collections in database:")
print(f"{'='*70}")
for coll_name in db.list_collection_names():
    count = db[coll_name].count_documents({})
    print(f"  - {coll_name}: {count} documents")

