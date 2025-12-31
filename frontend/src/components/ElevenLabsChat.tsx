import React, { useEffect, useState } from 'react';
import { Agent } from '../types';
import { ConversationBar } from './ui/conversation-bar';
import './ElevenLabsChat.css';

interface ElevenLabsChatProps {
  agent: Agent | null;
  onMessage: (role: 'user' | 'agent', text: string) => void;
  onConnectionChange: (connected: boolean) => void;
  apiKey: string | null;
}

const ElevenLabsChat: React.FC<ElevenLabsChatProps> = ({ 
  agent, 
  onMessage, 
  onConnectionChange,
  apiKey
}) => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Reset connection state when agent changes
    setIsConnected(false);
    onConnectionChange(false);
  }, [agent?.agent_id, onConnectionChange]);

  // Set API key in environment for useConversation hook
  useEffect(() => {
    if (apiKey && typeof window !== 'undefined') {
      // The useConversation hook reads from process.env or window
      // Set it in window for the hook to access
      (window as any).ELEVENLABS_API_KEY = apiKey;
    }
  }, [apiKey]);

  if (!agent || !agent.agent_id) {
    return (
      <div className="elevenlabs-chat">
        <div className="chat-header">
          <h2>Select an agent to start chatting</h2>
        </div>
        <div className="chat-container">
          <div className="no-agent-selected">
            <p>Please select or search for a historical figure to start chatting.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="elevenlabs-chat">
      <div className="chat-header">
        <h2>Chatting with {agent.name}</h2>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      
      <div className="chat-container">
        <ConversationBar
          agentId={agent.agent_id}
          apiKey={apiKey || undefined}
          agentName={agent.name}
          onConnect={() => {
            setIsConnected(true);
            onConnectionChange(true);
          }}
          onDisconnect={() => {
            setIsConnected(false);
            onConnectionChange(false);
          }}
          onMessage={(message: { source: "user" | "ai"; message: string }) => {
            // Map ElevenLabs message format to our format
            if (message.source === 'user') {
              onMessage('user', message.message);
            } else if (message.source === 'ai') {
              onMessage('agent', message.message);
            }
          }}
          onSendMessage={(message: string) => {
            // User message is already handled by onMessage with source='user'
            // This callback is for additional handling if needed
          }}
          onError={(error: Error) => {
            console.error('ConversationBar error:', error);
          }}
        />
      </div>
    </div>
  );
};

export default ElevenLabsChat;
