# ADR 0003: Person and login separation

Status: Accepted
Date: 2026-07-24

## Context

Children need durable profiles before independent login, and household adults may act for children.

## Decision

Participant identity is separate from login credentials; audit distinguishes acting account and active participant.

## Consequences

Later independent credentials do not lose history, but authorization must handle both identities explicitly.

## Alternatives considered

Using a login account as the participant identity was rejected.
