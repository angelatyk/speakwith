#!/usr/bin/env python3
"""
Interactive chat script for conversing with historical figures with ElevenLabs integration.
Maintains conversation history and prepares responses for voice synthesis.
"""
import requests
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5000"
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID')  # Optional: specific voice ID

def send_to_elevenlabs(text, voice_id=None):
    """
    Send text to ElevenLabs API for text-to-speech conversion.
    Returns audio data if successful, None otherwise.
    """
    if not ELEVENLABS_API_KEY:
        return None
    
    try:
        url = "https://api.elevenlabs.io/v1/text-to-speech"
        
        # Use provided voice_id or default
        if not voice_id:
            voice_id = ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"  # Default voice
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(f"{url}/{voice_id}", json=data, headers=headers)
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"⚠️  ElevenLabs API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"⚠️  Error sending to ElevenLabs: {e}")
        return None

def save_audio(audio_data, filename):
    """Save audio data to a file"""
    try:
        with open(filename, 'wb') as f:
            f.write(audio_data)
        return True
    except Exception as e:
        print(f"⚠️  Error saving audio: {e}")
        return False

def chat_with_historical_figure(person_name):
    """Interactive chat session with a historical figure, with ElevenLabs integration"""
    
    # First, ensure the person exists in database and get their data
    print(f"Loading {person_name}...")
    response = requests.get(f"{BASE_URL}/api/historical-figure/{person_name}")
    if response.status_code != 200:
        print(f"Error: {response.json().get('error', 'Unknown error')}")
        return
    
    figure_data = response.json()
    elevenlabs_voice_summary = figure_data.get('elevenlabs', '')
    
    print(f"✅ {person_name} is ready to chat!\n")
    
    # Display ElevenLabs voice summary if available
    if elevenlabs_voice_summary:
        print("=" * 70)
        print("ELEVENLABS VOICE PROFILE:")
        print("=" * 70)
        print(elevenlabs_voice_summary)
        print("=" * 70)
        print()
    
    # Check ElevenLabs configuration
    if ELEVENLABS_API_KEY:
        print("✅ ElevenLabs API configured - responses will be sent for voice synthesis")
    else:
        print("⚠️  ElevenLabs API key not found in .env file")
        print("   Set ELEVENLABS_API_KEY to enable voice synthesis")
        print("   Responses will still be prepared for ElevenLabs but not automatically sent\n")
    
    print("Commands:")
    print("  'quit' or 'exit' - Exit chat")
    print("  'clear' - Reset conversation history")
    print("  'voice' - Show ElevenLabs voice profile")
    print("  'save <filename>' - Save last response to file (for ElevenLabs)")
    print()
    print("Type your messages:\n")
    
    conversation_history = []
    last_response = None
    response_counter = 0
    
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
            last_response = None
            print("Conversation history cleared.\n")
            continue
        
        if user_message.lower() == 'voice':
            print("\n" + "=" * 70)
            print("ELEVENLABS VOICE PROFILE:")
            print("=" * 70)
            print(elevenlabs_voice_summary if elevenlabs_voice_summary else "No voice profile available")
            print("=" * 70 + "\n")
            continue
        
        if user_message.lower().startswith('save '):
            if not last_response:
                print("No response to save. Send a message first.\n")
                continue
            filename = user_message[5:].strip()
            if not filename:
                filename = f"{person_name.replace(' ', '_')}_response_{response_counter}.txt"
            
            # Save text response
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Historical Figure: {person_name}\n")
                    f.write(f"Voice Profile: {elevenlabs_voice_summary}\n\n")
                    f.write(f"Response:\n{last_response}\n")
                print(f"✅ Saved response to {filename}\n")
            except Exception as e:
                print(f"⚠️  Error saving file: {e}\n")
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
                last_response = ai_response
                response_counter += 1
                
                print(f"\n{person_name}: {ai_response}\n")
                
                # Prepare data for ElevenLabs
                elevenlabs_data = {
                    "text": ai_response,
                    "voice_settings": {
                        "voice_profile": elevenlabs_voice_summary,
                        "person_name": person_name
                    }
                }
                
                # If ElevenLabs API key is configured, send automatically
                if ELEVENLABS_API_KEY:
                    print("🎤 Sending to ElevenLabs for voice synthesis...")
                    audio_data = send_to_elevenlabs(ai_response)
                    
                    if audio_data:
                        # Save audio file
                        audio_filename = f"{person_name.replace(' ', '_')}_response_{response_counter}.mp3"
                        if save_audio(audio_data, audio_filename):
                            print(f"✅ Audio saved to {audio_filename}\n")
                        else:
                            print("⚠️  Audio generated but could not be saved\n")
                    else:
                        print("⚠️  Could not generate audio\n")
                else:
                    # Show what would be sent to ElevenLabs
                    print("📋 Data prepared for ElevenLabs:")
                    print(f"   Text: {ai_response[:100]}...")
                    print(f"   Voice Profile: {elevenlabs_voice_summary[:100] if elevenlabs_voice_summary else 'N/A'}...")
                    print("   (Set ELEVENLABS_API_KEY in .env to enable automatic voice synthesis)\n")
                
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
        print("Usage: python elevenchat.py <historical_figure_name>")
        print("Example: python elevenchat.py 'Thomas Paine'")
        print("\nEnvironment variables:")
        print("  ELEVENLABS_API_KEY - Your ElevenLabs API key (optional)")
        print("  ELEVENLABS_VOICE_ID - Specific voice ID to use (optional)")
        sys.exit(1)
    
    person_name = sys.argv[1]
    chat_with_historical_figure(person_name)

