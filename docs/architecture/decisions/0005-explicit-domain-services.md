# ADR 0005: Explicit domain services

Status: Accepted
Date: 2026-07-24

## Context

Planning, transfers, stock correction, and notifications span models and permissions.

## Decision

Use explicit service functions for multi-model workflows; keep views thin, avoid primary-workflow signals, and protect state transitions with transactions.

## Consequences

Important business operations are discoverable and testable.

## Alternatives considered

Signal-driven and view-embedded workflow logic were rejected.
