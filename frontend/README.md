# TalkWith Frontend

React frontend for chatting with historical figures using ElevenLabs Agents.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file (optional - API key is handled by backend):
```bash
cp .env.example .env
```

3. Update `.env` if needed:
```
REACT_APP_API_URL=http://localhost:5000
```

Note: The ElevenLabs API key is stored in the backend `.env` file, not the frontend.

4. Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Features

- **Search & Create Agents**: Search for historical figures and automatically create agents
- **Agent List**: View all available agents
- **Real-time Chat**: Chat with agents via WebSocket
- **Transcript**: See conversation history
- **Auto-cleanup**: Automatically removes oldest agents when exceeding 30

## Requirements

- Flask backend running on `http://localhost:5000`
- ElevenLabs API key with Agents Platform access
