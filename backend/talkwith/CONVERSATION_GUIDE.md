# How Conversations Work in app.py

## Overview

The conversation system uses **POST requests** to `/api/conversation/<person_name>`. Each request includes:
1. Your message
2. The conversation history (so the AI remembers previous exchanges)

The API returns:
1. The AI's response
2. The **updated conversation history** (including your new message and the response)

## How It Works

### Step 1: First Message (No History)

```bash
curl -X POST "http://localhost:5000/api/conversation/Thomas%20Paine" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?"
  }'
```

**Response:**
```json
{
  "person": "Thomas Paine",
  "user_message": "Hello, how are you?",
  "response": "Greetings, friend. I am well, thank you...",
  "conversation_history": [
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "Greetings, friend. I am well, thank you..."}
  ]
}
```

### Step 2: Follow-up Message (With History)

**Important:** Include the `conversation_history` from the previous response!

```bash
curl -X POST "http://localhost:5000/api/conversation/Thomas%20Paine" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What did you think about British rule?",
    "history": [
      {"role": "user", "content": "Hello, how are you?"},
      {"role": "assistant", "content": "Greetings, friend. I am well, thank you..."}
    ]
  }'
```

**Response:**
```json
{
  "person": "Thomas Paine",
  "user_message": "What did you think about British rule?",
  "response": "I found it to be oppressive and unjust...",
  "conversation_history": [
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "Greetings, friend. I am well, thank you..."},
    {"role": "user", "content": "What did you think about British rule?"},
    {"role": "assistant", "content": "I found it to be oppressive and unjust..."}
  ]
}
```

## Key Points

1. **Stateless API**: The server doesn't store conversation history. You must include it in each request.

2. **Always use the returned history**: The API returns `conversation_history` - use this in your next request!

3. **History limit**: The API keeps only the last 10 messages (5 exchanges) to avoid token limits.

4. **Format**: History is an array of objects with `role` ("user" or "assistant") and `content` (the message text).

## Example Python Script

```python
import requests

BASE_URL = "http://localhost:5000"
person_name = "Thomas Paine"
conversation_history = []

# First message
response = requests.post(
    f"{BASE_URL}/api/conversation/{person_name}",
    json={"message": "Hello!"},
    headers={"Content-Type": "application/json"}
)
data = response.json()
conversation_history = data['conversation_history']  # Save for next request
print(f"Response: {data['response']}")

# Second message (with history)
response = requests.post(
    f"{BASE_URL}/api/conversation/{person_name}",
    json={
        "message": "Tell me about Common Sense",
        "history": conversation_history  # Include previous conversation
    },
    headers={"Content-Type": "application/json"}
)
data = response.json()
conversation_history = data['conversation_history']  # Update history
print(f"Response: {data['response']}")

# Print full transcript
print("\nFull Conversation:")
for msg in conversation_history:
    role = msg['role']
    content = msg['content']
    print(f"{role.upper()}: {content}")
```

## Using the Helper Scripts

**Simple chat (handles history automatically):**
```bash
python chat.py "Thomas Paine"
```

**Chat with ElevenLabs integration:**
```bash
python elevenchat.py "Thomas Paine"
```

**See example conversation flow:**
```bash
python conversation_example.py "Thomas Paine"
```

## Full Transcript

The `conversation_history` in the response contains the **complete transcript** of your conversation so far. Each message includes:
- `role`: "user" or "assistant"
- `content`: The actual message text

You can use this to:
- Display the full conversation
- Save it to a file
- Continue the conversation in the next request
- Show it to users in a UI

