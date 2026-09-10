import React, { useState, useEffect } from 'react';
import { FileText, Database, MessageSquare, ArrowLeft, ArrowRight, RefreshCw, Search, ChevronDown, ChevronUp } from 'lucide-react';

export default function AuditLogPage({ onGoToChat, onGoToUpload }) {
  const [activeTab, setActiveTab] = useState('chunks'); // 'chunks' | 'logs' | 'files'
  const [chunksData, setChunksData] = useState({ total_chunks: 0, total_words: 0, chunks: [] });
  const [logsData, setLogsData] = useState([]);
  const [filesData, setFilesData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedChunkId, setExpandedChunkId] = useState(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [chunksRes, logsRes, filesRes] = await Promise.all([
        fetch('/chunks'),
        fetch('/logs'),
        fetch('/uploaded-files')
      ]);

      if (chunksRes.ok) {
        const cData = await chunksRes.json();
        setChunksData(cData);
      }
      if (logsRes.ok) {
        const lData = await logsRes.json();
        setLogsData(lData.logs || []);
      }
      if (filesRes.ok) {
        const fData = await filesRes.json();
        setFilesData(fData.files || []);
      }
    } catch (err) {
      console.error('Failed to load document breakdown:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredChunks = chunksData.chunks.filter(c => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.doc_name && c.doc_name.toLowerCase().includes(q)) ||
      (c.full_text && c.full_text.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{
      maxWidth: '980px',
      margin: '0 auto',
      padding: '30px 24px 80px'
    }}>
      {/* Top Navigation */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        marginBottom: '28px'
      }}>
        <button
          onClick={onGoToUpload}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            borderRadius: '8px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            fontSize: '0.85rem',
            fontWeight: '500'
          }}
        >
          <ArrowLeft size={15} />
          <span>Back to Upload</span>
        </button>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={fetchData}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)',
              fontSize: '0.85rem'
            }}
          >
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>

          <button
            onClick={onGoToChat}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 18px',
              borderRadius: '8px',
              background: 'var(--primary)',
              color: '#ffffff',
              fontSize: '0.88rem',
              fontWeight: '600'
            }}
          >
            <span>Start Chatting</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>

      {/* Title */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '2.4rem', fontWeight: '400', marginBottom: '6px' }}>
          Document Breakdown
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
          Here is how your documents were read, organized into sections, and prepared for questions.
        </p>
      </div>

      {/* Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        marginBottom: '24px'
      }}>
        <div className="panel" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Documents</div>
          <div style={{ fontSize: '1.8rem', fontWeight: '600', color: 'var(--primary)', marginTop: '2px' }}>
            {filesData.length}
          </div>
        </div>

        <div className="panel" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Sections & Passages</div>
          <div style={{ fontSize: '1.8rem', fontWeight: '600', marginTop: '2px' }}>
            {chunksData.total_chunks}
          </div>
        </div>

        <div className="panel" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Words</div>
          <div style={{ fontSize: '1.8rem', fontWeight: '600', marginTop: '2px' }}>
            {chunksData.total_words ? chunksData.total_words.toLocaleString() : 0}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '10px',
        marginBottom: '16px',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={() => setActiveTab('chunks')}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: '500',
              background: activeTab === 'chunks' ? 'var(--primary)' : 'transparent',
              color: activeTab === 'chunks' ? '#fff' : 'var(--text-secondary)'
            }}
          >
            Passages ({chunksData.total_chunks})
          </button>

          <button
            onClick={() => setActiveTab('logs')}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: '500',
              background: activeTab === 'logs' ? 'var(--primary)' : 'transparent',
              color: activeTab === 'logs' ? '#fff' : 'var(--text-secondary)'
            }}
          >
            Activity Log ({logsData.length})
          </button>

          <button
            onClick={() => setActiveTab('files')}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: '500',
              background: activeTab === 'files' ? 'var(--primary)' : 'transparent',
              color: activeTab === 'files' ? '#fff' : 'var(--text-secondary)'
            }}
          >
            Files ({filesData.length})
          </button>
        </div>

        {activeTab === 'chunks' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'var(--bg-input)',
            padding: '6px 12px',
            borderRadius: '6px',
            border: '1px solid var(--border-subtle)',
            width: '240px'
          }}>
            <Search size={14} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search passages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontSize: '0.82rem',
                width: '100%'
              }}
            />
          </div>
        )}
      </div>

      {/* Tab 1: Passages */}
      {activeTab === 'chunks' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {filteredChunks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              No passages found.
            </div>
          ) : (
            filteredChunks.map((chunk) => {
              const isExpanded = expandedChunkId === chunk.chunk_id;
              return (
                <div
                  key={chunk.chunk_id}
                  className="panel"
                  style={{ padding: '16px 20px' }}
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '8px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={15} color="var(--primary)" />
                      <span style={{ fontWeight: '600', fontSize: '0.9rem' }}>
                        {chunk.doc_name}
                      </span>
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        background: 'var(--badge-bg)',
                        color: 'var(--primary)'
                      }}>
                        Page {chunk.page_num}
                      </span>
                    </div>

                    <button
                      onClick={() => setExpandedChunkId(isExpanded ? null : chunk.chunk_id)}
                      style={{
                        background: 'transparent',
                        color: 'var(--primary)',
                        fontSize: '0.8rem',
                        fontWeight: '500',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '2px'
                      }}
                    >
                      <span>{isExpanded ? 'Show less' : 'Read full'}</span>
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </div>

                  <p style={{
                    fontSize: '0.88rem',
                    color: 'var(--text-secondary)',
                    lineHeight: '1.6',
                    whiteSpace: isExpanded ? 'pre-wrap' : 'normal'
                  }}>
                    {isExpanded ? chunk.full_text : chunk.preview}
                  </p>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Tab 2: Activity Logs */}
      {activeTab === 'logs' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {logsData.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              No activity recorded yet.
            </div>
          ) : (
            logsData.map((log) => (
              <div
                key={log.id}
                className="panel"
                style={{
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px'
                }}
              >
                <span style={{
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  marginTop: '1px'
                }}>
                  {log.timestamp}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.88rem', fontWeight: '600' }}>{log.title}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{log.detail}</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 3: Files */}
      {activeTab === 'files' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {filesData.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              No files uploaded yet.
            </div>
          ) : (
            filesData.map((file, idx) => (
              <div
                key={idx}
                className="panel"
                style={{
                  padding: '14px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <FileText size={16} color="var(--primary)" />
                  <div>
                    <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>{file.name}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{file.size_kb} KB</div>
                  </div>
                </div>

                <button
                  onClick={onGoToChat}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '6px',
                    background: 'var(--primary-subtle)',
                    color: 'var(--primary)',
                    fontSize: '0.82rem',
                    fontWeight: '600'
                  }}
                >
                  Ask about this file
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
