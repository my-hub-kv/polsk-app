# Weather history

**Product rules: Confirmed. Data and adapter design: Candidate. Implementation: Planned.**

Event location may change by year. A forecast snapshot has fetch/issue time and applies to a location/date; observed weather is separate. Historical UI distinguishes forecast from actual. Unavailable data and adapter failures degrade gracefully; later manual correction/import may be supported. Weather informs suggestions but never orders.
