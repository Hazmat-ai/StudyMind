import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api, errorMessage } from "../api/client";
import { useAuth } from "../context/Auth";
const titles = {
  login: "Welcome back",
  register: "Make room for better study",
  forgot: "Reset your password",
  verify: "Verify your email",
  reset: "Choose a new password",
};
export default function Auth({ mode }) {
  const navigate = useNavigate(),
    location = useLocation();
  const auth = useAuth();
  const [token] = useState(
    () => new URLSearchParams(location.hash.slice(1)).get("token") || "",
  );
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [verification, setVerification] = useState(false);
  useEffect(() => {
    if (location.hash) navigate(location.pathname, { replace: true });
  }, [location.hash, location.pathname, navigate]);
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (mode === "login") {
        await auth.login(email, password);
        const from = location.state?.from;
        navigate(from?.startsWith("/") && !from.startsWith("//") ? from : "/", {
          replace: true,
        });
      }
      if (mode === "register") {
        const data = await api.register(email, password);
        setVerification(data.verification_required);
        setMessage(
          data.verification_required
            ? data.message
            : "Account created. You can sign in now.",
        );
        setPassword("");
      }
      if (mode === "forgot") setMessage((await api.forgot(email)).message);
      if (mode === "verify") {
        await api.verify(token, password);
        setMessage("Email verified. You can sign in now.");
        setPassword("");
      }
      if (mode === "reset") {
        setMessage((await api.reset(token, password)).message);
        setPassword("");
      }
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel mx-auto max-w-lg">
      <p className="eyebrow">YOUR STUDY SPACE</p>
      <h1 tabIndex={-1}>{titles[mode]}</h1>
      <p className="muted mb-6">
        {mode === "verify"
          ? "Use the password you chose when registering."
          : "Private saved sets, ready when you need them."}
      </p>
      {error && (
        <p role="alert" className="notice-error">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="notice-success">
          {message}
        </p>
      )}
      <form onSubmit={submit} className="space-y-5">
        {["login", "register", "forgot"].includes(mode) && (
          <label className="field">
            Email address
            <input
              type="email"
              required
              maxLength={254}
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
        )}
        {mode !== "forgot" && (
          <label className="field">
            {mode === "reset" ? "New password" : "Password"}
            <input
              type="password"
              required
              minLength={["register", "reset"].includes(mode) ? 12 : 1}
              maxLength={128}
              autoComplete={
                ["register", "reset"].includes(mode)
                  ? "new-password"
                  : "current-password"
              }
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            {["register", "reset"].includes(mode) && (
              <span className="muted text-sm">
                Use at least 12 characters. Long passphrases work well.
              </span>
            )}
          </label>
        )}
        {["verify", "reset"].includes(mode) && !token ? (
          <p className="notice-error">
            Open the complete link from your email. This page is missing its
            one-time token.
          </p>
        ) : (
          <button className="btn w-full" disabled={busy}>
            {busy
              ? "Please wait…"
              : mode === "login"
                ? "Sign in"
                : mode === "register"
                  ? "Create account"
                  : mode === "forgot"
                    ? "Send recovery link"
                    : mode === "verify"
                      ? "Verify email"
                      : "Update password"}
          </button>
        )}
      </form>
      <div className="mt-6 flex flex-wrap gap-4 text-sm">
        <Link to="/auth">Sign in</Link>
        <Link to="/auth/register">Create account</Link>
        <Link to="/auth/forgot">Forgot password?</Link>
      </div>
      {(verification || mode === "login") && (
        <button
          className="text-button mt-5"
          disabled={busy || !email}
          onClick={async () => {
            setBusy(true);
            try {
              setMessage((await api.resend(email)).message);
            } catch (e) {
              setError(errorMessage(e));
            } finally {
              setBusy(false);
            }
          }}
        >
          Resend verification email
        </button>
      )}
    </section>
  );
}
