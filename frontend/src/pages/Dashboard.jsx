import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errorMessage } from "../api/client";
export default function Dashboard() {
  const [sets, setSets] = useState([]),
    [total, setTotal] = useState(0),
    [offset, setOffset] = useState(0),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [retry, setRetry] = useState(0),
    [deleting, setDeleting] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    api
      .listSets(offset, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setSets(data.items);
          setTotal(data.total);
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorMessage(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [offset, retry]);
  async function remove(item) {
    if (
      deleting ||
      !window.confirm(`Delete “${item.title}” and its study material?`)
    )
      return;
    setDeleting(item.id);
    setError("");
    try {
      await api.deleteSet(item.id);
      if (sets.length === 1 && offset > 0)
        setOffset((v) => Math.max(0, v - 20));
      else setRetry((v) => v + 1);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setDeleting("");
    }
  }
  return (
    <section>
      <div className="flex flex-wrap justify-between gap-4">
        <div>
          <p className="eyebrow">YOUR STUDY LIBRARY</p>
          <h1 tabIndex={-1}>Saved sets</h1>
          <p className="muted mt-3">
            {total} of 100 available saved sets. Only your account can access
            these.
          </p>
        </div>
        <Link className="btn self-start" to="/">
          Create a study set
        </Link>
      </div>
      {error && (
        <div className="notice-error mt-5" role="alert">
          {error}
          <button
            className="text-button ml-4"
            onClick={() => setRetry((v) => v + 1)}
          >
            Retry loading
          </button>
        </div>
      )}
      {loading ? (
        <p className="muted mt-8" role="status">
          Loading saved sets…
        </p>
      ) : !sets.length && !error ? (
        <div className="panel mt-8">
          <h2>A fresh start</h2>
          <p className="muted mt-3">
            Generate your first study set from lecture notes, then save it here
            for your next study session.
          </p>
          <Link className="btn mt-5 inline-block" to="/">
            Start with your notes
          </Link>
        </div>
      ) : (
        <div className="mt-8 grid gap-5 sm:grid-cols-2">
          {sets.map((item) => (
            <article key={item.id} className="panel">
              <h2 className="text-xl">
                <Link to={`/results/${item.id}`}>{item.title}</Link>
              </h2>
              <p className="muted mt-3 text-sm">
                Updated {new Date(item.updated_at).toLocaleDateString()}
              </p>
              <div className="mt-6 flex justify-between gap-4">
                <Link to={`/results/${item.id}?tab=flashcards`}>
                  Review flashcards
                </Link>
                <button
                  className="text-button danger"
                  disabled={!!deleting}
                  onClick={() => remove(item)}
                >
                  Delete<span className="sr-only"> {item.title}</span>
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
      <div className="mt-8 flex justify-between gap-4">
        <button
          className="btn-secondary"
          disabled={offset === 0 || loading}
          onClick={() => setOffset((v) => Math.max(0, v - 20))}
        >
          Previous page
        </button>
        <button
          className="btn-secondary"
          disabled={offset + 20 >= total || loading}
          onClick={() => setOffset((v) => v + 20)}
        >
          Next page
        </button>
      </div>
    </section>
  );
}
