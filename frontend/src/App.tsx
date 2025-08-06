import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { ChatMessage } from './components/ChatMessage';
import { ChatComposer } from './components/ChatComposer';
import { sessionApi, Message } from './services/api';
import { SSEClient } from './services/sse';

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState<string>('New Chat');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamContent, setCurrentStreamContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sseClient = useRef<SSEClient>(new SSEClient());

  useEffect(() => {
    initializeSession();
    return () => {
      sseClient.current.disconnect();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamContent]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeSession = async () => {
    try {
      const storedSessionId = localStorage.getItem('currentSessionId');
      
      if (storedSessionId) {
        const session = await sessionApi.get(storedSessionId);
        setSessionId(storedSessionId);
        setSessionTitle(session.title || 'New Chat');
        
        const { messages } = await sessionApi.getMessages(storedSessionId);
        setMessages(messages);
      } else {
        await createNewSession();
      }
    } catch (error) {
      console.error('Failed to initialize session:', error);
      await createNewSession();
    }
  };

  const createNewSession = async () => {
    try {
      const { id } = await sessionApi.create();
      setSessionId(id);
      setSessionTitle('New Chat');
      setMessages([]);
      localStorage.setItem('currentSessionId', id);
    } catch (error) {
      setError('Failed to create session');
      console.error('Failed to create session:', error);
    }
  };

  const handleNewChat = async () => {
    await createNewSession();
    setCurrentStreamContent('');
    setError(null);
    setSuccess(null);
  };

  const handleSendMessage = async (text: string) => {
    if (!sessionId || isStreaming) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);
    setCurrentStreamContent('');
    setError(null);

    try {
      await sseClient.current.connect(sessionId, text, {
        onMessage: (data) => {
          setCurrentStreamContent(prev => prev + data);
        },
        onError: (error) => {
          console.error('SSE error:', error);
          setError('Failed to get response');
          setIsStreaming(false);
        },
        onEnd: async () => {
          const assistantMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: currentStreamContent,
            created_at: new Date().toISOString(),
          };
          
          setMessages(prev => [...prev, assistantMessage]);
          setCurrentStreamContent('');
          setIsStreaming(false);
          
          const { messages } = await sessionApi.getMessages(sessionId);
          setMessages(messages);
        },
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message');
      setIsStreaming(false);
    }
  };

  const handleStopGenerating = () => {
    sseClient.current.disconnect();
    setIsStreaming(false);
    
    if (currentStreamContent) {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: currentStreamContent,
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setCurrentStreamContent('');
    }
  };

  const handleSummarize = async () => {
    if (!sessionId) return;

    try {
      const summary = await sessionApi.summarize(sessionId);
      setSessionTitle(summary.title);
      setSuccess('Session summarized successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      console.error('Failed to summarize:', error);
      setError('Failed to summarize session');
    }
  };

  const handleSaveToNotion = async () => {
    if (!sessionId) return;

    try {
      const notion = await sessionApi.saveToNotion(sessionId);
      setSuccess(`Saved to Notion! <a href="${notion.url}" target="_blank">View page</a>`);
      setTimeout(() => setSuccess(null), 5000);
    } catch (error: any) {
      console.error('Failed to save to Notion:', error);
      setError(error.response?.data?.detail || 'Failed to save to Notion');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="session-title">{sessionTitle}</h1>
        <div className="header-buttons">
          <button onClick={handleNewChat} className="header-button">
            New Chat
          </button>
          <button 
            onClick={handleSummarize} 
            className="header-button"
            disabled={messages.length === 0}
          >
            Summarize
          </button>
          <button 
            onClick={handleSaveToNotion} 
            className="header-button"
            disabled={messages.length === 0}
          >
            Save to Notion
          </button>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)} className="close-button">×</button>
        </div>
      )}

      {success && (
        <div className="success-banner" dangerouslySetInnerHTML={{ __html: success }} />
      )}

      <main className="chat-container">
        <div className="messages-list">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              role={message.role}
              content={message.content}
            />
          ))}
          {isStreaming && currentStreamContent && (
            <ChatMessage
              role="assistant"
              content={currentStreamContent}
              isStreaming={true}
            />
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="composer-container">
          {isStreaming && (
            <button onClick={handleStopGenerating} className="stop-button">
              Stop generating
            </button>
          )}
          <ChatComposer
            onSend={handleSendMessage}
            disabled={isStreaming || !sessionId}
            placeholder={isStreaming ? "Waiting for response..." : "Type your message..."}
          />
        </div>
      </main>
    </div>
  );
}

export default App;