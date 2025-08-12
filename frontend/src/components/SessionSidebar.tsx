import { useState, useEffect } from 'react';
import './SessionSidebar.css';
import type { Session } from '../services/api';

interface SessionSidebarProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  sessions: Session[];
  onRefresh: () => void;
  onDeleteSession: (sessionId: string) => void;
}

export function SessionSidebar({
  currentSessionId,
  onSessionSelect,
  onNewChat,
  sessions,
  onRefresh,
  onDeleteSession
}: SessionSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours === 0) {
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        if (diffMinutes === 0) return 'Just now';
        return `${diffMinutes}m ago`;
      }
      return `${diffHours}h ago`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
    } else {
      const months = Math.floor(diffDays / 30);
      return `${months} month${months > 1 ? 's' : ''} ago`;
    }
  };

  const groupSessionsByDate = (sessions: Session[]) => {
    const groups: { [key: string]: Session[] } = {
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      'Older': []
    };

    const now = new Date();
    
    sessions.forEach(session => {
      const date = new Date(session.created_at);
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) {
        groups['Today'].push(session);
      } else if (diffDays === 1) {
        groups['Yesterday'].push(session);
      } else if (diffDays < 7) {
        groups['Previous 7 Days'].push(session);
      } else if (diffDays < 30) {
        groups['Previous 30 Days'].push(session);
      } else {
        groups['Older'].push(session);
      }
    });

    return Object.entries(groups).filter(([_, sessions]) => sessions.length > 0);
  };

  const groupedSessions = groupSessionsByDate(sessions);

  return (
    <div className={`session-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="new-chat-button" onClick={onNewChat}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          {!isCollapsed && <span>New Chat</span>}
        </button>
        <button 
          className="toggle-sidebar-button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            {isCollapsed ? (
              <path d="M10 4L14 8L10 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            ) : (
              <path d="M6 4L2 8L6 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            )}
          </svg>
        </button>
      </div>

      {!isCollapsed && (
        <div className="sessions-list">
          {groupedSessions.length === 0 ? (
            <div className="no-sessions">
              <p>No conversations yet</p>
              <p className="hint">Start a new chat to begin</p>
            </div>
          ) : (
            groupedSessions.map(([groupName, groupSessions]) => (
              <div key={groupName} className="session-group">
                <div className="group-header">{groupName}</div>
                {groupSessions.map(session => (
                  <div
                    key={session.id}
                    className={`session-item-container ${session.id === currentSessionId ? 'active' : ''}`}
                    onMouseEnter={() => setHoveredSessionId(session.id)}
                    onMouseLeave={() => {
                      setHoveredSessionId(null);
                      if (confirmDelete === session.id) {
                        setConfirmDelete(null);
                      }
                    }}
                  >
                    <button
                      className="session-item"
                      onClick={() => onSessionSelect(session.id)}
                    >
                      <div className="session-title">
                        {session.title || 'New Chat'}
                      </div>
                      <div className="session-time">
                        {formatDate(session.created_at)}
                      </div>
                    </button>
                    {(hoveredSessionId === session.id || confirmDelete === session.id) && session.id !== currentSessionId && (
                      <button
                        className={`delete-button ${confirmDelete === session.id ? 'confirm' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirmDelete === session.id) {
                            onDeleteSession(session.id);
                            setConfirmDelete(null);
                          } else {
                            setConfirmDelete(session.id);
                          }
                        }}
                        title={confirmDelete === session.id ? "Click again to confirm delete" : "Delete session"}
                      >
                        {confirmDelete === session.id ? (
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M5 8L7 10L11 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        ) : (
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M6 3V2C6 1.44772 6.44772 1 7 1H9C9.55228 1 10 1.44772 10 2V3M2 3H14M3 3V13C3 14.1046 3.89543 15 5 15H11C12.1046 15 13 14.1046 13 13V3M5 7V11M8 7V11M11 7V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        )}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ))
          )}
        </div>
      )}

      {!isCollapsed && (
        <div className="sidebar-footer">
          <button className="refresh-button" onClick={onRefresh} title="Refresh sessions">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M14 8C14 11.3137 11.3137 14 8 14C5.5 14 3.5 12.5 2.5 10.5M2 8C2 4.68629 4.68629 2 8 2C10.5 2 12.5 3.5 13.5 5.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M14 5.5H10.5V2M2 10.5H5.5V14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}