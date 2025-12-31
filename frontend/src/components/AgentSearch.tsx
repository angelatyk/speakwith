import React, { useState, useEffect } from 'react';
import { Agent } from '../types';
import api from '../services/api';
import './AgentSearch.css';

interface AgentSearchProps {
  onAgentSelect: (agent: Agent) => void;
  selectedAgent: Agent | null;
}

const AgentSearch: React.FC<AgentSearchProps> = ({ onAgentSelect, selectedAgent }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await api.listAgents();
      setAgents(response.figures.filter(a => a.has_agent));
    } catch (err: any) {
      setError(err.message || 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      return;
    }

    setCreating(true);
    setError(null);

    try {
      // Check if agent already exists
      const status = await api.getAgentStatus(searchQuery);
      
      if (status.ready && status.agent_id) {
        // Agent exists and is ready
        const agent: Agent = {
          id: status.person_name,
          name: status.person_name,
          has_agent: true,
          agent_id: status.agent_id,
          voice_id: status.voice_id
        };
        onAgentSelect(agent);
        await loadAgents(); // Refresh list
      } else {
        // Create new agent
        const response = await api.createFigureWithAgent(searchQuery);
        
        if (response.agent.ready && response.agent.agent_id) {
          const agent: Agent = {
            id: response.figure.person_name,
            name: response.figure.person_name,
            has_agent: true,
            agent_id: response.agent.agent_id,
            voice_id: response.agent.voice_id
          };
          onAgentSelect(agent);
          await loadAgents(); // Refresh list
          setSearchQuery(''); // Clear search
        } else {
          setError('Agent creation is still in progress. Please wait a moment and try again.');
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Failed to create agent');
      console.error('Error creating agent:', err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="agent-search">
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          placeholder="Who do you want to chat with?"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          disabled={creating}
          className="search-input"
        />
        <button 
          type="submit" 
          disabled={creating || !searchQuery.trim()}
          className="search-button"
        >
          {creating ? 'Creating...' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="agents-list">
        <h3>Available Agents ({agents.length})</h3>
        {loading ? (
          <div className="loading">Loading agents...</div>
        ) : agents.length === 0 ? (
          <div className="empty-state">No agents created yet. Search for a historical figure to get started!</div>
        ) : (
          <div className="agents-grid">
            {agents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => onAgentSelect(agent)}
                className={`agent-card ${selectedAgent?.id === agent.id ? 'selected' : ''}`}
              >
                <div className="agent-name">{agent.name}</div>
                <div className="agent-status">
                  {agent.agent_id ? '✓ Ready' : 'Creating...'}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentSearch;

