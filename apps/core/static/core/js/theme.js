(() => {
  "use strict";

  const storageKey = "polsk-theme";
  const root = document.documentElement;
  const controls = document.querySelectorAll("[data-theme-toggle]");
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

  function currentTheme() {
    return root.dataset.theme === "dark" ? "dark" : "light";
  }

  function updateControls() {
    const isDark = currentTheme() === "dark";
    controls.forEach((control) => {
      control.setAttribute("aria-pressed", String(isDark));
      control.setAttribute(
        "aria-label",
        isDark ? "Skift til lyst tema" : "Skift til mørkt tema",
      );
      const label = control.querySelector("[data-theme-toggle-label]");
      if (label) {
        label.textContent = isDark ? "Brug lyst tema" : "Brug mørkt tema";
      }
    });
  }

  function setTheme(theme, persist) {
    root.dataset.theme = theme;
    if (persist) {
      try {
        window.localStorage.setItem(storageKey, theme);
      } catch (_) {
        // A theme preference is optional and must not affect app use.
      }
    }
    updateControls();
  }

  controls.forEach((control) => {
    control.addEventListener("click", () => {
      setTheme(currentTheme() === "dark" ? "light" : "dark", true);
    });
  });

  mediaQuery.addEventListener("change", (event) => {
    try {
      if (!window.localStorage.getItem(storageKey)) {
        setTheme(event.matches ? "dark" : "light", false);
      }
    } catch (_) {
      setTheme(event.matches ? "dark" : "light", false);
    }
  });

  updateControls();
})();
