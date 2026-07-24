# Coding standards

Use English source identifiers and Danish visible text. Follow PEP 8 and existing tooling; use type hints for public/non-obvious code. Keep views thin, validate with forms/explicit validation, put state changes in services, reusable reads in QuerySets/selectors, and important invariants in constraints/transactions.

Avoid generic utils dumping grounds, central signal workflows, premature abstractions, and dependencies without approval. Use timezone-aware datetimes, accessible semantic mobile-first templates, HTMX only for useful interactions, and Alpine only for small local state. Log safely, return structured actionable errors, explain *why* in comments, document public/non-obvious behaviour, and keep changes small/reviewable.
