# Design spec: agiloft-dashboards

Layout and style rules for the dashboard page. The renderer is `assets/dashboard_template.html`; the data format is `references/dashboard-schema.md`.

## Required sections (in order)
1. Top bar with the source name, then a footer line with source, account, checked at, records, documents read (document sources) and mapped columns; a caveat banner if any.
2. Tab bar with four tabs: Contract Reporting Dashboard, Contract Requester Dashboard, Cycle Times Reporting Dashboard, Vendor Management. Use the customer's own labels when given.
3. Per tab: tile row, then a three-column card grid (cards span 1, 2 or 3 columns).
4. Every card ends with a source line.

## Style
- Light and dark themes follow the viewer's setting; colours are tokens, so a re-skin changes one block. Fifteen chart colours that stay distinguishable, never colour alone: legends and tooltips carry the label.
- Tile tones: in flight teal, in force purple, closed red, total none.
- Layout is three columns, two below 62rem and one below 40rem.

## Missing data
Show the card as `empty` with the reason. Never leave a blank box or drop the card.
