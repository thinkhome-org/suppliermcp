---
name: offer-comparison
description: Use when comparing supplier offers for individual products, including quantity, packaging, last-known prices, and freshness uncertainty.
---

# Compare individual product offers

Ask for the requested quantity if it is missing. Use `compare_offers` with product IDs and quantities; each product is a separate comparison, not a basket optimization.

- Do not merge unresolved variants or packaging based on similar names. Inspect supplier identities and evidence with `get_product`.
- Show requested and orderable quantity. Do not silently approve a rounded order quantity. Different orderable quantities or currencies do not establish a common cheapest offer.
- Quote net prices, explicitly identify included known fees, and disclose that shipping and VAT are excluded from the comparison total. Unknown fees, order multiples or discount formulas mean the payable total is unknown; never substitute zero.
- Distinguish `last_known_winner` from `fresh_winner`. Show evidence time and refresh failures. A newly downloaded unchanged export is not fresh evidence of a price.
- `refresh=true` queues a read, then returns cached evidence. `refresh_pending` is not a completed refresh. Recheck status before claiming a verified price.
- If fields contradict each other, call out the contradiction and withhold a cheapest claim. A cheap stale offer can be shown with its limitations; it must not become a fresh recommendation by omission.

Use supplier data only. Do not research manufacturer websites, read account orders/invoices, place orders, or claim a purchase occurred. No write tools exist.
