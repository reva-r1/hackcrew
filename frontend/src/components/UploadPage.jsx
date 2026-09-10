import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle, AlertCircle, Loader2, Database, MessageSquare, ArrowRight, ArrowLeft } from 'lucide-react';

export default function UploadPage({ onGoToLanding, onGoToAudit, onGoToChat, onUploadSuccess, uploadedFiles }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file) => {
    setErrorMsg('');
    setUploadResult(null);
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'failed') {
        throw new Error(data.error || 'Failed to read document');
      }

      setUploadResult({
        docName: data.doc_name || file.name,
        chunksCreated: data.chunks_created || 0,
        confidence: data.confidence !== undefined ? Math.round(data.confidence * 100) : 100,
        preview: data.preview_text || ''
      });

      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (err) {
      console.error('Upload failed:', err);
      setErrorMsg(err.message || 'Something went wrong while reading this file');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{
      maxWidth: '820px',
      margin: '0 auto',
      padding: '30px 24px 80px'
    }}>
      {/* Back button */}
      <div style={{ marginBottom: '24px' }}>
        <button
          onClick={onGoToLanding}
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
          onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text-primary)'}
          onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
        >
          <ArrowLeft size={15} />
          <span>Back to Home</span>
        </button>
      </div>

      {/* Title */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 style={{ fontSize: '2.4rem', fontWeight: '400', marginBottom: '8px' }}>
          Add your document
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '540px', margin: '0 auto' }}>
          Upload a company policy, handbook, spreadsheet, or scan. We'll read the text so you can ask questions immediately.
        </p>
      </div>

      {/* Upload Box */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current && fileInputRef.current.click()}
        className="panel"
        style={{
          padding: '48px 24px',
          textAlign: 'center',
          border: isDragging ? '2px dashed var(--primary)' : '1px dashed var(--border-active)',
          background: isDragging ? 'var(--primary-subtle)' : 'var(--bg-card)',
          cursor: isUploading ? 'not-allowed' : 'pointer',
          marginBottom: '28px'
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".pdf,.txt,.csv,.png,.jpg,.jpeg,.webp,.docx"
          style={{ display: 'none' }}
        />

        {isUploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
            <Loader2 size={36} color="var(--primary)" style={{ animation: 'spin 1s linear infinite' }} />
            <div>
              <div style={{ fontWeight: '600', fontSize: '1.05rem', marginBottom: '2px' }}>
                Reading and organizing your document...
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Extracting text, sections, and tables
              </div>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '10px',
              background: 'var(--primary-subtle)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <UploadCloud size={24} />
            </div>

            <div>
              <div style={{ fontWeight: '600', fontSize: '1.05rem', marginBottom: '4px' }}>
                Drop your file here, or <span style={{ color: 'var(--primary)', textDecoration: 'underline' }}>browse</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                PDF, Text (.txt), Excel / CSV, Word (.docx), or photos (PNG, JPG)
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '14px 18px',
          borderRadius: '8px',
          background: 'var(--safeguard-bg)',
          border: '1px solid var(--safeguard-border)',
          color: 'var(--primary)',
          marginBottom: '24px'
        }}>
          <AlertCircle size={18} />
          <div style={{ fontSize: '0.88rem' }}>{errorMsg}</div>
        </div>
      )}

      {/* Success & Two Decision Buttons */}
      {uploadResult && (
        <div className="panel" style={{
          padding: '28px',
          marginBottom: '32px',
          background: 'var(--bg-card)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'var(--primary-subtle)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <CheckCircle size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.35rem', fontWeight: '500', marginBottom: '2px' }}>
                Document ready!
              </h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                <strong>{uploadResult.docName}</strong> was read successfully ({uploadResult.chunksCreated} sections indexed).
              </p>
            </div>
          </div>

          {/* Choice: View Document Breakdown vs Start Chat */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '12px'
          }}>
            <button
              onClick={onGoToAudit}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '14px',
                borderRadius: '8px',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-active)',
                color: 'var(--text-primary)',
                fontSize: '0.92rem',
                fontWeight: '600'
              }}
            >
              <Database size={16} color="var(--primary)" />
              <span>View Document Breakdown</span>
            </button>

            <button
              onClick={onGoToChat}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '14px',
                borderRadius: '8px',
                background: 'var(--primary)',
                color: '#ffffff',
                fontSize: '0.92rem',
                fontWeight: '600',
                boxShadow: '0 4px 12px var(--primary-glow)'
              }}
            >
              <MessageSquare size={16} />
              <span>Start Chatting</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </div>
      )}

      {/* Document List */}
      {uploadedFiles && uploadedFiles.length > 0 && (
        <div style={{ marginTop: '32px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '14px'
          }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-primary)' }}>
              Active Documents ({uploadedFiles.length})
            </h4>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Ready for questions
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {uploadedFiles.map((file, idx) => (
              <div
                key={idx}
                className="panel"
                style={{
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <FileText size={16} color="var(--primary)" />
                  <div>
                    <div style={{ fontSize: '0.88rem', fontWeight: '500' }}>{file.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {file.size_kb} KB
                    </div>
                  </div>
                </div>

                <button
                  onClick={onGoToChat}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '6px',
                    background: 'var(--primary-subtle)',
                    color: 'var(--primary)',
                    fontSize: '0.8rem',
                    fontWeight: '600'
                  }}
                >
                  Ask Questions
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
