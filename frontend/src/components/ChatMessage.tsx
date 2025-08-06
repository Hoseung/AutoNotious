import React from 'react';
import ReactMarkdown from 'react-markdown';
import './ChatMessage.css';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  role, 
  content, 
  isStreaming = false 
}) => {
  return (
    <div className={`chat-message ${role}`}>
      <div className="message-role">
        {role === 'user' ? 'You' : 'Assistant'}
      </div>
      <div className="message-content">
        {role === 'assistant' ? (
          <ReactMarkdown>{content}</ReactMarkdown>
        ) : (
          <p>{content}</p>
        )}
        {isStreaming && <span className="streaming-indicator">●</span>}
      </div>
    </div>
  );
};