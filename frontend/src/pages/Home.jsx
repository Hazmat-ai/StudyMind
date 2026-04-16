import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

/* ── Feature badge ────────────────────────────────────── */
function FeatureBadge({ icon, label, delay }) {
  return (
    <div className="feature-badge animate-fade-up" style={{ animationDelay: delay }}>
      {icon}
      {label}
    </div>
  );
}

/* ── Generation progress bar ─────────────────────────── */
const PHASES = [
  { label: 'Reading your content…',         pct: 15 },
  { label: 'Identifying key concepts…',     pct: 35 },
  { label: 'Crafting flashcards…',          pct: 55 },
  { label: 'Writing practice questions…',   pct: 75 },
  { label: 'Finalising your study set…',    pct: 90 },
];

function ProgressBar({ phase }) {
  const { label, pct } = PHASES[Math.min(phase, PHASES.length - 1)];
  return (
    <div className="w-full mt-10 animate-fade-up" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem' }}>
        <span className="text-secondary flex items-center gap-2">
          <span className="w-3 h-3 rounded-full inline-block" style={{
            border: '2px solid var(--c-border)',
            borderTopColor: '#7c3aed',
            animation: 'spin 1s linear infinite',
          }} />
          {label}
        </span>
        <span className="text-hint" style={{ fontVariantNumeric: 'tabular-nums' }}>{pct}%</span>
      </div>
      <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--c-bg-muted)', borderRadius: '9999px', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          background: 'linear-gradient(to right, #7c3aed, #a855f7)',
          borderRadius: '9999px',
          transition: 'width 0.7s ease-out',
        }} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1.5rem' }}>
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="card" style={{
            height: '9rem',
            animationDelay: `${i * 0.15}s`,
            animation: 'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite',
          }} />
        ))}
      </div>
    </div>
  );
}

