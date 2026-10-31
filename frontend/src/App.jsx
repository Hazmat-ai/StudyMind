import {
  createBrowserRouter,
  RouterProvider,
  Outlet,
  Link,
  Navigate,
  useLocation,
  useRouteError,
} from "react-router-dom";
import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./context/Auth";
import { DraftProvider } from "./context/Draft";
import Home from "./pages/Home";
import Results from "./pages/Results";
import Dashboard from "./pages/Dashboard";
import Auth from "./pages/Auth";
import Account from "./pages/Account";
function Protected({ children }) {
  const { user, ready } = useAuth();
  const location = useLocation();
  if (!ready) return <p role="status">Reconnecting your account…</p>;
  return user ? (
    <div key={user.id}>{children}</div>
  ) : (
    <Navigate
      to="/auth"
      state={{ from: location.pathname + location.search }}
      replace
    />
  );
}
function Layout() {
  const { user, ready } = useAuth();
  const location = useLocation();
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem("theme") !== "light";
    } catch {
      return true;
    }
  });
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try {
      localStorage.setItem("theme", dark ? "dark" : "light");
    } catch {
      /* Theme remains usable without storage. */
    }
  }, [dark]);
  useEffect(() => {
    window.scrollTo(0, 0);
    document.querySelector("main h1")?.focus();
  }, [location.pathname]);
  return (
    <DraftProvider>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="shell flex flex-wrap items-center justify-between gap-3">
          <Link to="/" className="brand">
            <span className="brand-icon" aria-hidden="true">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  d="M3 5h7l2 2 2-2h7v14h-7l-2 2-2-2H3zM12 7v14"
                  strokeWidth="2"
                />
              </svg>
            </span>
            <span>StudyMind</span>
          </Link>
          <nav
            aria-label="Main navigation"
            className="flex flex-wrap items-center gap-4"
          >
            <Link to="/dashboard">Saved sets</Link>
            {ready && user ? (
              <Link to="/account">Account</Link>
            ) : (
              <Link to="/auth">Sign in</Link>
            )}
            <button
              className="theme-toggle"
              onClick={() => setDark((value) => !value)}
              aria-label={
                dark ? "Switch to light theme" : "Switch to dark theme"
              }
            >
              {dark ? "☀" : "☾"}
            </button>
          </nav>
        </div>
      </header>
      <main id="main" className="shell py-10">
        <Outlet />
      </main>
      <footer className="shell border-t border-slate-300 py-6 text-sm dark:border-slate-700">
        <Link to="/privacy">Privacy and data</Link>
        <p className="muted mt-2">
          Study aids generated from your notes. Check important facts against
          your course material.
        </p>
      </footer>
    </DraftProvider>
  );
}
function Privacy() {
  return (
    <article className="prose-study">
      <h1 tabIndex={-1}>Your notes, your choice</h1>
      <p>
        Generating study aids sends the text you approve to Anthropic. Use
        material you have permission to share and remove sensitive personal
        information first.
      </p>
      <p>
        Unsaved generated drafts are recoverable for one hour. Quota records
        cover a rolling 24-hour window; scheduled cleanup removes expired data.
        Saved sets stay private to your account until you delete them; saving
        source notes is optional. You can export your saved material or delete
        your account in Account.
      </p>
      <p>
        Access tokens stay in memory. An HttpOnly browser cookie keeps you
        signed in for up to seven days. Only the theme preference is stored in
        localStorage. No camera, microphone or advertising tracker is used.
      </p>
      <p>
        Deleting records removes live application access. Hosting logs and
        restricted backups follow the operator’s documented retention policy.
        Contact the service operator for support and the applicable hosting,
        provider and backup retention details.
      </p>
    </article>
  );
}
function RouteError() {
  useRouteError();
  return (
    <main className="shell py-16">
      <h1>We couldn’t display this screen</h1>
      <p className="muted mt-3">
        Reload to reconnect. Saved study sets remain in your account.
      </p>
      <button className="btn mt-5" onClick={() => window.location.reload()}>
        Reload StudyMind
      </button>
    </main>
  );
}
const router = createBrowserRouter([
  {
    element: <Layout />,
    errorElement: <RouteError />,
    children: [
      { path: "/", element: <Home /> },
      {
        path: "/results/:id",
        element: (
          <Protected>
            <Results />
          </Protected>
        ),
      },
      {
        path: "/dashboard",
        element: (
          <Protected>
            <Dashboard />
          </Protected>
        ),
      },
      {
        path: "/account",
        element: (
          <Protected>
            <Account />
          </Protected>
        ),
      },
      { path: "/privacy", element: <Privacy /> },
      { path: "/auth", element: <Auth key="login" mode="login" /> },
      {
        path: "/auth/register",
        element: <Auth key="register" mode="register" />,
      },
      { path: "/auth/forgot", element: <Auth key="forgot" mode="forgot" /> },
      { path: "/auth/verify", element: <Auth key="verify" mode="verify" /> },
      { path: "/auth/reset", element: <Auth key="reset" mode="reset" /> },
      {
        path: "*",
        element: (
          <section>
            <h1 tabIndex={-1}>Page not found</h1>
            <Link to="/">Return to your notes</Link>
          </section>
        ),
      },
    ],
  },
]);
export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}
