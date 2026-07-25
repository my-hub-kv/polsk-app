(() => {
  "use strict";

  const endpoint = "/internal/client-errors/";
  const maximumMessageLength = 300;

  function csrfToken() {
    const cookie = document.cookie
      .split("; ")
      .find((value) => value.startsWith("csrftoken="));

    return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
  }

  function boundedText(value) {
    if (typeof value !== "string") {
      return "";
    }

    return value.replace(/\s+/g, " ").trim().slice(0, maximumMessageLength);
  }

  function localPath(value) {
    if (typeof value !== "string" || !value) {
      return "";
    }

    try {
      const url = new URL(value, window.location.origin);
      return url.origin === window.location.origin ? url.pathname : "external";
    } catch {
      return "";
    }
  }

  function report(payload) {
    const token = csrfToken();
    if (!token) {
      return;
    }

    fetch(endpoint, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": token,
      },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {
      // Error reporting must not create another user-visible error.
    });
  }

  window.addEventListener(
    "error",
    (event) => {
      if (!(event instanceof ErrorEvent)) {
        return;
      }

      report({
        kind: "error",
        message: boundedText(event.message) || "Unknown client error",
        source: localPath(event.filename),
        line: Number.isInteger(event.lineno) ? event.lineno : 0,
        column: Number.isInteger(event.colno) ? event.colno : 0,
        page: window.location.pathname,
      });
    },
    true,
  );

  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    const message = reason instanceof Error ? reason.message : "Unhandled promise rejection";

    report({
      kind: "unhandledrejection",
      message: boundedText(message) || "Unhandled promise rejection",
      source: "",
      line: 0,
      column: 0,
      page: window.location.pathname,
    });
  });
})();
