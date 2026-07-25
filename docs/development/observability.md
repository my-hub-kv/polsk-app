# Error logging and observability

**Baseline status: Implemented for Django request errors and browser runtime errors.** The application writes safe error information to standard error; the deployment platform captures that output in its service log explorer. This repository does not use an external error-monitoring service.

## Server-side errors

`config/settings.py` sends Django request and security errors, application errors, and other warning-or-higher Python logs to the console. Unhandled Django request exceptions therefore retain their traceback in the platform log. Application code uses `logging.getLogger(__name__)`; when catching an expected exception at a boundary, log it once with `logger.exception()` only when the traceback is useful, then return a safe Danish error. Do not catch an exception merely to log and re-raise it when Django will already log the same failure.

The production health endpoint reports availability, not every application error. Deployment failure and unhealthy-service notifications are configured outside the repository. Search the platform log explorer by timestamp, error level, safe route information, and request ID where available.

## Browser errors

`apps/core/static/core/client-error-reporting.js` installs global listeners for runtime `error` and `unhandledrejection` events. It sends a small same-origin JSON report to `POST /internal/client-errors/`; that endpoint keeps Django CSRF protection, accepts only the expected report kinds, bounds all text, records only a path without a query string, and writes one application error log. It does not persist reports in the database.

The current homepage uses `ensure_csrf_cookie` and loads this script. Every future base template must load the script once and ensure Django provides a CSRF cookie before browser errors need reporting. Errors that occur before the script loads, inside browser extensions, or when the browser cannot reach the application cannot be captured by this mechanism.

## Privacy and safe context

Never put a token, cookie, authorization header, request body, form value, private message, phone number, dietary information, email address, or full URL/query string into a log or client error report. Do not attach browser storage, DOM contents, screenshots, user-agent strings, stack traces, or arbitrary exception objects. Custom JavaScript errors must not build their message from participant data.

Useful safe context is the error kind, bounded message, same-origin script path, line/column, page path, and platform request ID when supplied. If a future debugging need requires more context, document the field, privacy risk, retention, and authorization boundary before adding it.

## Operational workflow

1. Enable service failure notifications in the deployment platform.
2. Investigate a reported failure in the service log explorer using the timestamp and error level.
3. Reproduce with synthetic data locally; do not inspect hosted databases or production personal data.
4. Add a regression test, fix the root cause, and record any new durable behaviour or risk in the relevant documentation.

Platform log retention and any external log-stream destination are operational decisions maintained outside this public repository. Do not treat logs as a long-term audit store.
