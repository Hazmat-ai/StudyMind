import { createContext, useContext, useEffect, useState } from "react";
import { api, refreshAuth, subscribeAuth, errorMessage } from "../api/client";
const Context = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null),
    [ready, setReady] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    const unsubscribe = subscribeAuth(setUser);
    let active = true;
    try {
      localStorage.removeItem("token");
    } catch {
      /* Private browsing can block storage. */
    }
    refreshAuth()
      .catch((e) => {
        if (active && e.response?.status !== 401) setError(errorMessage(e));
      })
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);
  return (
    <Context.Provider
      value={{ user, ready, error, login: api.login, logout: api.logout }}
    >
      {children}
    </Context.Provider>
  );
}
export const useAuth = () => useContext(Context);
