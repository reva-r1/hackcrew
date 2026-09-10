import React from 'react';
import { ArrowRight, BookOpen, CheckCircle, Shield } from 'lucide-react';

export default function LandingPage({ onGetStarted }) {
  return (
    <div style={{
      maxWidth: '960px',
      margin: '0 auto',
      padding: '60px 24px 100px',
      textAlign: 'center'
    }}>
      {/* Subtle intro badge */}
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
        <span style={{
          fontSize: '0.82rem',
          fontWeight: '600',
          padding: '6px 14px',
          borderRadius: '20px',
          background: 'var(--badge-bg)',
          color: 'var(--primary)',
          border: '1px solid var(--badge-border)'
        }}>
          Reliable & Document-Verified
        </span>
      </div>

      {/* Main Editorial Headline */}
      <h1 style={{
        fontSize: '3.6rem',
        lineHeight: '1.15',
        marginBottom: '20px',
        fontWeight: '400'
      }}>
        Read your policies and documents with <span style={{ fontStyle: 'italic', color: 'var(--primary)' }}>complete clarity.</span>
      </h1>

      {/* Natural, humanized explanation */}
      <p style={{
        fontSize: '1.15rem',
        color: 'var(--text-secondary)',
        lineHeight: '1.7',
        maxWidth: '680px',
        margin: '0 auto 40px'
      }}>
        Search and understand company handbooks, benefits policies, contracts, and notes in plain English. 
        Get direct answers with page citations — and honest notifications when a question is outside your documents.
      </p>

      {/* Single, prominent Get Started button */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '72px' }}>
        <button
          onClick={onGetStarted}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '10px',
            padding: '16px 36px',
            borderRadius: '10px',
            background: 'var(--primary)',
            color: '#ffffff',
            fontSize: '1rem',
            fontWeight: '600',
            boxShadow: '0 4px 14px var(--primary-glow)'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'var(--primary-hover)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'var(--primary)'}
        >
          <span>Get Started — Upload Documents</span>
          <ArrowRight size={18} />
        </button>
      </div>

      {/* 3 Humanized Principle Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '20px',
        textAlign: 'left'
      }}>
        <div className="panel" style={{ padding: '28px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'var(--primary-subtle)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px'
          }}>
            <BookOpen size={20} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', fontWeight: '500' }}>
            Any document format
          </h3>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
            Drop in PDF handbooks, spreadsheets, scanned pages, or plain notes. The text is neatly read and organized so you can start asking questions.
          </p>
        </div>

        <div className="panel" style={{ padding: '28px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'var(--primary-subtle)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px'
          }}>
            <CheckCircle size={20} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', fontWeight: '500' }}>
            Exact page citations
          </h3>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
            Every answer links directly to the specific page and document it came from, making it effortless to cross-check and verify.
          </p>
        </div>

        <div className="panel" style={{ padding: '28px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'var(--primary-subtle)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px'
          }}>
            <Shield size={20} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', fontWeight: '500' }}>
            No guessing or inventing
          </h3>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
            If your uploaded documents don't mention a topic, you'll be told clearly instead of receiving a fabricated or hallucinated reply.
          </p>
        </div>
      </div>
    </div>
  );
}
