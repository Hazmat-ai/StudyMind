import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/Auth";
import { useDraft } from "../context/Draft";
import { api, errorMessage } from "../api/client";
export default function Home() {
  const auth = useAuth(),
    draft = useDraft(),
    navigate = useNavigate();
  const [config, setConfig] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [uploading, setUploading] = useState(false),
    [consent, setConsent] = useState(false);
  const [cards, setCards] = useState(10),
    [questions, setQuestions] = useState(5),
    [difficulty, setDifficulty] = useState("university");
  const current = useRef(0),
    controller = useRef(null),
    intent = useRef(null),
    locked = useRef(false);
  useEffect(() => {
    let active = true;
    api
      .config()
      .then((data) => {
        if (active) setConfig(data);
      })
      .catch(() => {
        if (active)
          setError(
            "Could not check service availability. Reload to reconnect.",
          );
      });
    return () => {
      active = false;
      controller.current?.abort();
    };
  }, []);
  useEffect(() => {
    const warn = (event) => {
      if (draft.content.trim()) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [draft.content]);
  const valid =
    draft.content.trim().length >= 50 &&
    draft.content.length <= 12000 &&
    cards >= 1 &&
    cards <= 30 &&
    questions >= 1 &&
    questions <= 15;
  async function generate(event) {
    event.preventDefault();
    if (locked.current || !auth.user || !consent || !valid) return;
    locked.current = true;
    setBusy(true);
    setError("");
    const generation = ++current.current;
    controller.current = new AbortController();
    const source = draft.content;
    const options = {
      num_flashcards: cards,
      num_questions: questions,
      difficulty,
    };
    const fingerprint = JSON.stringify({ source, options });
    if (intent.current?.fingerprint !== fingerprint)
      intent.current = { fingerprint, key: crypto.randomUUID() };
    try {
      const data = await api.generateStudySet(
        source,
        options,
        intent.current.key,
        controller.current.signal,
      );
      if (generation === current.current) {
        draft.rememberSource(data.generation_id, source);
        navigate(`/results/draft-${data.generation_id}`);
      }
    } catch (e) {
      if (generation === current.current) {
        setError(errorMessage(e));
        if ([503, 410].includes(e.response?.status)) intent.current = null;
      }
    } finally {
      if (generation === current.current) {
        locked.current = false;
        setBusy(false);
      }
    }
  }
  async function upload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setError("Choose a PDF no larger than 5 MiB.");
      return;
    }
    setUploading(true);
    setError("");
    controller.current = new AbortController();
    try {
      draft.setContent(
        (await api.extractPdfText(file, controller.current.signal)).content,
      );
    } catch (e) {
      if (!controller.current.signal.aborted) setError(errorMessage(e));
    } finally {
      setUploading(false);
    }
  }
  return (
    <div className="space-y-8">
      <section className="max-w-2xl">
        <p className="eyebrow">LESS PREP. MORE ACTIVE RECALL.</p>
        <h1 tabIndex={-1}>
          Turn your notes into
          <br />
          <span className="text-violet-600 dark:text-violet-300">
            a clearer study plan.
          </span>
        </h1>
        <p className="muted mt-4 text-lg">
          Paste lecture notes or extract text from a PDF. Build a summary,
          flashcards, practice questions and connected concepts in one focused
          space.
        </p>
      </section>
      {(error || auth.error) && (
        <p className="notice-error" role="alert">
          {error || auth.error}
        </p>
      )}
      <form onSubmit={generate} className="panel space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="m-0">Start with your course material</h2>
          <label className="btn-secondary cursor-pointer focus-within:outline focus-within:outline-2 focus-within:outline-violet-500">
            {uploading ? "Reading PDF…" : "Choose PDF"}
            <input
              className="sr-only"
              type="file"
              accept="application/pdf,.pdf"
              disabled={!auth.user || busy || uploading}
              onChange={upload}
            />
          </label>
        </div>
        <p className="muted text-sm">
          PDFs: up to 5 MiB and 40 pages. Text: 50–12,000 characters. Scanned
          documents need OCR before upload.
        </p>
        <label className="field" htmlFor="notes">
          Your notes
          <textarea
            id="notes"
            rows={10}
            value={draft.content}
            readOnly={busy || uploading}
            onChange={(event) => draft.setContent(event.target.value)}
            placeholder="Paste the material you want to understand…"
            aria-describedby="notes-count"
          />
        </label>
        <p
          id="notes-count"
          className={
            draft.content.length > 12000
              ? "text-rose-600 dark:text-rose-300"
              : "muted"
          }
        >
          {draft.content.length.toLocaleString()} / 12,000 characters
        </p>
        <div className="grid gap-5 sm:grid-cols-3">
          <label className="field">
            Flashcards
            <input
              type="number"
              min={1}
              max={30}
              value={cards}
              disabled={busy}
              onChange={(event) => setCards(Number(event.target.value))}
            />
          </label>
          <label className="field">
            Practice questions
            <input
              type="number"
              min={1}
              max={15}
              value={questions}
              disabled={busy}
              onChange={(event) => setQuestions(Number(event.target.value))}
            />
          </label>
          <label className="field">
            Level
            <select
              value={difficulty}
              disabled={busy}
              onChange={(event) => setDifficulty(event.target.value)}
            >
              <option value="high_school">High school</option>
              <option value="university">University</option>
              <option value="advanced">Advanced</option>
            </select>
          </label>
        </div>
        <label className="flex items-start gap-3 text-sm">
          <input
            className="mt-1"
            type="checkbox"
            checked={consent}
            disabled={busy}
            onChange={(event) => setConsent(event.target.checked)}
          />
          <span>
            I agree to send this text to Anthropic to generate study aids. I
            have permission to share it and have removed sensitive details.{" "}
            <Link to="/privacy">Data details</Link>
          </span>
        </label>
        {auth.user ? (
          <button
            className="btn w-full"
            disabled={
              busy ||
              uploading ||
              !valid ||
              !consent ||
              !config?.generation_ready
            }
          >
            {busy ? "Generating study aids…" : "Generate study set"}
          </button>
        ) : (
          <Link
            className="btn block text-center"
            to="/auth"
            state={{ from: "/" }}
          >
            Sign in to generate
          </Link>
        )}
        {config && !config.generation_ready && (
          <p className="notice-neutral">
            Generation is currently unavailable. You can still sign in and
            review saved sets.
          </p>
        )}
        {busy && (
          <div aria-busy="true">
            <p role="status" className="muted mb-3">
              Preparing your summary, cards and questions. Your notes remain on
              this page.
            </p>
            <div className="skeleton h-6 w-3/4" />
            <div className="skeleton mt-3 h-6 w-full" />
            <div className="skeleton mt-3 h-24 w-full" />
            <button
              className="text-button mt-4"
              type="button"
              onClick={() => {
                current.current++;
                controller.current?.abort();
                locked.current = false;
                setBusy(false);
                setError(
                  "Stopped waiting. Retry the same notes and options to recover a completed generation without starting another one.",
                );
              }}
            >
              Stop waiting
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
