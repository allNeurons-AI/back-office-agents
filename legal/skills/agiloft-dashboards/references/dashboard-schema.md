# Dashboard data schema

Used at Step 6. Edit only the `DATA` block near the bottom of `assets/dashboard_template.html`. The page above it (styles, chart engine) and the small bootstrap script after it are not changed. Every text value is HTML-escaped by the engine, so text extracted from documents cannot run as markup. Links render only for full `https://` URLs; anything else is plain text.

```
meta: {
  sourceName,                 // brand label in the top bar: "Agiloft", "SharePoint", the system's name
  instance,                   // the exact source: instance, site, and file / list / folder
  kb,                         // optional: knowledge base or library
  area,                       // sub-title, default "Contract Management"
  user,                       // top-right label, optional
  account,                    // whose view: the signed-in account
  checked,                    // when the data was read
  records,                    // "Based on" line: how many rows or files
  docsRead,                   // document sources only: "50 of 212 (cap 50)"
  mapped                      // "Status -> in flight / in force / closed"
}
active: "reporting" | "requester" | "cycletimes" | "vendor"
dashboards: { reporting, requester, cycletimes, vendor }   // always all four
  each: { name, filters: [{label, value}], tiles: [{ label, value, tone: "teal"|"purple"|"red", note }],
          cards: [...], caveat }
card: { title, type, span: 2|3, source, options }
  "donut" | "pie":  data: [{ label, value }]               options: { centre }
  "bar":            data: [{ label, value }] or [{ label, values: { series: n } }]
                    options: { series: [...], stacked, xLabel, legend }
  "area":           data as bar; options: { series: [...], xLabel }
  "table":          data: { columns: [...], rows: [[...]], note }
  "links":          data: [{ label, url? }]                  // url only if you have seen it
  "empty":          data: { message }                        // say why there is no figure
source (on every card): { query, records, widget?, widgetValue?, differs?, note? }
```

For a SharePoint or file source, `query` is the filter in plain words plus the file and sheet, `records` is the row or file count, and `note` carries "extracted from document" where values came from reading text. Leave `widget`, `widgetValue` and `differs` out unless the source has a report that covers the panel.

Default tab names: "Contract Reporting Dashboard", "Contract Requester Dashboard", "Cycle Times Reporting Dashboard", "Vendor Management". Use the customer's own names if they gave them.

Publish with the Artifact tool: copy the template to `contract-dashboard.html`, edit the DATA block, publish with the same path every time so the URL stays the same. The template has no doctype or body tags; the Artifact tool adds the page skeleton.
