import axios from "axios";
export const sessionTransport = axios.create({
  baseURL: import.meta.env?.VITE_API_URL || "/api",
  withCredentials: true,
  timeout: 15000,
});
const client = axios.create({
  baseURL: import.meta.env?.VITE_API_URL || "/api",
  withCredentials: true,
  timeout: 15000,
});
let accessToken = "",
  csrfPromise = null,
  refreshPromise = null;
const listeners = new Set();
function publish(data) {
  accessToken = data?.access_token || "";
  for (const listener of listeners) listener(data?.user ?? null);
}
export const subscribeAuth = (listener) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};
export function clearAuth() {
  publish(null);
  window.dispatchEvent(new Event("studymind:logout"));
}
async function csrf() {
  if (!csrfPromise)
    csrfPromise = sessionTransport
      .get("/auth/csrf")
      .then((r) => r.data.csrf_token)
      .finally(() => {
        csrfPromise = null;
      });
  return csrfPromise;
}
export function refreshAuth() {
  if (!refreshPromise) {
    const run = async () => {
      const nonce = await csrf();
      const response = await sessionTransport.post(
        "/auth/refresh",
        {},
        { headers: { "X-CSRF-Token": nonce } },
      );
      publish(response.data);
      return response.data.user;
    };
    refreshPromise = (
      typeof navigator !== "undefined" && navigator.locks
        ? navigator.locks.request("studymind-refresh", run)
        : run()
    )
      .catch((error) => {
        publish(null);
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}
client.interceptors.request.use(async (config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  if (config.url.startsWith("/auth/") && config.method !== "get")
    config.headers["X-CSRF-Token"] = await csrf();
  return config;
});
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (
      error.response?.status === 401 &&
      config &&
      !config._retried &&
      !config.url.startsWith("/auth/")
    ) {
      config._retried = true;
      try {
        await refreshAuth();
        return client.request(config);
      } catch {
        publish(null);
      }
    }
    return Promise.reject(error);
  },
);
export function errorMessage(error) {
  if (axios.isCancel(error)) return "Request cancelled.";
  if (error.code === "ECONNABORTED")
    return "This request took too long. Your notes remain in this page; retry to recover the same generation.";
  if (error.response?.status === 422)
    return "Check the required fields, text length, and option limits.";
  const detail = error.response?.data?.detail;
  return typeof detail === "string" && detail.length < 300
    ? detail
    : "Could not complete this request. Check your connection and retry.";
}
export const api = {
  config: async () => (await client.get("/config")).data,
  login: async (email, password) => {
    const { data } = await client.post("/auth/login", { email, password });
    publish(data);
    return data.user;
  },
  register: async (email, password) =>
    (await client.post("/auth/register", { email, password })).data,
  logout: async () => {
    await client.post("/auth/logout");
    clearAuth();
  },
  forgot: async (email) =>
    (await client.post("/auth/forgot-password", { email })).data,
  resend: async (email) =>
    (await client.post("/auth/resend-verification", { email })).data,
  verify: async (token, password) =>
    (await client.post("/auth/verify-email", { token, password })).data,
  reset: async (token, new_password) =>
    (await client.post("/auth/reset-password", { token, new_password })).data,
  changePassword: async (current_password, new_password) => {
    const { data } = await client.post("/auth/change-password", {
      current_password,
      new_password,
    });
    clearAuth();
    return data;
  },
  deleteAccount: async (password) => {
    await client.delete("/auth/account", { data: { password } });
    clearAuth();
  },
  generateStudySet: async (content, options, key, signal) =>
    (
      await client.post(
        "/generate",
        { content, options, consent_to_provider: true },
        { headers: { "Idempotency-Key": key }, timeout: 125000, signal },
      )
    ).data,
  extractPdfText: async (file, signal) => {
    const body = new FormData();
    body.append("file", file);
    return (
      await client.post("/generate/extract-pdf", body, {
        signal,
        timeout: 12000,
      })
    ).data;
  },
  getDraft: async (id, signal) =>
    (await client.get(`/generate/${id}`, { signal })).data,
  saveStudySet: async (body) => (await client.post("/studysets", body)).data,
  listSets: async (offset = 0, signal) =>
    (await client.get("/studysets", { params: { offset, limit: 20 }, signal }))
      .data,
  getSet: async (id, signal) =>
    (await client.get(`/studysets/${id}`, { signal })).data,
  rename: async (id, title) =>
    (await client.patch(`/studysets/${id}`, { title })).data,
  deleteSet: async (id) => client.delete(`/studysets/${id}`),
  exportSets: async () => (await client.get("/studysets/export")).data,
};
export default client;
