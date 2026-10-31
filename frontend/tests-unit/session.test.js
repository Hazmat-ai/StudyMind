import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { AxiosError } from "axios";
import client, {
  sessionTransport,
  api,
  refreshAuth,
  clearAuth,
  errorMessage,
} from "../src/api/client.js";
globalThis.window = { dispatchEvent() {} };
const response = (config, status, data) => ({
  config,
  status,
  data,
  statusText: String(status),
  headers: {},
});
beforeEach(() => clearAuth());
test("concurrent private requests refresh once and retry with the new in-memory token", async () => {
  let refreshes = 0,
    nonces = 0,
    requests = 0;
  sessionTransport.defaults.adapter = async (config) => {
    if (config.url === "/auth/csrf") {
      nonces++;
      return response(config, 200, { csrf_token: "test-nonce" });
    }
    refreshes++;
    await new Promise((resolve) => setTimeout(resolve, 10));
    assert.equal(config.headers["X-CSRF-Token"], "test-nonce");
    return response(config, 200, {
      access_token: "fresh",
      user: { id: "one" },
    });
  };
  client.defaults.adapter = async (config) => {
    requests++;
    if (config.headers.Authorization !== "Bearer fresh")
      throw new AxiosError(
        "unauthorized",
        "ERR_BAD_REQUEST",
        config,
        {},
        response(config, 401, {}),
      );
    return response(config, 200, { ok: true });
  };
  const results = await Promise.all([
    client.get("/studysets"),
    client.get("/studysets"),
  ]);
  assert.equal(refreshes, 1);
  assert.equal(nonces, 1);
  assert.equal(requests, 4);
  assert.ok(results.every((r) => r.data.ok));
});
test("persistent 401 retries once and login failures never trigger refresh loops", async () => {
  let refreshes = 0,
    requests = 0;
  sessionTransport.defaults.adapter = async (config) =>
    config.url === "/auth/csrf"
      ? response(config, 200, { csrf_token: "nonce" })
      : (refreshes++,
        response(config, 200, {
          access_token: "expired",
          user: { id: "one" },
        }));
  client.defaults.adapter = async (config) => {
    requests++;
    throw new AxiosError(
      "unauthorized",
      "ERR_BAD_REQUEST",
      config,
      {},
      response(config, 401, {}),
    );
  };
  await assert.rejects(client.get("/studysets"));
  assert.equal(requests, 2);
  assert.equal(refreshes, 1);
  await assert.rejects(api.login("a@example.com", "wrong"));
  assert.equal(refreshes, 1);
});
test("session bootstrap coalesces refresh and validation errors do not expose server input", async () => {
  let calls = 0;
  sessionTransport.defaults.adapter = async (config) =>
    config.url === "/auth/csrf"
      ? response(config, 200, { csrf_token: "nonce" })
      : (calls++,
        response(config, 200, { access_token: "token", user: { id: "one" } }));
  await Promise.all([refreshAuth(), refreshAuth()]);
  assert.equal(calls, 1);
  assert.equal(
    errorMessage({
      response: {
        status: 422,
        data: { detail: [{ input: "private-password" }] },
      },
    }),
    "Check the required fields, text length, and option limits.",
  );
});
