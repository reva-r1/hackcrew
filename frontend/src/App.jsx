import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LandingPage from './components/LandingPage';
import UploadPage from './components/UploadPage';
import AuditLogPage from './components/AuditLogPage';
import ChatPage from './components/ChatPage';

export default function App() {
  // Theme state: 'theme-dark-red' (Black + Red) or 'theme-light-red' (White + Red)
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('aether-theme') || 'theme-dark-red';
  });

  // Current view: 'landing' (default) -> 'upload' -> choice: 'audit' or 'chat'
  const [currentView, setCurrentView] = useState('landing');
  
  // Knowledge base state
  const [totalChunks, setTotalChunks] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  useEffect(() => {
    localStorage.setItem('aether-theme', theme);
    document.body.className = theme;
  }, [theme]);

  const loadMetadata = async () => {
    try {
      const [chunksRes, filesRes] = await Promise.all([
        fetch('/chunks'),
        fetch('/uploaded-files')
      ]);

      if (chunksRes.ok) {
        const cData = await chunksRes.json();
        setTotalChunks(cData.total_chunks || 0);
      }
      if (filesRes.ok) {
        const fData = await filesRes.json();
        setUploadedFiles(fData.files || []);
      }
    } catch (e) {
      console.warn('Failed to load initial metadata:', e);
    }
  };

  useEffect(() => {
    loadMetadata();
  }, [currentView]);

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to purge all uploaded documents and indices?')) {
      return;
    }
    try {
      const res = await fetch('/clear-all', { method: 'POST' });
      if (res.ok) {
        setTotalChunks(0);
        setUploadedFiles([]);
        setCurrentView('upload');
      }
    } catch (e) {
      alert('Failed to clear data');
    }
  };

  return (
    <div className={`app-root ${theme}`} style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navigation & Header */}
      <Header
        currentView={currentView}
        setCurrentView={setCurrentView}
        theme={theme}
        setTheme={setTheme}
        totalChunks={totalChunks}
        onClearAll={handleClearAll}
      />

      {/* Main View Router */}
      <main style={{ flex: 1 }}>
        {currentView === 'landing' && (
          <LandingPage
            onGetStarted={() => setCurrentView('upload')}
          />
        )}

        {currentView === 'upload' && (
          <UploadPage
            onGoToLanding={() => setCurrentView('landing')}
            onGoToAudit={() => setCurrentView('audit')}
            onGoToChat={() => setCurrentView('chat')}
            onUploadSuccess={loadMetadata}
            uploadedFiles={uploadedFiles}
          />
        )}

        {currentView === 'audit' && (
          <AuditLogPage
            onGoToChat={() => setCurrentView('chat')}
            onGoToUpload={() => setCurrentView('upload')}
          />
        )}

        {currentView === 'chat' && (
          <ChatPage
            onGoToUpload={() => setCurrentView('upload')}
            onGoToAudit={() => setCurrentView('audit')}
            onGoToLanding={() => setCurrentView('landing')}
          />
        )}
      </main>
    </div>
  );
}
