# ADR 0001: Modular Django monolith

Status: Accepted
Date: 2026-07-24

## Context

The product is small and its domains are still emerging.

## Decision

Use one modular Django application and one PostgreSQL database; do not use microservices at this scale.

## Consequences

Deployment and shared infrastructure stay simple; explicit app boundaries remain important.

## Alternatives considered

Separate services were rejected as premature complexity.
