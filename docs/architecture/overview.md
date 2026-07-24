# Architecture overview

Polsk App is one deployable modular Django monolith with one PostgreSQL database, Django sessions/authentication, server-rendered templates, targeted HTMX enhancement, small Alpine components, and Tailwind styling. Provider-neutral adapters isolate external weather, push, and email integrations. When asynchronous delivery exists, database-backed durable notification/outbox concepts protect domain state.

This suits roughly 40–50 participants and prioritises maintainability over a frontend/backend split, microservices, or Docker.
