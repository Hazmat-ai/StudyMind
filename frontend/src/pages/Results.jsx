import { useState, useEffect } from 'react';
import { useSearchParams, useParams, Link, useLocation, useNavigate } from 'react-router-dom';

/* ── FlashCard ─────────────────────────────────────── */
function FlashCard({ card, index }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <div
      onClick={() => setFlipped(f => !f)}
      className="animate-fade-up"
      style={{
        position: 'relative',
        height: '14rem',
        borderRadius: '1rem',
        cursor: 'pointer',
        perspective: '1000px',
        animationDelay: `${index * 0.08}s`,
      }}
    >
      {/* Rotating inner */}
      <div style={{
        position: 'relative', width: '100%', height: '100%',
        transformStyle: 'preserve-3d',
        transition: 'transform 0.55s cubic-bezier(0.4, 0, 0.2, 1)',
        transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
      }}>

        {/* Front */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundColor: 'var(--c-bg-card)',
          border: '1px solid var(--c-border)',
          borderRadius: '1rem',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          textAlign: 'center', padding: '1.5rem',
          backfaceVisibility: 'hidden',
          WebkitBackfaceVisibility: 'hidden',
          transition: 'border-color 0.2s, box-shadow 0.2s',
        }}>
          <p style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--c-text-hint)', marginBottom: '0.75rem' }}>
            Term · click to flip
          </p>
          <p style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--c-text)' }}>{card.term}</p>
        </div>

        {/* Back */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundColor: 'var(--c-violet-bg)',
          border: '1px solid var(--c-violet-border)',
          borderRadius: '1rem',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          textAlign: 'center', padding: '1.5rem',
          backfaceVisibility: 'hidden',
          WebkitBackfaceVisibility: 'hidden',
          transform: 'rotateY(180deg)',
        }}>
          <p style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--c-violet)', marginBottom: '0.75rem' }}>
            Definition
          </p>
          <p style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--c-text)', lineHeight: 1.6 }}>{card.definition}</p>
        </div>
      </div>
    </div>
  );
}

/* ── Reveal button ───────────────────────────────── */
function RevealButton({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="btn-ghost"
      style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        padding: '0.625rem 1.25rem',
        borderRadius: '0.75rem',
        fontSize: '0.875rem',
        fontWeight: 600,
        cursor: 'pointer',
      }}
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
      Reveal Answer
    </button>
  );
}

