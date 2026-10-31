import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, errorMessage } from "../api/client";
import { useAuth } from "../context/Auth";
import { download } from "../utils/download";
export default function Account() {
  const { user, logout } = useAuth(),
    navigate = useNavigate();
  const [password, setPassword] = useState(""),
    [newPassword, setNewPassword] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function action(run) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await run();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="mx-auto max-w-xl space-y-6">
      <div>
        <p className="eyebrow">YOUR ACCOUNT</p>
        <h1 tabIndex={-1}>Private by default</h1>
        <p className="muted mt-3">Signed in as {user.email}</p>
      </div>
      {error && (
        <p className="notice-error" role="alert">
          {error}
        </p>
      )}
      <div className="panel">
        <h2>Keep a copy</h2>
        <p className="muted mt-3">
          Export all your saved sets, including source notes you chose to
          retain.
        </p>
        <button
          className="btn-secondary mt-5"
          disabled={busy}
          onClick={() =>
            action(async () =>
              download(
                "studymind-export.json",
                JSON.stringify(await api.exportSets(), null, 2),
              ),
            )
          }
        >
          Export saved study sets
        </button>
      </div>
      <form
        className="panel space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          action(async () => {
            await api.changePassword(password, newPassword);
            navigate("/auth", { replace: true });
          });
        }}
      >
        <h2>Change password</h2>
        <label className="field">
          Current password
          <input
            type="password"
            required
            autoComplete="current-password"
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <label className="field">
          New password
          <input
            type="password"
            required
            minLength={12}
            maxLength={128}
            autoComplete="new-password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
        </label>
        <p className="muted text-sm">
          Changing your password signs out every session.
        </p>
        <button className="btn" disabled={busy}>
          Update password
        </button>
      </form>
      <div className="panel">
        <h2>Session and deletion</h2>
        <button
          className="btn-secondary mt-5"
          disabled={busy}
          onClick={() =>
            action(async () => {
              await logout();
              navigate("/auth", { replace: true });
            })
          }
        >
          Sign out
        </button>
        <p className="muted mt-5">
          Deleting your account removes your saved sets and active sessions.
          Enter your current password above, then confirm.
        </p>
        <button
          className="text-button danger mt-4"
          disabled={busy || !password}
          onClick={() => {
            if (
              window.confirm(
                "Permanently delete your account and all saved sets?",
              )
            )
              action(async () => {
                await api.deleteAccount(password);
                navigate("/auth", { replace: true });
              });
          }}
        >
          Delete my account
        </button>
      </div>
    </section>
  );
}
