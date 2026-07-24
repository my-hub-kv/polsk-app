# ADR 0002: Server-rendered frontend

Status: Accepted
Date: 2026-07-24

## Context

The product needs a fast, coherent, mobile-first interface without separate frontend operations.

## Decision

Use Django templates, HTMX, Alpine.js, and Tailwind; do not build an SPA or separate frontend.

## Consequences

Server-side validation and rendering remain central; client enhancement stays narrow.

## Alternatives considered

A separate SPA was rejected as disproportionate.
