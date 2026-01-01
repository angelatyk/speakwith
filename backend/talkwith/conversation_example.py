#!/usr/bin/env python3
"""
Simple example showing how to use POST calls to have a conversation with a historical figure.
This demonstrates the conversation flow with the API.
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def print_conversation(history):
    """Print the full conversation transcript"""
    print("\n" + "=" * 70)
    print("CONVERSATION TRANSCRIPT:")
    print("=" * 70)
    for i, msg in enumerate(history, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if role == 'user':
            print(f"\n[{i}] You: {content}")
        elif role == 'assistant':
            print(f"[{i}] {person_name}: {content}")
    print("=" * 70 + "\n")

def have_conversation(person_name):
    """Demonstrate conversation using POST calls"""
    
    print(f"Starting conversation with {person_name}...\n")
    
    # Initialize empty conversation history
    conversation_history = []
    
    # Example conversation flow
    messages = [
        "Hello, how are you?",
        "What did you think about the American Revolution?",
        "Can you tell me more about your role in it?"
    ]
    
    for user_message in messages:
        print(f"\n📤 Sending: {user_message}")
        
        # Make POST request
        response = requests.post(
            f"{BASE_URL}/api/conversation/{person_name}",
            json={
                "message": user_message,
                "history": conversation_history
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract response
            ai_response = data.get('response', '')
            updated_history = data.get('conversation_history', [])
            
            print(f"📥 Response: {ai_response[:100]}...")
            
            # Update conversation history for next request
            conversation_history = updated_history
            
            # Show full transcript
            print_conversation(conversation_history)
        else:
            error = response.json().get('error', 'Unknown error')
            print(f"❌ Error: {error}")
            break
    
    # Final conversation transcript
    print("\n" + "=" * 70)
    print("FINAL CONVERSATION TRANSCRIPT:")
    print("=" * 70)
    for msg in conversation_history:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if role == 'user':
            print(f"\nYou: {content}")
        elif role == 'assistant':
            print(f"{person_name}: {content}")
    print("=" * 70)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python conversation_example.py <historical_figure_name>")
        print("Example: python conversation_example.py 'Thomas Paine'")
        sys.exit(1)
    
    person_name = sys.argv[1]
    have_conversation(person_name)

