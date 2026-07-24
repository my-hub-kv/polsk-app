# ADR 0004: Provider-neutral configuration

Status: Accepted
Date: 2026-07-24

## Context

Public source must not become an operational runbook or expose account details.

## Decision

Domain/application code uses generic adapters and environment variables. Public documentation avoids operational account details; narrow deployment files or external systems retain provider configuration. The application uses `APP_HOST` and `APP_ORIGIN` for its public host and origin, while scheduled checks read `APP_BASE_URL` from a repository variable rather than a committed URL. Provider identity is not a security boundary.

## Consequences

Provider replacement remains feasible without copying operational details into product docs. Existing deployment-specific environment variables may be supported temporarily as compatibility fallbacks while their generic replacements are configured.

## Alternatives considered

Embedding provider-specific workflows broadly in source was rejected.
