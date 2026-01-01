#!/usr/bin/env python3
"""Clear MongoDB database collections"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'talkwith')

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

print(f"Connected to database: {DATABASE_NAME}")
print(f"Collections: {db.list_collection_names()}")

# Clear historical figures
result = db.historical_figures.delete_many({})
print(f"\n✅ Deleted {result.deleted_count} historical figure(s)")

# Optionally clear other collections
# db.items.delete_many({})
# print("✅ Cleared items collection")

print("\nDatabase cleared!")

