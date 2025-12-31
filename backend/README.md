# Historical Figure Profile API

A Flask server that queries Google Gemini to create comprehensive profiles of historical figures and stores them in MongoDB.

## Features

- **95 Comprehensive Questions**: Queries Gemini with 95 detailed questions about historical figures
- **MongoDB Storage**: Stores all Q&A pairs and responses in MongoDB
- **ElevenLabs Voice Summary**: Automatically generates a 1000-character voice and personality summary using Gemini
- **Smart Caching**: Checks database first to avoid redundant API calls

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables in `.env`:
```
GEMINI_API_KEY=your-gemini-api-key
MONGO_URI=mongodb://localhost:27017/  # Optional
DATABASE_NAME=talkwith  # Optional
```

3. Make sure MongoDB is running locally on the default port (27017)

4. Run the Flask server:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Health Check
- `GET /` - Server status
- `GET /health` - Health check with database connection test

### Historical Figures (Frontend-Ready)

**List all figures:**
- `GET /api/historical-figures` - List all historical figures
  - Returns: `{figures: [{id, name, has_agent, agent_id, voice_id}], count}`
  - Perfect for displaying available figures in your React app

**Search figures:**
- `GET /api/historical-figures/search?q=<query>` - Search historical figures by name
  - Returns: `{query, figures: [{id, name, has_agent, agent_id, voice_id}], count}`
  - Case-insensitive search

**Get or create figure:**
- `GET /api/historical-figure/<person_name>` - Get or create historical figure profile
  - If person exists in database, returns cached data
  - If not found, queries Gemini API with 95 questions and saves to database
  - Automatically generates ElevenLabs voice/personality summary
  - Returns complete profile with all question-answer pairs and `elevenlabs` field

**Create figure with agent (one-step):**
- `POST /api/historical-figure/<person_name>/create-with-agent` - Create figure AND agent in one call
  - Gets or creates historical figure profile
  - Creates ElevenLabs voice and agent automatically
  - Returns: `{figure: {...}, agent: {agent_id, voice_id, status, ready}}`
  - **Perfect for frontend**: User searches → creates → ready to chat

**Check agent status:**
- `GET /api/figure/<person_name>/agent-status` - Get agent status for a figure
  - Returns: `{person_name, exists, has_agent, agent_id, voice_id, agent_valid, ready}`
  - Useful for checking if agent is ready before starting conversation

### ElevenLabs Agent Creation

- `POST /api/historical-figure/<person_name>/create-agent` - Create ElevenLabs voice and agent
  - Creates a voice using the `elevenlabs` field from MongoDB as voice description
  - Creates an agent trained on all Q&A pairs from MongoDB `answers` field
  - Stores `elevenlabs_voice_id` and `elevenlabs_agent_id` in MongoDB
  - Returns voice_id and agent_id

- `POST /api/create-all-agents` - Create ElevenLabs agents for all historical figures
  - Processes all figures in the database
  - Skips figures that already have agents
  - Returns summary of created agents

### ElevenLabs Agent Communication

- `GET /api/agent/<agent_id>/info` - Get agent information
  - Returns agent configuration and status

- `POST /api/agent/<agent_id>/conversation/start` - Start a new conversation
  - Returns `conversation_id` for subsequent messages

- `POST /api/agent/<agent_id>/conversation` - Send message to agent
  - Request: `{message: "text", conversation_id: "optional"}`
  - Returns agent's response
  - Use this for text-based conversation with the agent

## Example Usage

Get or create a historical figure profile:
```bash
curl "http://localhost:5000/api/historical-figure/Thomas%20Paine"
```

List all historical figures:
```bash
curl "http://localhost:5000/api/historical-figures"
```

Create ElevenLabs agent for a historical figure:
```bash
curl -X POST "http://localhost:5000/api/historical-figure/Thomas%20Paine/create-agent"
```

Create agents for all historical figures:
```bash
curl -X POST "http://localhost:5000/api/create-all-agents"
```

### Frontend Integration Examples

**List all available figures:**
```bash
curl "http://localhost:5000/api/historical-figures"
```

**Search for a figure:**
```bash
curl "http://localhost:5000/api/historical-figures/search?q=thomas"
```

**Create figure and agent in one call (recommended for frontend):**
```bash
curl -X POST "http://localhost:5000/api/historical-figure/Thomas%20Paine/create-with-agent"
```

**Check if agent is ready:**
```bash
curl "http://localhost:5000/api/figure/Thomas%20Paine/agent-status"
```

**Start conversation with agent:**
```bash
# Start conversation
curl -X POST "http://localhost:5000/api/agent/<agent_id>/conversation/start"

# Send message
curl -X POST "http://localhost:5000/api/agent/<agent_id>/conversation" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## Response Format

The API returns a JSON object with:
- `person_name`: Full name of the historical figure
- `person_name_lower`: Lowercase version for lookups
- `questions`: Array of all 95 questions asked
- `answers`: Dictionary mapping questions to answers
- `full_response`: Raw response from Gemini
- `elevenlabs`: 1000-character summary of voice and personality (for ElevenLabs)
- `_id`: MongoDB document ID

## How It Works

1. **Receive person name** via GET request
2. **Check MongoDB** - If person exists, return cached data
3. **Query Gemini** - If not found, send all 95 questions to Gemini
4. **Parse responses** - Extract individual Q&A pairs from Gemini's response
5. **Generate voice summary** - Query Gemini again to create voice/personality summary
6. **Store in MongoDB** - Save everything including the `elevenlabs` field
7. **Return complete profile** - JSON response with all data

## Database Structure

Each historical figure document contains:
- Basic identification (name, normalized name)
- All 95 questions
- All 95 answers (parsed from Gemini)
- Full Gemini response
- ElevenLabs voice/personality summary (1000 chars or less)

## Environment Variables

**Required:**
- `GEMINI_API_KEY`: Google Gemini API key

**Optional:**
- `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017/`)
- `DATABASE_NAME`: Database name (default: `talkwith`)
- `ELEVENLABS_API_KEY`: ElevenLabs API key (required for agent creation)
