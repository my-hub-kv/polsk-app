(() => {
  "use strict";

  const navigationSelector = ".desktop-navigation-link, .mobile-navigation-link";
  let mobileMenuTrigger = null;

  function mobileMenu() {
    return document.querySelector("[data-mobile-shell-menu-modal]");
  }

  function closeMobileMenu() {
    const menu = mobileMenu();
    if (!menu) return;
    menu.hidden = true;
    document.body.classList.remove("shell-modal-open");
    if (mobileMenuTrigger) {
      mobileMenuTrigger.setAttribute("aria-expanded", "false");
      mobileMenuTrigger.focus({ preventScroll: true });
    }
  }

  function openMobileMenu(trigger) {
    const menu = mobileMenu();
    if (!menu) return;
    mobileMenuTrigger = trigger;
    menu.hidden = false;
    document.body.classList.add("shell-modal-open");
    trigger.setAttribute("aria-expanded", "true");
    const closeButton = menu.querySelector("[data-mobile-shell-menu-close]");
    if (closeButton) closeButton.focus({ preventScroll: true });
  }

  function isPlainNavigationClick(event, link) {
    if (event.defaultPrevented || event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    if (link.target && link.target !== "_self") return false;
    if (link.hasAttribute("download")) return false;
    const destination = new URL(link.href, window.location.href);
    return destination.origin === window.location.origin && destination.href !== window.location.href;
  }

  function startPageLoading() {
    document.documentElement.dataset.pageLoading = "true";
  }

  function markNavigationPending(link) {
    const href = link.getAttribute("href");
    if (!href) return;
    document.querySelectorAll(navigationSelector).forEach((candidate) => {
      const matchesDestination = candidate.getAttribute("href") === href;
      candidate.classList.toggle("is-pending", matchesDestination);
      candidate.classList.toggle("is-active", matchesDestination);
      if (matchesDestination) {
        candidate.setAttribute("aria-current", "page");
        candidate.setAttribute("aria-busy", "true");
      } else {
        candidate.removeAttribute("aria-current");
        candidate.removeAttribute("aria-busy");
      }
    });
  }

  function clearPendingNavigation() {
    document.querySelectorAll(`${navigationSelector}.is-pending`).forEach((link) => {
      link.classList.remove("is-pending");
      link.removeAttribute("aria-busy");
    });
  }

  document.addEventListener("click", (event) => {
    const openTrigger = event.target.closest("[data-mobile-shell-menu-open]");
    if (openTrigger) {
      event.preventDefault();
      openMobileMenu(openTrigger);
      return;
    }

    if (event.target.closest("[data-mobile-shell-menu-close]")) {
      event.preventDefault();
      closeMobileMenu();
      return;
    }

    const menuAction = event.target.closest(
      "[data-mobile-shell-menu-modal] a, [data-mobile-shell-menu-modal] button[type='submit']",
    );
    if (menuAction) closeMobileMenu();

    const navigationLink = event.target.closest(navigationSelector);
    if (navigationLink && isPlainNavigationClick(event, navigationLink)) {
      markNavigationPending(navigationLink);
      startPageLoading();
      return;
    }

    const pageLink = event.target.closest("a[href]");
    if (pageLink && isPlainNavigationClick(event, pageLink)) {
      startPageLoading();
    }
  });

  document.addEventListener("submit", (event) => {
    const form = event.target.closest("form[data-submit-feedback]");
    if (!form || event.defaultPrevented || form.dataset.submitting === "true") return;
    const submitButton = form.querySelector("button[type='submit']");
    if (!submitButton) return;
    form.dataset.submitting = "true";
    submitButton.disabled = true;
    submitButton.dataset.loading = "true";
    submitButton.textContent = form.dataset.submittingLabel || "Gemmer…";
    const status = form.querySelector("[data-submission-status]");
    if (status) status.hidden = false;
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && mobileMenu() && !mobileMenu().hidden) {
      closeMobileMenu();
    }
  });

  window.addEventListener("pageshow", () => {
    clearPendingNavigation();
    delete document.documentElement.dataset.pageLoading;
  });
})();
