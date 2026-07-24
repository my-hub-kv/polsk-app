# Shopping lists

**Product rules: Confirmed. Suggestion and export design: Candidate. Implementation: Planned.**

Shopping requests, suggested items, list lines, delivery days, optional vendor-product mappings, export snapshots/status, list status, and change-after-export detection are event-year concepts. Suggestions are explainable and advisory: for example, low verified stock, reservations, warm forecast, historical warm-day usage, or an item already pending.

No suggestion orders automatically. CSV exports use known encoding, correct escaping, formula-injection neutralisation where appropriate, and tests for delimiters, quotes, line breaks, Danish characters, and empty fields. Exports contain synthetic examples only and omit secrets/internal IDs unless deliberately needed by an approved vendor template. Exact dialect remains configurable.
