import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Home from './pages/Home';
import Results from './pages/Results';
import Dashboard from './pages/Dashboard';
import Auth from './pages/Auth';

/* ── Theme hook — syncs dark class to <html> ─────────── */
function useTheme() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  return [dark, setDark];
}

/* ── Toggle button ───────────────────────────────────── */
function ThemeToggle({ dark, setDark }) {
  return (
    <button
      onClick={() => setDark(d => !d)}
      aria-label="Toggle theme"
      title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="relative w-9 h-9 rounded-xl flex items-center justify-center active:scale-90"
      style={{
        backgroundColor: 'var(--c-bg-muted)',
        border: '1px solid var(--c-border)',
        color: 'var(--c-text-muted)',
        transition: 'all 0.2s ease',
      }}
    >
      {/* Sun */}
      <svg
        className="w-[18px] h-[18px] absolute"
        style={{
          opacity: dark ? 0 : 1,
          transform: dark ? 'rotate(90deg) scale(0.5)' : 'rotate(0deg) scale(1)',
          transition: 'opacity 0.3s, transform 0.4s',
        }}
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
      {/* Moon */}
      <svg
        className="w-[18px] h-[18px] absolute"
        style={{
          opacity: dark ? 1 : 0,
          transform: dark ? 'rotate(0deg) scale(1)' : 'rotate(-90deg) scale(0.5)',
          transition: 'opacity 0.3s, transform 0.4s',
        }}
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
    </button>
  );
}

/* ── Header ──────────────────────────────────────────── */
function Header({ dark, setDark }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '0.625rem 1rem',
        backgroundColor: scrolled ? 'var(--c-bg-card)' : 'transparent',
        borderBottom: `1px solid var(--c-border)`,
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        transition: 'background-color 0.3s ease',
        boxShadow: scrolled ? '0 1px 0 var(--c-border)' : 'none',
      }}
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center shadow-lg shadow-violet-500/30 transition-all duration-300 group-hover:scale-105 group-hover:shadow-violet-500/50">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5"
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-violet-600 to-fuchsia-500 bg-clip-text text-transparent tracking-tight">
            StudyMind
          </span>
        </Link>

        <nav className="flex items-center gap-2">
          <Link to="/dashboard" className="nav-link">Dashboard</Link>
          <Link to="/auth" className="btn-violet-ghost text-sm font-semibold px-4 py-1.5 rounded-lg">
            Sign In
          </Link>
          <ThemeToggle dark={dark} setDark={setDark} />
        </nav>
      </div>
    </header>
  );
}

/* ── Routes ──────────────────────────────────────────── */
function AnimatedRoutes() {
  const location = useLocation();
  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home />} />
        <Route path="/results/:id" element={<Results />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/auth" element={<Auth />} />
      </Routes>
    </main>
  );
}

/* ── App root ─────────────────────────────────────────── */
export default function App() {
  const [dark, setDark] = useTheme();
  return (
    <BrowserRouter>
      <div className="theme-root">
        <Header dark={dark} setDark={setDark} />
        <AnimatedRoutes />
      </div>
    </BrowserRouter>
  );
}
