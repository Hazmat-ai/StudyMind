import { createContext, useContext, useEffect, useState } from "react";
import { useAuth } from "./Auth";
const Context = createContext(null);
export function DraftProvider({ children }) {
  const { user } = useAuth();
  const [draft, setDraft] = useState({ owner: null, content: "" }),
    [sources, setSources] = useState({});
  useEffect(() => {
    const clear = () => {
      setDraft({ owner: null, content: "" });
      setSources({});
    };
    window.addEventListener("studymind:logout", clear);
    return () => window.removeEventListener("studymind:logout", clear);
  }, []);
  const content =
    draft.owner && user && draft.owner !== user.id ? "" : draft.content;
  const setContent = (value) =>
    setDraft({ owner: user?.id ?? draft.owner, content: value });
  const rememberSource = (id, text) =>
    setSources((current) => ({
      ...Object.fromEntries(Object.entries(current).slice(-4)),
      [id]: { owner: user?.id, content: text },
    }));
  const sourceFor = (id) =>
    sources[id]?.owner === user?.id ? sources[id].content : "";
  return (
    <Context.Provider
      value={{ content, setContent, rememberSource, sourceFor }}
    >
      {children}
    </Context.Provider>
  );
}
export const useDraft = () => useContext(Context);