/* ── Home page ───────────────────────────────────────── */
export default function Home() {
  const [content, setContent]           = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUploading, setIsUploading]   = useState(false);
  const [phaseIdx, setPhaseIdx]         = useState(0);
  const [errorDesc, setErrorDesc]       = useState('');
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [isMounted, setIsMounted]       = useState(false);
  const fileInputRef = useRef(null);
  const phaseTimer   = useRef(null);
  const navigate     = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => setIsMounted(true), 50);
    return () => clearTimeout(t);
  }, []);

  const startPhaseTimer = () => {
    setPhaseIdx(0);
    let idx = 0;
    phaseTimer.current = setInterval(() => {
      idx = Math.min(idx + 1, PHASES.length - 1);
      setPhaseIdx(idx);
      if (idx === PHASES.length - 1) clearInterval(phaseTimer.current);
    }, 1200);
  };

  const stopPhaseTimer = () => {
    clearInterval(phaseTimer.current);
    setPhaseIdx(0);
  };

  const runGenerate = async (textContent) => {
    setIsGenerating(true);
    setErrorDesc('');
    startPhaseTimer();
    try {
      const result = await api.generateStudySet(textContent, {
        num_flashcards: 8,
        num_questions: 5,
        difficulty: 'intermediate',
      });
      stopPhaseTimer();
      navigate('/results/generated', { state: { studySet: result } });
    } catch (err) {
      stopPhaseTimer();
      const detail = err.response?.data?.detail;
      setErrorDesc(
        typeof detail === 'string' ? detail :
        detail ? JSON.stringify(detail) :
        err.message || 'Failed to generate study set'
      );
      setIsGenerating(false);
    }
  };

  const handleGenerate = () => { if (content.trim()) runGenerate(content); };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.type !== 'application/pdf') {
      setErrorDesc('Please upload a valid PDF file.');
      return;
    }
    setIsUploading(true);
    setUploadedFileName(file.name);
    setErrorDesc('');
    try {
      const data = await api.extractPdfText(file);
      const extracted = data.content;
      setContent(extracted);
      setIsUploading(false);
      await runGenerate(extracted);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorDesc(
        typeof detail === 'string' ? detail :
        detail ? JSON.stringify(detail) :
        'Failed to extract text from PDF'
      );
      setUploadedFileName('');
      setIsUploading(false);
    } finally {
      e.target.value = null;
    }
  };

  const isWorking   = isGenerating || isUploading;
  const canGenerate = !!content.trim() && !isWorking;

  const uploadLabel = isUploading ? 'Extracting PDF…'
    : (isGenerating && uploadedFileName) ? `From: ${uploadedFileName}`
    : uploadedFileName || 'Upload PDF';

  const icons = {
    flashcard: <svg className="w-3 h-3" style={{ color: '#7c3aed' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>,
    summary:   <svg className="w-3 h-3" style={{ color: '#a855f7' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>,
    practice:  <svg className="w-3 h-3" style={{ color: '#10b981' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>,
    bolt:      <svg className="w-3 h-3" style={{ color: '#3b82f6' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>,
  };

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      maxWidth: '42rem', margin: '2rem auto 0',
      opacity: isMounted ? 1 : 0,
      transform: isMounted ? 'translateY(0)' : 'translateY(24px)',
      transition: 'opacity 0.6s ease, transform 0.6s ease',
    }}>

      {/* Feature badges */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center', marginBottom: '2rem' }}>
        <FeatureBadge delay="0.1s"  icon={icons.flashcard} label="AI Flashcards" />
        <FeatureBadge delay="0.15s" icon={icons.summary}   label="Smart Summaries" />
        <FeatureBadge delay="0.2s"  icon={icons.practice}  label="Practice Questions" />
        <FeatureBadge delay="0.25s" icon={icons.bolt}      label="Auto-Generate from PDF" />
      </div>

      {/* Headline */}
      <h1 className="animate-fade-up" style={{
        fontSize: 'clamp(2.5rem, 6vw, 3.5rem)',
        fontWeight: 800,
        textAlign: 'center',
        lineHeight: 1.15,
        letterSpacing: '-0.02em',
        color: 'var(--c-text)',
        marginBottom: '1rem',
        animationDelay: '0.05s',
      }}>
        Learn faster with{' '}
        <span style={{ background: 'linear-gradient(135deg, #7c3aed, #a855f7, #6d28d9)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          StudyMind
        </span>
      </h1>
      <p className="animate-fade-up" style={{
        color: 'var(--c-text-muted)',
        fontSize: '1.1rem',
        textAlign: 'center',
        lineHeight: 1.7,
        marginBottom: '2.5rem',
        animationDelay: '0.15s',
      }}>
        Upload a PDF or paste your notes — we'll instantly generate<br />
        flashcards, summaries &amp; practice questions.
      </p>

      {/* Error banner */}
      {errorDesc && (
        <div className="error-box animate-fade-up w-full" style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
          <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <span>{errorDesc}</span>
        </div>
      )}

      {/* Input card */}
      <div className="card glow-card animate-fade-up w-full" style={{ padding: '0.5rem', animationDelay: '0.25s', position: 'relative', overflow: 'hidden' }}>
        {/* Hover shimmer */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '1rem', pointerEvents: 'none',
          background: 'radial-gradient(ellipse at top, rgba(124,58,237,0.04) 0%, transparent 60%)',
        }} />

        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') handleGenerate(); }}
          placeholder={
            isUploading ? 'Extracting text from PDF…'
            : isGenerating ? 'Generating your study set…'
            : 'Paste your lecture notes here… (⌘+Enter to generate)'
          }
          disabled={isWorking}
          style={{
            width: '100%',
            height: '16rem',
            backgroundColor: 'transparent',
            color: 'var(--c-text)',
            resize: 'none',
            padding: '1.25rem',
            borderRadius: '0.75rem',
            fontSize: '1rem',
            lineHeight: 1.7,
            outline: 'none',
            fontFamily: 'inherit',
          }}
          className="placeholder-style"
        />
        <style>{`textarea::placeholder { color: var(--c-text-hint); }`}</style>

        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0.75rem 1rem',
          borderTop: '1px solid var(--c-border)',
        }}>
          {/* Upload */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".pdf" className="hidden" />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isWorking}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                fontSize: '0.875rem',
                color: 'var(--c-text-muted)',
                background: 'none', border: 'none', cursor: isWorking ? 'not-allowed' : 'pointer',
                opacity: isWorking ? 0.5 : 1,
                transition: 'color 0.2s',
              }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--c-violet)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--c-text-muted)'}
            >
              {isUploading
                ? <span style={{ width: '1rem', height: '1rem', borderRadius: '50%', border: '2px solid var(--c-border)', borderTopColor: '#7c3aed', animation: 'spin 1s linear infinite', display: 'inline-block' }} />
                : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
              }
              <span style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {uploadLabel}
              </span>
            </button>
            {content.length > 0 && (
              <span style={{ fontSize: '0.75rem', color: 'var(--c-text-hint)', fontVariantNumeric: 'tabular-nums' }}>
                {content.length.toLocaleString()} chars
              </span>
            )}
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={!canGenerate}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.625rem 1.5rem',
              borderRadius: '0.75rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              border: 'none',
              cursor: canGenerate ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease',
              background: canGenerate
                ? 'linear-gradient(135deg, #7c3aed, #a855f7)'
                : 'var(--c-bg-muted)',
              color: canGenerate ? '#ffffff' : 'var(--c-text-hint)',
              boxShadow: canGenerate ? '0 4px 14px rgba(124,58,237,0.35)' : 'none',
              transform: 'scale(1)',
            }}
            onMouseEnter={e => { if (canGenerate) e.currentTarget.style.boxShadow = '0 6px 20px rgba(124,58,237,0.5)'; }}
            onMouseLeave={e => { if (canGenerate) e.currentTarget.style.boxShadow = '0 4px 14px rgba(124,58,237,0.35)'; }}
          >
            {isGenerating
              ? <>
                  <span style={{ width: '1rem', height: '1rem', borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 1s linear infinite', display: 'inline-block' }} />
                  Generating…
                </>
              : <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                  Generate Study Set
                </>
            }
          </button>
        </div>
      </div>

      {/* Progress */}
      {isWorking && <ProgressBar phase={phaseIdx} />}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
