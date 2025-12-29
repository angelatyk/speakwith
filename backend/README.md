# Flask MongoDB Server

A barebones Flask server connected to a locally hosted MongoDB database.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure MongoDB is running locally on the default port (27017)

3. Run the Flask server:
   - The database will be automatically created on startup if it doesn't exist
```bash
python app.py
```

The server will start on `http://localhost:5000`

## Environment Variables

**Required:**
- `GEMINI_API_KEY`: Google Gemini API key (required for historical figure queries)

**Optional:**
- `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017/`)
- `DATABASE_NAME`: Database name (default: `talkwith`)
- `GOOGLE_CLOUD_PROJECT_ID`: Google Cloud Project ID (for Vertex AI embeddings)
- `GOOGLE_CLOUD_LOCATION`: Google Cloud location (default: `us-central1`)

## API Endpoints

### General Endpoints
- `GET /` - Server status
- `GET /health` - Health check with database connection test
- `GET /api/items?collection=<name>` - Get all items (default collection: `items`)
- `POST /api/items?collection=<name>` - Create a new item
- `GET /api/items/<id>?collection=<name>` - Get a specific item by ID
- `PUT /api/items/<id>?collection=<name>` - Update an item by ID
- `DELETE /api/items/<id>?collection=<name>` - Delete an item by ID

### Historical Figure Endpoints
- `GET /api/historical-figure/<person_name>` - Get or create historical figure profile
  - If the person exists in the database, returns cached data
  - If not found, queries Google Gemini API with 95 comprehensive questions and saves to database
  - Returns complete profile with all question-answer pairs and `elevenlabs` voice summary
- `GET /api/historical-figures` - List all historical figures in the database
- `POST /api/conversation/<person_name>` - Simulate a conversation with a historical figure
  - Request body: `{"message": "Your question", "history": []}` (optional)
  - Returns in-character response based on stored personality and voice data
- `POST /api/vector-search` - Semantic search across all historical figure Q&A pairs
  - Request body: `{"query": "search text", "person_name": "optional filter", "n_results": 5}`
  - Requires vector database to be built first (see Vector Database section)

## Example Usage

Create an item:
```bash
curl -X POST http://localhost:5000/api/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "value": 123}'
```

Get all items:
```bash
curl http://localhost:5000/api/items
```

### Historical Figure Examples

Get or create a historical figure profile (will query Gemini if not in database):
```bash
curl http://localhost:5000/api/historical-figure/Leonardo%20da%20Vinci
```

List all historical figures:
```bash
curl http://localhost:5000/api/historical-figures
```

## Historical Figure Questions

The system asks 80+ comprehensive questions covering:
- Basic information (name, dates, location, time period)
- Achievements and what they're known for
- Physical characteristics and voice
- Personality traits and character
- Personal quirks and habits
- Scandals and controversies
- Speech patterns and vernacular
- Relationships and social life
- Education and background
- Legacy and historical impact
- Communication style and memorable quotes
- Decision-making and work habits
- Psychological depth (fears, regrets, joys, coping mechanisms)
- Philosophical and spiritual beliefs
- Cultural and intellectual interests
- Health and aging
- Influence on others and leadership style
- Historical context and environment

All responses are stored in MongoDB for future use, avoiding redundant API calls.

## Vector Database (Vertex AI)

The system can create a vector database from MongoDB data for semantic search.

### Building the Vector Database

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Optional: Set up Vertex AI** (for better embeddings):
   - Set `GOOGLE_CLOUD_PROJECT_ID` in your `.env` file
   - Authenticate with Google Cloud: `gcloud auth application-default login`
   - If not set, ChromaDB will use default embeddings

3. **Build the vector database:**
   ```bash
   python build_vector_db.py
   ```

   This will:
   - Extract all Q&A pairs from MongoDB
   - Generate embeddings (Vertex AI if configured, otherwise ChromaDB default)
   - Store in a local ChromaDB database at `./chroma_db`

4. **Query the vector database:**
   ```bash
   # Via script
   python build_vector_db.py query "What was their personality like?" "Leonardo da Vinci"
   
   # Via API
   curl -X POST http://localhost:5000/api/vector-search \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What was their personality like?",
       "person_name": "Leonardo da Vinci",
       "n_results": 5
     }'
   ```

### Rebuilding the Vector Database

If you add new historical figures or update existing ones, rebuild the vector database:
```bash
python build_vector_db.py
```

The script will automatically clear and rebuild the entire database.

