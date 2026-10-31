import { useEffect, useRef, useState } from "react";
import {
  useParams,
  useSearchParams,
  Link,
  useNavigate,
} from "react-router-dom";
import { api, errorMessage } from "../api/client";
import { useDraft } from "../context/Draft";
import { Flashcards, Practice } from "../components/StudyTools";
import { download } from "../utils/download";
const TABS = ["summary", "flashcards", "practice", "concepts"];
export default function Results() {
  const { id } = useParams(),
    [params, setParams] = useSearchParams(),
    navigate = useNavigate(),
    draft = useDraft();
  const [data, setData] = useState(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [retry, setRetry] = useState(0),
    [saving, setSaving] = useState(false),
    [title, setTitle] = useState(""),
    [retain, setRetain] = useState(false),
    [notice, setNotice] = useState("");
  const heading = useRef(null);
  const hasData = Boolean(data);
  useEffect(() => {
    if (!loading && hasData) heading.current?.focus();
  }, [loading, hasData]);
  const isDraft = id.startsWith("draft-");
  const tab = TABS.includes(params.get("tab")) ? params.get("tab") : "summary";
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setData(null);
    setRetain(false);
    setNotice("");
    (isDraft
      ? api.getDraft(id.slice(6), controller.signal)
      : api.getSet(id, controller.signal)
    )
      .then((result) => {
        if (!controller.signal.aborted) {
          setData(result);
          setTitle(result.title);
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorMessage(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [id, isDraft, retry]);
  async function save(event) {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    setError("");
    try {
      if (isDraft) {
        const saved = await api.saveStudySet({
          generation_id: data.generation_id,
          title,
          source_text: retain ? draft.sourceFor(data.generation_id) : "",
        });
        navigate(`/results/${saved.id}?tab=${tab}`, { replace: true });
      } else {
        setData(await api.rename(id, title));
        setNotice("Title updated.");
      }
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }
  if (loading)
    return (
      <section aria-busy="true">
        <h1 tabIndex={-1}>Opening study set</h1>
        <p role="status" className="muted">
          Loading your study materials…
        </p>
        <div className="skeleton mt-6 h-40" />
      </section>
    );
  if (!data)
    return (
      <section>
        <h1 tabIndex={-1}>This study set couldn’t load</h1>
        <p className="notice-error" role="alert">
          {error}
        </p>
        <button className="btn mt-5" onClick={() => setRetry((v) => v + 1)}>
          Retry opening set
        </button>
        <Link className="ml-5" to="/dashboard">
          Saved sets
        </Link>
      </section>
    );
  return (
    <div className="space-y-7">
      <section>
        <p className="eyebrow">
          {isDraft
            ? "UNSAVED DRAFT · AVAILABLE FOR ONE HOUR"
            : "YOUR PRIVATE STUDY SET"}
        </p>
        <h1 ref={heading} tabIndex={-1}>
          {data.title}
        </h1>
        <p className="muted mt-3">
          AI-generated study aids can contain mistakes. Check definitions and
          answers against your source material.
        </p>
      </section>
      {error && (
        <p className="notice-error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="notice-success" role="status">
          {notice}
        </p>
      )}
      <form className="panel space-y-4" onSubmit={save}>
        <label className="field">
          Study set title
          <input
            required
            maxLength={255}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        {isDraft && (
          <label className="flex items-start gap-3 text-sm">
            <input
              type="checkbox"
              className="mt-1"
              checked={retain}
              disabled={!draft.sourceFor(data.generation_id)}
              onChange={(event) => setRetain(event.target.checked)}
            />
            <span>
              Include the original source notes in the saved set.{" "}
              {draft.sourceFor(data.generation_id)
                ? "Otherwise, save only the generated study material."
                : "Source notes are no longer in this tab; the generated material can still be saved."}
            </span>
          </label>
        )}
        <div className="flex flex-wrap gap-3">
          <button className="btn" disabled={saving || !title.trim()}>
            {saving ? "Saving…" : isDraft ? "Save study set" : "Update title"}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() =>
              download("studymind-set.json", JSON.stringify(data, null, 2))
            }
          >
            Download study material
          </button>
          <Link className="btn-secondary" to="/">
            New study set
          </Link>
        </div>
      </form>
      <div role="tablist" aria-label="Study material sections" className="tabs">
        {TABS.map((value, i) => (
          <button
            key={value}
            role="tab"
            id={`tab-${value}`}
            aria-selected={tab === value}
            aria-controls={`panel-${value}`}
            tabIndex={tab === value ? 0 : -1}
            className={tab === value ? "tab active" : "tab"}
            onClick={() => setParams({ tab: value })}
            onKeyDown={(event) => {
              let next;
              if (event.key === "ArrowRight") next = (i + 1) % TABS.length;
              if (event.key === "ArrowLeft")
                next = (i + TABS.length - 1) % TABS.length;
              if (event.key === "Home") next = 0;
              if (event.key === "End") next = TABS.length - 1;
              if (next !== undefined) {
                event.preventDefault();
                setParams({ tab: TABS[next] });
                event.currentTarget.parentElement.children[next].focus();
              }
            }}
          >
            {value[0].toUpperCase() + value.slice(1)}
          </button>
        ))}
      </div>
      {TABS.map((value) => (
        <section
          key={value}
          role="tabpanel"
          hidden={tab !== value}
          tabIndex={0}
          id={`panel-${value}`}
          aria-labelledby={`tab-${value}`}
          className="min-h-56"
        >
          {tab === value && (
            <>
              {tab === "summary" && (
                <div className="panel whitespace-pre-wrap leading-8">
                  {data.summary}
                </div>
              )}
              {tab === "flashcards" && (
                <Flashcards key={id} cards={data.flashcards} />
              )}{" "}
              {tab === "practice" && <Practice questions={data.questions} />}{" "}
              {tab === "concepts" && (
                <div className="grid gap-4 sm:grid-cols-2">
                  {data.concepts.map((item, i) => (
                    <article key={i} className="panel">
                      <h2 className="text-xl">{item.term}</h2>
                      <p className="muted mt-3">
                        {item.related.length
                          ? item.related.join(" · ")
                          : "Review this concept in your source notes."}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      ))}
    </div>
  );
}
