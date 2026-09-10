import React, { useState, useEffect, useRef } from 'react';
import { Send, FileText, ArrowUp, ArrowLeft, Database, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';

export default function ChatPage({ onGoToUpload, onGoToAudit }) {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [previewScore, setPreviewScore] = useState(0);
  const [previewStatus, setPreviewStatus] = useState('no_match');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!inputQuery || inputQuery.trim().length < 2) {
      setPreviewScore(0);
      setPreviewStatus('no_match');
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const res = await fetch('/preview-confidence', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ partial_query: inputQuery })
        });
        if (res.ok) {
          const data = await res.json();
          setPreviewScore(Math.round(data.score || 0));
          setPreviewStatus(data.status || 'no_match');
        }
      } catch (e) {}
    }, 120);

    return () => clearTimeout(timer);
  }, [inputQuery]);

  const handleSend = async (queryText) => {
    const q = (queryText || inputQuery).trim();
    if (!q || isSending) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setPreviewScore(0);
    setIsSending(true);

    try {
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, role: 'employee' })
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();

      const botMsg = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        status: data.status, // 'answered' | 'refused' | 'error'
        text: data.answer || '',
        confidence: data.confidence !== null && data.confidence !== undefined ? Math.round(data.confidence * 100) : 0,
        sources: data.sources || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-err-${Date.now()}`,
          role: 'assistant',
          status: 'error',
          text: `Could not reach the assistant: ${err.message}`,
          sources: [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsSending(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    "Give me a summary of the document",
    "What is the policy on paid time off or leaves?",
    "What equipment or stipends are provided?",
    "What are the working hours and overtime rules?"
  ];

  return (
    <div style={{
      maxWidth: '860px',
      margin: '0 auto',
      padding: '16px 20px 40px',
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 110px)'
    }}>
      {/* Top Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingBottom: '12px',
        marginBottom: '12px',
        borderBottom: '1px solid var(--border-subtle)'
      }}>
        <button
          onClick={onGoToUpload}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '6px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            fontSize: '0.82rem',
            fontWeight: '500'
          }}
        >
          <ArrowLeft size={14} />
          <span>Back to Upload</span>
        </button>

        <button
          onClick={onGoToAudit}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '6px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            fontSize: '0.82rem',
            fontWeight: '500'
          }}
        >
          <Database size={14} color="var(--primary)" />
          <span>View Document Breakdown</span>
        </button>
      </div>

      {/* Messages Thread */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        paddingRight: '6px',
        marginBottom: '16px'
      }}>
        {messages.length === 0 ? (
          <div style={{
            margin: 'auto 0',
            textAlign: 'center',
            padding: '24px 16px'
          }}>
            <h3 style={{ fontSize: '2rem', fontWeight: '400', marginBottom: '8px' }}>
              Ask anything about your document
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '520px', margin: '0 auto 24px' }}>
              Questions are answered using only the verified content in your uploaded files. If a detail isn't in your document, we won't guess.
            </p>

            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '8px',
              justifyContent: 'center',
              maxWidth: '620px',
              margin: '0 auto'
            }}>
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(s)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '8px',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    fontSize: '0.85rem'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = 'var(--text-primary)';
                    e.currentTarget.style.borderColor = 'var(--border-active)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = 'var(--text-secondary)';
                    e.currentTarget.style.borderColor = 'var(--border-subtle)';
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                gap: '4px'
              }}
            >
              {msg.role === 'user' ? (
                <div style={{
                  maxWidth: '75%',
                  background: 'var(--primary)',
                  color: '#ffffff',
                  padding: '12px 18px',
                  borderRadius: '12px 12px 2px 12px',
                  fontSize: '0.95rem',
                  lineHeight: '1.5'
                }}>
                  {msg.text}
                </div>
              ) : (
                <div style={{ maxWidth: '92%', width: '100%' }}>
                  {msg.status === 'refused' ? (
                    <div className="panel" style={{
                      padding: '18px 22px',
                      background: 'var(--safeguard-bg)',
                      border: '1px solid var(--safeguard-border)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary)', fontWeight: '600', marginBottom: '6px', fontSize: '0.92rem' }}>
                        <AlertCircle size={16} />
                        <span>Not mentioned in your documents</span>
                      </div>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                        I couldn't find information about this in your uploaded files. To make sure you get accurate facts, I only answer questions that are explicitly covered in your documents.
                      </p>
                    </div>
                  ) : (
                    <div className="panel" style={{
                      padding: '20px 24px',
                      background: 'var(--bg-card)'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '12px'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <CheckCircle2 size={15} color="var(--primary)" />
                          <span style={{ fontSize: '0.82rem', fontWeight: '600', color: 'var(--primary)' }}>
                            Document Verified
                          </span>
                        </div>
                      </div>

                      <div style={{
                        fontSize: '0.96rem',
                        lineHeight: '1.7',
                        color: 'var(--text-primary)',
                        whiteSpace: 'pre-wrap',
                        marginBottom: msg.sources && msg.sources.length > 0 ? '16px' : '0'
                      }}>
                        {msg.text}
                      </div>

                      {msg.sources && msg.sources.length > 0 && (
                        <div style={{
                          borderTop: '1px solid var(--border-subtle)',
                          paddingTop: '12px',
                          marginTop: '12px'
                        }}>
                          <div style={{
                            fontSize: '0.75rem',
                            color: 'var(--text-muted)',
                            marginBottom: '6px',
                            fontWeight: '600'
                          }}>
                            Sources from your document:
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {msg.sources.map((src, i) => (
                              <div
                                key={i}
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '6px',
                                  padding: '4px 10px',
                                  borderRadius: '6px',
                                  background: 'var(--bg-surface)',
                                  border: '1px solid var(--border-subtle)',
                                  fontSize: '0.78rem',
                                  color: 'var(--text-secondary)'
                                }}
                              >
                                <FileText size={12} color="var(--primary)" />
                                <span>{src.doc_name}</span>
                                <span style={{ color: 'var(--primary)', fontWeight: '600' }}>
                                  Page {src.page_num}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}

        {isSending && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--primary)', display: 'inline-block' }} />
            <span>Reading your document to find the answer...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Typing Match Indicator */}
      {inputQuery.trim().length >= 2 && (
        <div style={{
          marginBottom: '6px',
          padding: '4px 10px',
          fontSize: '0.75rem',
          color: previewScore >= 40 ? 'var(--primary)' : 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: previewScore >= 40 ? 'var(--primary)' : 'var(--text-muted)'
          }} />
          <span>
            {previewScore >= 40 ? 'Matching text found in your files' : 'No direct matches found yet for this wording'}
          </span>
        </div>
      )}

      {/* Clean Input Bar */}
      <div className="panel" style={{
        padding: '6px 8px 6px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        background: 'var(--bg-card)'
      }}>
        <input
          ref={inputRef}
          type="text"
          placeholder="Ask a question about your files..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            fontSize: '0.95rem',
            color: 'var(--text-primary)',
            padding: '8px 0'
          }}
        />

        <button
          onClick={() => handleSend()}
          disabled={!inputQuery.trim() || isSending}
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: inputQuery.trim() && !isSending ? 'var(--primary)' : 'var(--bg-surface)',
            color: inputQuery.trim() && !isSending ? '#ffffff' : 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: inputQuery.trim() && !isSending ? 'pointer' : 'not-allowed'
          }}
        >
          <ArrowUp size={18} />
        </button>
      </div>
    </div>
  );
}
