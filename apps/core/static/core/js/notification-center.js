(() => {
  "use strict";
  const token = document.cookie
    .split("; ")
    .find((value) => value.startsWith("csrftoken="))
    ?.split("=")[1];
  if (!token) return;
  fetch("/notifikationer/%C3%A5bnet/", {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-CSRFToken": token },
  }).catch(() => {
    // The inbox remains usable if the optional read-state update fails.
  });
})();
