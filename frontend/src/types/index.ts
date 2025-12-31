export interface Agent {
  id: string;
  name: string;
  has_agent: boolean;
  agent_id: string | null;
  voice_id: string | null;
}

export interface TranscriptMessage {
  role: 'user' | 'agent';
  text: string;
  timestamp: Date;
}

