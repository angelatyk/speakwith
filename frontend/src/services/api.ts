import axios from 'axios';
import { Agent } from '../types';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export interface AgentListResponse {
  figures: Agent[];
  count: number;
}

export interface AgentStatusResponse {
  person_name: string;
  exists: boolean;
  has_agent: boolean;
  agent_id: string | null;
  voice_id: string | null;
  agent_valid: boolean;
  ready: boolean;
}

export interface CreateAgentResponse {
  figure: any;
  agent: {
    agent_id: string;
    voice_id: string;
    status: string;
    ready: boolean;
  };
}

const api = {
  // List all historical figures
  listAgents: async (): Promise<AgentListResponse> => {
    const response = await axios.get(`${API_BASE}/api/historical-figures`);
    return response.data;
  },

  // Search for historical figures
  searchAgents: async (query: string): Promise<AgentListResponse> => {
    const response = await axios.get(`${API_BASE}/api/historical-figures/search`, {
      params: { q: query }
    });
    return response.data;
  },

  // Get agent status
  getAgentStatus: async (personName: string): Promise<AgentStatusResponse> => {
    const response = await axios.get(`${API_BASE}/api/figure/${encodeURIComponent(personName)}/agent-status`);
    return response.data;
  },

  // Create figure and agent
  createFigureWithAgent: async (personName: string): Promise<CreateAgentResponse> => {
    const response = await axios.post(`${API_BASE}/api/historical-figure/${encodeURIComponent(personName)}/create-with-agent`);
    return response.data;
  },

  // Get WebSocket URL for an agent (with API key embedded)
  getWebSocketUrl: async (agentId: string): Promise<string> => {
    const response = await axios.get(`${API_BASE}/api/agent/${agentId}/websocket-url`);
    return response.data.websocket_url;
  },

  // Get ElevenLabs API key for SDK configuration
  getElevenLabsApiKey: async (): Promise<string> => {
    const response = await axios.get(`${API_BASE}/api/elevenlabs-api-key`);
    return response.data.api_key;
  }
};

export default api;

