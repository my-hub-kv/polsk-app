# Shopping lists

**Product rules: Confirmed. Suggestion and export design: Candidate. Implementation: Planned.**

Shopping requests, suggested items, list lines, delivery days, optional vendor-product mappings, export snapshots/status, list status, and change-after-export detection are event-year concepts. A coordinator may add a request to a list, dismiss it, edit its text, quantity, or unit, and merge duplicates. Lists are planned for a delivery day or delivery period, so each purchase covers the next period rather than the entire event. Suggestions are explainable and advisory: for example, low verified stock, reservations, warm forecast, historical warm-day usage, or an item already pending.

The baseline export fields are product name, optional vendor product number, quantity, unit, delivery date, category, purpose, reserved dinner/box/label, packing or handling note, and general comment. Exact column order, delimiter, encoding, and vendor-specific templates remain configurable.

No suggestion orders automatically. CSV exports use the configured encoding, correct escaping, formula-injection neutralisation where appropriate, and tests for delimiters, quotes, line breaks, Danish characters, and empty fields. Exports contain synthetic examples only and omit secrets/internal IDs unless deliberately needed by an approved vendor template.
