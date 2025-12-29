#!/usr/bin/env python3
"""
Interactive chat script for conversing with historical figures.
Maintains conversation history automatically.
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def chat_with_historical_figure(person_name):
    """Interactive chat session with a historical figure"""
    
    # First, ensure the person exists in database
    print(f"Loading {person_name}...")
    response = requests.get(f"{BASE_URL}/api/historical-figure/{person_name}")
    if response.status_code != 200:
        print(f"Error: {response.json().get('error', 'Unknown error')}")
        return
    
    print(f"✅ {person_name} is ready to chat!\n")
    print("Type your messages (or 'quit' to exit, 'clear' to reset conversation)\n")
    
    conversation_history = []
    
    while True:
        # Get user input
        user_message = input("You: ").strip()
        
        if not user_message:
            continue
        
        if user_message.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if user_message.lower() == 'clear':
            conversation_history = []
            print("Conversation history cleared.\n")
            continue
        
        # Send message
        try:
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
                ai_response = data.get('response', '')
                
                print(f"\n{person_name}: {ai_response}\n")
                
                # Add to history
                conversation_history.append({"role": "user", "content": user_message})
                conversation_history.append({"role": "assistant", "content": ai_response})
                
                # Keep only last 10 messages (5 exchanges) to avoid token limits
                if len(conversation_history) > 10:
                    conversation_history = conversation_history[-10:]
            else:
                error = response.json().get('error', 'Unknown error')
                print(f"Error: {error}\n")
        
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Is it running?\n")
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python chat.py <historical_figure_name>")
        print("Example: python chat.py 'Thomas Paine'")
        sys.exit(1)
    
    person_name = sys.argv[1]
    chat_with_historical_figure(person_name)

