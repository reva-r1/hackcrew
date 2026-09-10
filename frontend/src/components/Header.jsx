import React from 'react';
import { Sun, Moon, Database, MessageSquare, Upload, Home, Trash2, ArrowLeft } from 'lucide-react';

export default function Header({ 
  currentView, 
  setCurrentView, 
  theme, 
  setTheme, 
  totalChunks,
  onClearAll 
}) {
  const isDark = theme === 'theme-dark-red';

  return (
    <header className="panel" style={{
      margin: '16px 24px',
      padding: '12px 20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: '16px',
      zIndex: 100
    }}>
      {/* Brand */}
      <div 
        onClick={() => setCurrentView('landing')}
        style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
      >
        <div style={{
          width: '28px',
          height: '28px',
          borderRadius: '6px',
          background: 'var(--primary)',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: '700',
          fontSize: '0.9rem'
        }}>
          Æ
        </div>
        <div>
          <span style={{ fontWeight: '600', fontSize: '1.05rem', letterSpacing: '-0.01em' }}>
            Aether
          </span>
        </div>
      </div>

      {/* Navigation Pills (Only shown after landing page) */}
      {currentView !== 'landing' && (
        <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setCurrentView('landing')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: '500',
              background: 'transparent',
              color: 'var(--text-secondary)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text-primary)'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
          >
            <Home size={14} />
            <span>Home</span>
          </button>

          <button
            onClick={() => setCurrentView('upload')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: '500',
              background: currentView === 'upload' ? 'var(--primary)' : 'transparent',
              color: currentView === 'upload' ? '#ffffff' : 'var(--text-secondary)'
            }}
          >
            <Upload size={14} />
            <span>Upload</span>
          </button>

          <button
            onClick={() => setCurrentView('audit')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: '500',
              background: currentView === 'audit' ? 'var(--primary)' : 'transparent',
              color: currentView === 'audit' ? '#ffffff' : 'var(--text-secondary)'
            }}
          >
            <Database size={14} />
            <span>Audit Log</span>
            {totalChunks > 0 && (
              <span style={{
                fontSize: '0.7rem',
                padding: '1px 6px',
                borderRadius: '6px',
                background: currentView === 'audit' ? 'rgba(255,255,255,0.25)' : 'var(--badge-bg)',
                color: currentView === 'audit' ? '#ffffff' : 'var(--primary)',
                fontWeight: '600'
              }}>
                {totalChunks}
              </span>
            )}
          </button>

          <button
            onClick={() => setCurrentView('chat')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 16px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: '500',
              background: currentView === 'chat' ? 'var(--primary)' : 'transparent',
              color: currentView === 'chat' ? '#ffffff' : 'var(--primary)',
              border: currentView === 'chat' ? 'none' : '1px solid var(--border-active)'
            }}
          >
            <MessageSquare size={14} />
            <span>Chat</span>
          </button>
        </nav>
      )}

      {/* Right Tools: Theme & Clear */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button
          onClick={() => setTheme(isDark ? 'theme-light-red' : 'theme-dark-red')}
          title={isDark ? "Switch to light theme" : "Switch to dark theme"}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '8px',
            background: 'var(--bg-input)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-primary)',
            fontSize: '0.8rem',
            fontWeight: '500'
          }}
        >
          {isDark ? <Sun size={14} color="#e02840" /> : <Moon size={14} color="#c41a2e" />}
          <span>{isDark ? 'Light' : 'Dark'}</span>
        </button>

        <button
          onClick={onClearAll}
          title="Clear uploaded documents and start over"
          style={{
            padding: '6px 10px',
            borderRadius: '8px',
            background: 'transparent',
            color: 'var(--text-muted)'
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = 'var(--primary)'}
          onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
        >
          <Trash2 size={15} />
        </button>
      </div>
    </header>
  );
}
