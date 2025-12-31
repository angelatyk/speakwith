import React, { useState, useEffect } from 'react';
import './App.css';
import AgentSearch from './components/AgentSearch';
import ElevenLabsChat from './components/ElevenLabsChat';
import Transcript from './components/Transcript';
import { Agent } from './types';
import api from './services/api';

function App() {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [transcript, setTranscript] = useState<Array<{role: 'user' | 'agent', text: string, timestamp: Date}>>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [apiKey, setApiKey] = useState<string | null>(null);

  // Get API key from backend for useConversation hook
  useEffect(() => {
    const fetchApiKey = async () => {
      try {
        const key = await api.getElevenLabsApiKey();
        setApiKey(key);
      } catch (error) {
        console.error('Failed to get ElevenLabs API key from backend:', error);
        // Fallback to environment variable if backend fails
        const envKey = process.env.REACT_APP_ELEVENLABS_API_KEY;
        if (envKey) {
          setApiKey(envKey);
        }
      }
    };
    
    fetchApiKey();
  }, []);

  const handleAgentSelect = (agent: Agent) => {
    setSelectedAgent(agent);
    setTranscript([]); // Clear transcript when switching agents
  };

  const handleNewMessage = (role: 'user' | 'agent', text: string) => {
    setTranscript(prev => [...prev, { role, text, timestamp: new Date() }]);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>TalkWith Historical Figures</h1>
      </header>
      
      <div className="main-container">
        <div className="chat-section">
          <ElevenLabsChat 
            agent={selectedAgent}
            onMessage={handleNewMessage}
            onConnectionChange={setIsConnected}
            apiKey={apiKey}
          />
          <Transcript messages={transcript} />
        </div>
        
        <div className="search-section">
          <AgentSearch 
            onAgentSelect={handleAgentSelect}
            selectedAgent={selectedAgent}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
