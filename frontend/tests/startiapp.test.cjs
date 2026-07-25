const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync("apps/core/static/core/js/startiapp.js", "utf8");

function runBridge({
  dataset,
  sdk,
  elements = {},
  fetchImpl = async () => ({ json: async () => ({ ok: true }) }),
}) {
  const listeners = new Map();
  const timers = new Map();
  let nextTimerId = 0;
  const body = { dataset };
  const document = {
    body,
    cookie: "",
    querySelector: (selector) => elements[selector] || null,
    addEventListener(type, listener, options = {}) {
      const registered = listeners.get(type) || [];
      registered.push({ listener, once: Boolean(options.once) });
      listeners.set(type, registered);
    },
    removeEventListener(type, listener) {
      listeners.set(
        type,
        (listeners.get(type) || []).filter((entry) => entry.listener !== listener)
      );
    },
    dispatchEvent(event) {
      for (const entry of [...(listeners.get(event.type) || [])]) {
        entry.listener(event);
        if (entry.once) this.removeEventListener(event.type, entry.listener);
      }
    },
  };
  const window = {
    startiapp: sdk,
    fetch: fetchImpl,
    setTimeout(callback) {
      const id = nextTimerId += 1;
      timers.set(id, callback);
      return id;
    },
    clearTimeout(id) {
      timers.delete(id);
    },
  };
  vm.runInNewContext(source, {
    document,
    window,
    Promise,
    Error,
    Event: class Event {
      constructor(type) {
        this.type = type;
      }
    },
  });
  return { timers };
}

async function settle() {
  await new Promise(setImmediate);
  await new Promise(setImmediate);
}

test("registers the opaque identity after one native initialization", async () => {
  let initializeCalls = 0;
  let registeredId = "";
  runBridge({
    dataset: { startiappMode: "authenticated", startiappUserId: "opaque-account-id" },
    sdk: {
      initialize: async () => { initializeCalls += 1; },
      isRunningInApp: () => true,
      User: { registerId: async (value) => { registeredId = value; } },
    },
  });
  await settle();
  assert.equal(initializeCalls, 1);
  assert.equal(registeredId, "opaque-account-id");
});

test("initializes after the native bridge emits its late ready event", async () => {
  let readyListener;
  let initialized = 0;
  let registeredId = "";
  let runningInApp = false;
  runBridge({
    dataset: { startiappMode: "authenticated", startiappUserId: "opaque-account-id" },
    sdk: {
      addEventListener: (event, listener) => {
        if (event === "ready") readyListener = listener;
      },
      initialize: async () => { initialized += 1; },
      isRunningInApp: () => runningInApp,
      User: { registerId: async (value) => { registeredId = value; } },
    },
  });
  assert.equal(typeof readyListener, "function");
  runningInApp = true;
  readyListener();
  await settle();
  assert.equal(initialized, 1);
  assert.equal(registeredId, "opaque-account-id");
});

test("completes native credential storage before acknowledging the server", async () => {
  const calls = [];
  runBridge({
    dataset: {
      startiappMode: "authenticated",
      startiappCompleteBiometricSave: "true",
      startiappCompleteBiometricSaveUrl: "/internal/biometric-save/",
    },
    sdk: {
      initialize: async () => {},
      isRunningInApp: () => true,
      Biometrics: {
        endSaveUsernameAndPassword: async () => { calls.push("native"); },
      },
    },
    fetchImpl: async () => {
      calls.push("server");
      return { json: async () => ({ ok: true }) };
    },
  });
  await settle();
  assert.deepEqual(calls, ["native", "server"]);
});

test("does not acknowledge the server when native credential storage fails", async () => {
  let serverCalls = 0;
  runBridge({
    dataset: {
      startiappMode: "authenticated",
      startiappCompleteBiometricSave: "true",
      startiappCompleteBiometricSaveUrl: "/internal/biometric-save/",
    },
    sdk: {
      initialize: async () => {},
      isRunningInApp: () => true,
      Biometrics: {
        endSaveUsernameAndPassword: async () => { throw new Error("native failure"); },
      },
    },
    fetchImpl: async () => {
      serverCalls += 1;
      return { json: async () => ({ ok: true }) };
    },
  });
  await settle();
  assert.equal(serverCalls, 0);
});

test("removes device credentials and unregisters the identity after logout", async () => {
  let credentialsRemoved = false;
  let identityUnregistered = false;
  runBridge({
    dataset: { startiappMode: "logout" },
    sdk: {
      initialize: async () => {},
      isRunningInApp: () => true,
      Biometrics: {
        removeUsernameAndPassword: async () => { credentialsRemoved = true; },
      },
      User: {
        unregisterId: async () => { identityUnregistered = true; },
      },
    },
  });
  await settle();
  assert.equal(credentialsRemoved, true);
  assert.equal(identityUnregistered, true);
});

test("reports unavailable native push without failing the notification center", async () => {
  let clickListener;
  const status = { textContent: "" };
  runBridge({
    dataset: { startiappMode: "authenticated" },
    sdk: { initialize: async () => {}, isRunningInApp: () => true },
    elements: {
      "[data-startiapp-push-enable]": {
        addEventListener: (event, listener) => {
          if (event === "click") clickListener = listener;
        },
      },
      "[data-startiapp-push-status]": status,
    },
  });
  await settle();
  await clickListener();
  assert.equal(status.textContent, "Pushnotifikationer er kun tilgængelige i Polsk App.");
});

test("falls back safely when optional native modules are absent", async () => {
  runBridge({
    dataset: { startiappMode: "login" },
    sdk: { initialize: async () => {}, isRunningInApp: () => true },
  });
  await settle();
  assert.ok(true);
});
