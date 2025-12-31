import React, { useEffect, useRef } from 'react';
import { TranscriptMessage } from '../types';
import './Transcript.css';

interface TranscriptProps {
  messages: TranscriptMessage[];
}

const Transcript: React.FC<TranscriptProps> = ({ messages }) => {
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="transcript">
      <div className="transcript-header">
        <h3>Conversation Transcript</h3>
        <span className="message-count">{messages.length} messages</span>
      </div>
      
      <div className="transcript-messages">
        {messages.length === 0 ? (
          <div className="empty-transcript">
            Your conversation will appear here...
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <div className="message-header">
                <span className="message-role">
                  {msg.role === 'user' ? '👤 You' : '🤖 Agent'}
                </span>
                <span className="message-time">{formatTime(msg.timestamp)}</span>
              </div>
              <div className="message-text">{msg.text}</div>
            </div>
          ))
        )}
        <div ref={transcriptEndRef} />
      </div>
    </div>
  );
};

export default Transcript;

