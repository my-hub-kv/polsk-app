# Commenting and code documentation

Code is part of Polsk App’s technical documentation, but it does not replace product, domain, or ADR documentation. Keep durable product rules in `docs/`; use code comments to make local reasoning and non-obvious constraints maintainable.

## Comments

- Explain **why**, a security/privacy boundary, a domain invariant, a performance trade-off, or an intentionally surprising choice. Do not restate what readable code already says.
- Place a comment immediately next to the decision it explains. Write complete, current sentences and remove comments that become false after a change.
- Link to an ADR, domain document, or issue only when it gives a future maintainer useful context. Do not paste conversation transcripts or private reasoning into code.
- Use `TODO` only with a concrete follow-up issue/reference and an actionable condition; do not leave vague future-work comments.
- Comments must not contain secrets, personal data, production URLs, or operational account details.

## Docstrings

- Add docstrings to public modules/classes and non-obvious public functions, services, selectors, management commands, and adapter interfaces.
- Start with a concise summary, then document meaningful inputs, return value, side effects, exceptions, authorization assumptions, or invariants when they are not clear from type hints and naming.
- Do not write docstrings for trivial getters, obvious framework wiring, or code whose behaviour is already clear from a focused name and signature.
- Update the docstring in the same change as a behaviour change; stale documentation is worse than no documentation.

## When documentation belongs outside code

- Product behaviour and user promises: `docs/product/`.
- Data lifecycle and invariants: `docs/domain/`.
- Technical trade-offs: an ADR.
- Local implementation details and contracts: code comments/docstrings.

When a domain becomes implemented, update its durable domain document with a short, code-grounded current-behaviour note: relevant app/module entry points, important invariants, known risks, and useful test starting points. Do not put ticket-specific plans or unresolved proposals in that note.

When code and documentation disagree, stop and resolve the conflict rather than silently choosing one.
