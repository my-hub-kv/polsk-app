# ADR 0004: Provider-neutral configuration

Status: Accepted
Date: 2026-07-24

## Context

Public source must not become an operational runbook or expose account details.

## Decision

Domain/application code uses generic adapters and environment variables. Public documentation avoids operational account details; narrow deployment files or external systems retain provider configuration. Provider identity is not a security boundary.

## Consequences

Provider replacement remains feasible without copying operational details into product docs.

## Alternatives considered

Embedding provider-specific workflows broadly in source was rejected.
