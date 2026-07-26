(() => {
  "use strict";

  const body = document.body;
  const INITIALIZATION_TIMEOUT_MS = 5_000;
  const READY_FALLBACK_MS = 250;
  const LIGHT_SYSTEM_BAR_COLOR = "#f7f8fa";
  const DARK_SYSTEM_BAR_COLOR = "#101828";
  let initializationPromise;
  let nativeInitializationPromise;
  let nativeInitialized = false;
  let readyListenerAttached = false;

  function starti() {
    return window.startiapp || null;
  }

  function withTimeout(promise, message) {
    return new Promise((resolve, reject) => {
      const timeoutId = window.setTimeout(
        () => reject(new Error(message)),
        INITIALIZATION_TIMEOUT_MS
      );
      Promise.resolve(promise).then(
        (value) => { window.clearTimeout(timeoutId); resolve(value); },
        (error) => { window.clearTimeout(timeoutId); reject(error); }
      );
    });
  }

  function isRunningInApp(sdk) {
    try {
      return Boolean(
        sdk && typeof sdk.isRunningInApp === "function" && sdk.isRunningInApp()
      );
    } catch (_) {
      return false;
    }
  }

  function notifyNativeInitialized() {
    document.dispatchEvent(new Event("startiapp:initialized"));
  }

  function currentThemeIsDark() {
    return document.documentElement.dataset.theme === "dark";
  }

  function nativeChromeOptions() {
    const isDark = currentThemeIsDark();
    return {
      darkContent: !isDark,
      safeAreaColor: isDark ? DARK_SYSTEM_BAR_COLOR : LIGHT_SYSTEM_BAR_COLOR,
    };
  }

  function initializeOptions() {
    // Starti exposes the native insets as --startiapp-inset-* when the safe
    // areas are removed. The shared shell then owns the matching padding,
    // which keeps the header and bottom navigation clear of device chrome.
    const chrome = nativeChromeOptions();
    return {
      statusBar: {
        removeSafeArea: true,
        hideText: false,
        darkContent: chrome.darkContent,
      },
    };
  }

  function configureNativeChrome(sdk) {
    document.documentElement.dataset.startiappNative = "true";

    const app = sdk && sdk.App;
    if (!app) return;
    const chrome = nativeChromeOptions();

    // Starti merges runtime status-bar updates. Match both the safe-area
    // background and icon contrast to the current presentation theme.
    try {
      if (typeof app.setStatusBar === "function") {
        app.setStatusBar({ darkContent: chrome.darkContent });
      }
    } catch (_) {}
    try {
      if (typeof app.setSafeAreaBackgroundColor === "function") {
        Promise.resolve(app.setSafeAreaBackgroundColor(chrome.safeAreaColor)).catch(() => {});
      }
    } catch (_) {}
  }

  function attemptNativeInitialization(sdk) {
    if (nativeInitialized) return Promise.resolve(sdk);
    if (nativeInitializationPromise) return nativeInitializationPromise;

    nativeInitializationPromise = withTimeout(
      Promise.resolve().then(() => sdk.initialize(initializeOptions())),
      "StartiApp initialization timed out."
    ).then(() => {
      if (!isRunningInApp(sdk)) return null;
      nativeInitialized = true;
      configureNativeChrome(sdk);
      notifyNativeInitialized();
      return sdk;
    }).catch(() => null).finally(() => {
      if (!nativeInitialized) nativeInitializationPromise = undefined;
    });
    return nativeInitializationPromise;
  }

  function initialize() {
    if (nativeInitialized) return Promise.resolve(starti());
    if (initializationPromise) return initializationPromise;
    const sdk = starti();
    if (!sdk || typeof sdk.initialize !== "function") return Promise.resolve(null);

    initializationPromise = new Promise((resolve) => {
      let settled = false;
      let fallbackTimer;
      let terminalTimer;
      const finish = (value) => {
        if (settled) return;
        settled = true;
        if (fallbackTimer) window.clearTimeout(fallbackTimer);
        if (terminalTimer) window.clearTimeout(terminalTimer);
        document.removeEventListener("startiapp:initialized", initialized);
        resolve(value);
      };
      const initialized = () => finish(sdk);
      const runInitialization = () => {
        attemptNativeInitialization(sdk).then((readySdk) => {
          if (readySdk) finish(readySdk);
        });
      };

      document.addEventListener("startiapp:initialized", initialized, { once: true });
      if (typeof sdk.addEventListener === "function" && !readyListenerAttached) {
        try {
          sdk.addEventListener("ready", runInitialization);
          readyListenerAttached = true;
        } catch (_) {
          // The browser path remains fully functional when the optional bridge fails.
        }
      }

      if (isRunningInApp(sdk)) {
        runInitialization();
      } else {
        fallbackTimer = window.setTimeout(() => {
          if (isRunningInApp(sdk)) runInitialization();
        }, READY_FALLBACK_MS);
      }
      terminalTimer = window.setTimeout(() => finish(null), INITIALIZATION_TIMEOUT_MS);
    }).finally(() => {
      if (!nativeInitialized) initializationPromise = undefined;
    });
    return initializationPromise;
  }

  async function registerIdentity(sdk) {
    const identity = body.dataset.startiappUserId;
    if (!identity || !sdk.User || typeof sdk.User.registerId !== "function") return false;
    try {
      await sdk.User.registerId(identity);
      return true;
    } catch (_) {
      return false;
    }
  }

  async function setupLogin(sdk) {
    const biometrics = sdk.Biometrics;
    const form = document.querySelector("[data-startiapp-login-form]");
    const biometricButton = document.querySelector("[data-startiapp-biometric-login]");
    const armed = document.querySelector("[data-startiapp-capture-armed]");
    const usernameSelector = body.dataset.startiappUsernameSelector;
    const passwordSelector = body.dataset.startiappPasswordSelector;
    const submitSelector = body.dataset.startiappSubmitSelector;
    if (!biometrics || !form || !armed || !usernameSelector || !passwordSelector || !submitSelector) return;
    if (typeof biometrics.startSaveUsernameAndPassword === "function") {
      try {
        await biometrics.startSaveUsernameAndPassword({
          usernameInputFieldSelector: usernameSelector,
          passwordInputFieldSelector: passwordSelector,
          submitButtonSelector: submitSelector,
          title: "Gem login",
          reason: "Gem dine oplysninger til næste gang",
          language: "da",
        });
        form.addEventListener("submit", () => { armed.value = "1"; }, { once: true });
      } catch (_) {
        return;
      }
    }
    if (!biometricButton || typeof biometrics.hasUsernameAndPassword !== "function" || typeof biometrics.getUsernameAndPassword !== "function") return;
    try {
      if (!await biometrics.hasUsernameAndPassword()) return;
      biometricButton.hidden = false;
      biometricButton.addEventListener("click", async () => {
        const credentials = await biometrics.getUsernameAndPassword("Log ind", "Bekræft for at fortsætte");
        if (!credentials) return;
        document.querySelector(usernameSelector).value = credentials.username;
        document.querySelector(passwordSelector).value = credentials.password;
        form.requestSubmit();
      });
    } catch (_) {
      biometricButton.hidden = true;
    }
  }

  async function completeCredentialSave(sdk) {
    if (body.dataset.startiappCompleteBiometricSave !== "true") return;
    const url = body.dataset.startiappCompleteBiometricSaveUrl;
    if (!url || !sdk.Biometrics || typeof sdk.Biometrics.endSaveUsernameAndPassword !== "function") return;
    try {
      await withTimeout(
        Promise.resolve().then(() => sdk.Biometrics.endSaveUsernameAndPassword()),
        "StartiApp credential save timed out."
      );
      const response = await window.fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrfToken() },
      });
      await response.json();
    } catch (_) {
      // Device credentials are optional; Django authentication remains authoritative.
    }
  }

  function csrfToken() {
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function setupPushButton(sdk) {
    const button = document.querySelector("[data-startiapp-push-enable]");
    const status = document.querySelector("[data-startiapp-push-status]");
    if (!button || !status) return;
    button.addEventListener("click", async () => {
      const push = sdk.PushNotification;
      if (!push || typeof push.requestAccess !== "function") {
        status.textContent = "Pushnotifikationer er kun tilgængelige i Polsk App.";
        return;
      }
      try {
        const permission = await push.requestAccess();
        const registered = permission && permission.granted && await registerIdentity(sdk);
        status.textContent = registered ? "Pushnotifikationer er aktiveret." : "Tilladelsen blev ikke givet.";
      } catch (_) {
        status.textContent = "Pushnotifikationer kunne ikke aktiveres lige nu.";
      }
    });
  }

  function showNativeCredit(sdk) {
    const credit = document.querySelector("[data-startiapp-credit]");
    if (credit && isRunningInApp(sdk)) credit.hidden = false;
  }

  function showNativePushControl(sdk) {
    const control = document.querySelector("[data-startiapp-push-control]");
    if (control && isRunningInApp(sdk)) control.hidden = false;
  }

  async function setupLogout(sdk) {
    const biometrics = sdk.Biometrics;
    if (biometrics && typeof biometrics.removeUsernameAndPassword === "function") {
      try { await biometrics.removeUsernameAndPassword(); } catch (_) {}
    }
    if (sdk.User && typeof sdk.User.unregisterId === "function") {
      try { await sdk.User.unregisterId(); } catch (_) {}
    }
  }

  function setupMode(sdk) {
    if (body.dataset.startiappSetupState === "complete") return;
    body.dataset.startiappSetupState = "complete";
    if (!sdk) return;
    showNativeCredit(sdk);
    if (body.dataset.startiappMode === "login") setupLogin(sdk);
    if (body.dataset.startiappMode === "authenticated") {
      registerIdentity(sdk);
      completeCredentialSave(sdk);
      showNativePushControl(sdk);
      setupPushButton(sdk);
    }
    if (body.dataset.startiappMode === "logout") setupLogout(sdk);
  }

  function startSetup() {
    const setupAfterLateReady = () => setupMode(starti());
    document.addEventListener("startiapp:initialized", setupAfterLateReady, { once: true });
    document.addEventListener("polsk:themechange", () => {
      if (nativeInitialized) configureNativeChrome(starti());
    });
    initialize().then((sdk) => {
      if (!sdk) return;
      document.removeEventListener("startiapp:initialized", setupAfterLateReady);
      setupMode(sdk);
    });
  }

  startSetup();
})();
