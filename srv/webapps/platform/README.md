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