/* ── Results page ─────────────────────────────────── */
export default function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab  = searchParams.get('tab') || 'summary';
  const studySet   = location.state?.studySet || null;
  const [revealedQs, setRevealedQs] = useState({});
  const [isMounted, setIsMounted]   = useState(false);

  useEffect(() => {
    setRevealedQs({});
    setSearchParams({ tab: 'summary' }, { replace: true });
  }, [studySet]);

  useEffect(() => {
    const t = setTimeout(() => setIsMounted(true), 50);
    return () => clearTimeout(t);
  }, []);

  /* Data */
  const title      = studySet?.title || 'Introduction to Cell Biology';
  const summary    = studySet?.summary || 'Cells are the fundamental units of life. They provide structure, take in nutrients, and convert them into energy. All multicellular organisms depend on the coordinated action of specialised cells.';
  const flashcards = studySet?.flashcards || [
    { term: 'Mitochondria', definition: 'Powerhouse of the cell — generates most chemical energy (ATP) via cellular respiration.' },
    { term: 'Ribosomes',    definition: 'Molecular machines that synthesize proteins by translating mRNA sequences.' },
    { term: 'Nucleus',      definition: 'Control center of the cell, housing the genome and regulating gene expression.' },
    { term: 'Cell Membrane',definition: 'Selectively permeable lipid bilayer that controls passage of substances in and out of the cell.' },
  ];
  const practiceQs = studySet?.questions || [
    { question: 'What is the primary function of the cell membrane?', answer: "It acts as a selectively permeable barrier, controlling what enters and exits the cell while maintaining its internal environment." },
    { question: 'How do mitochondria produce energy?', answer: "Through cellular respiration — oxidising glucose via the Krebs cycle and oxidative phosphorylation to produce ATP." },
  ];
  const concepts   = studySet?.concepts || [
    { term: 'Eukaryotes', related: ['Nucleus', 'Membrane-bound organelles', 'Complex structure'] },
    { term: 'Prokaryotes', related: ['No nucleus', 'Simpler structure', 'Bacteria'] },
    { term: 'Organelles',  related: ['Mitochondria', 'Ribosomes', 'ER', 'Golgi'] },
    { term: 'Cell Theory', related: ['All life from cells', 'Basic unit of life', 'Heredity'] },
  ];

  const tabs = [
    { id: 'summary',    label: 'Summary',    d: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', count: null },
    { id: 'flashcards', label: 'Flashcards', d: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z', count: flashcards.length },
    { id: 'practice',   label: 'Practice',   d: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', count: practiceQs.length },
    { id: 'concepts',   label: 'Concepts',   d: 'M13 10V3L4 14h7v7l9-11h-7z', count: concepts.length },
  ];

  const setTab       = (t) => setSearchParams({ tab: t });
  const toggleReveal = (i) => setRevealedQs(p => ({ ...p, [i]: !p[i] }));

  const iconBox = (bg, icon) => (
    <div style={{
      width: '2rem', height: '2rem', borderRadius: '0.5rem',
      backgroundColor: bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      {icon}
    </div>
  );

  return (
    <div style={{
      width: '100%',
      opacity: isMounted ? 1 : 0,
      transform: isMounted ? 'translateY(0)' : 'translateY(16px)',
      transition: 'opacity 0.6s ease, transform 0.6s ease',
    }}>

      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
        <Link to="/" style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
          fontSize: '0.875rem', fontWeight: 500,
          color: 'var(--c-text-muted)',
          textDecoration: 'none',
          transition: 'color 0.2s',
        }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--c-violet)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--c-text-muted)'}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Back to Generator
        </Link>
        <button
          onClick={() => navigate('/')}
          className="btn-violet-ghost"
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.5rem 1rem',
            borderRadius: '0.75rem',
            fontSize: '0.875rem', fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
          New Study Set
        </button>
      </div>

      {/* Title + actions */}
      <div className="animate-fade-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '2.5rem', flexWrap: 'wrap' }}>
        <div>
          <p style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--c-violet)', marginBottom: '0.5rem' }}>Study Set</p>
          <h1 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', fontWeight: 800, color: 'var(--c-text)', lineHeight: 1.2, letterSpacing: '-0.02em' }}>{title}</h1>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
          <button className="btn-ghost" style={{ padding: '0.5rem 1rem', borderRadius: '0.75rem', fontSize: '0.875rem', fontWeight: 500, cursor: 'pointer' }}>Share</button>
          <button className="btn-violet-ghost" style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.5rem 1rem', borderRadius: '0.75rem',
            fontSize: '0.875rem', fontWeight: 500, cursor: 'pointer',
          }}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
            Save
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div className="tab-bar animate-fade-up" style={{ display: 'flex', gap: '0.25rem', marginBottom: '2rem', animationDelay: '0.1s' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setTab(tab.id)}
            className={`tab-btn ${activeTab === tab.id ? 'tab-btn-active' : ''}`}
          >
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={tab.d} />
            </svg>
            <span style={{ display: 'none' }} className="sm:inline">{tab.label}</span>
            <span style={{ display: 'inline' }}>{tab.label}</span>
            {tab.count !== null && (
              <span className="tab-count">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      <div style={{ minHeight: '24rem' }}>

        {/* SUMMARY */}
        {activeTab === 'summary' && (
          <div className="card animate-fade-up" style={{ padding: '2rem' }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.25rem', fontWeight: 700, color: 'var(--c-text)', marginBottom: '1.5rem' }}>
              {iconBox('var(--c-violet-bg)', <svg className="w-4 h-4" style={{ color: 'var(--c-violet)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>)}
              Core Concepts Summary
            </h2>
            <div>
              {summary.split('\n').filter(p => p.trim()).map((para, i) => (
                <p key={i} className="animate-fade-up" style={{
                  color: 'var(--c-text-muted)',
                  fontSize: '1.05rem',
                  lineHeight: 1.8,
                  marginBottom: '1rem',
                  animationDelay: `${i * 0.1}s`,
                }}>{para}</p>
              ))}
            </div>
          </div>
        )}

        {/* FLASHCARDS */}
        {activeTab === 'flashcards' && (
          <div>
            <p style={{ fontSize: '0.875rem', color: 'var(--c-text-hint)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5"/></svg>
              Click any card to reveal the definition
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.25rem' }}>
              {flashcards.map((card, i) => <FlashCard key={i} card={card} index={i} />)}
            </div>
          </div>
        )}

        {/* PRACTICE */}
        {activeTab === 'practice' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {practiceQs.map((q, i) => (
              <div key={i} className="card animate-fade-up" style={{ padding: '2rem', animationDelay: `${i * 0.1}s` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                  <div style={{
                    width: '2.25rem', height: '2.25rem', borderRadius: '0.75rem',
                    backgroundColor: 'var(--c-violet-bg)',
                    border: '1px solid var(--c-violet-border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <span style={{ color: 'var(--c-violet)', fontWeight: 700, fontSize: '0.875rem' }}>{i + 1}</span>
                  </div>
                  <span style={{ color: 'var(--c-text-hint)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Practice Question</span>
                </div>
                <p style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--c-text)', lineHeight: 1.5, marginBottom: '2rem' }}>{q.question}</p>

                {!revealedQs[i]
                  ? <RevealButton onClick={() => toggleReveal(i)} />
                  : (
                    <div className="answer-box animate-fade-up">
                      <p style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#16a34a', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        Answer
                      </p>
                      <p style={{ color: 'var(--c-text-muted)', lineHeight: 1.7, fontSize: '1.05rem' }}>{q.answer}</p>
                    </div>
                  )
                }
              </div>
            ))}
          </div>
        )}

        {/* CONCEPTS */}
        {activeTab === 'concepts' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1.25rem' }}>
            {concepts.map((concept, i) => (
              <div key={i} className="card card-hover animate-fade-up" style={{
                padding: '1.5rem',
                animationDelay: `${i * 0.08}s`,
                transition: 'border-color 0.2s, box-shadow 0.2s, transform 0.2s',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--c-text)' }}>{concept.term}</h3>
                  {iconBox('rgba(16,185,129,0.1)', <svg className="w-4 h-4" style={{ color: '#10b981' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>)}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {concept.related.map((rel, j) => (
                    <span key={j} className="surface-muted" style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '0.5rem',
                      fontSize: '0.8rem',
                      color: 'var(--c-text-muted)',
                    }}>{rel}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
