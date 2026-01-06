# Platform service overview

This Flask app serves multiple client frontends and a small set of backend data
files per client, using each client's `msn_<user>.json` manifest to decide what
to load.

- `data_access.py` determines the client slug from the request host, loads that
  client's manifest, exposes the default entry HTML, and provides the whitelist
  of backend data files the API may read or write.
- `app.py` wires these utilities into Flask routes: it uses the manifest to
  serve the correct frontend files and restricts backend data access to the
  whitelisted filenames from the manifest.

The combination keeps routing and file I/O bounded to what each client declares
in their manifest while allowing host-based multi-tenant serving.

## Layout
```txt
srv/webapps/platform/
├── app.py              # Flask application entry point
├── data_access.py      # Client/manifest helpers:contentReference[oaicite:4]{index=4}
├── data/               # <--- NEW: global data (taxonomy/product types)
│   ├── taxonomy.json
│   └── product_type.json
├── modules/            # API blueprints exposed to clients
│   ├── donation_receipts.py
│   ├── weather.py
│   └── catalog.py      # <--- NEW: exposes taxonomy & product types
└── services/           # (optional) internal helpers/integrations, not directly exposed
    └── newsletter.py   # e.g. SES ingestion and sending
```

- Everything in modules/ contains a Flask Blueprint registered under /api/ that clients can call.
- Everything in services/ contains helper functions or long‑running tasks (e.g. sending newsletters, polling POS systems). They are imported from blueprints or Celery tasks, not exposed over HTTP.
- The new data/ directory holds platform‑wide JSON that can be read by any blueprint.

## After adding multi-tenant data acess

From any client domain a query can target the global taxonomy and product types:
`GET https://<client-domain>/api/taxonomy` → returns the JSON contents of taxonomy.json.
`GET https://<client-domain>/api/product-types` → returns the JSON contents of product_type.json.

If you decide later that clients should not see the entire taxonomy, you can move the blueprint into an internal package and restrict access by origin or authentication. For now, the above approach keeps the data read‑only and globally available.
