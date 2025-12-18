# web-dir-ctv
This repository contains the static website for cuyahogaterravita.com.
It is served by NGINX directly from the server at:
```html
/srv/webapps/clients/cuyahogaterravita.com/frontend/
```
This repository includes:
	•	HTML, CSS, JS (static assets only)
	•	Images, icons, and supporting website media
	•	The client manifest file: msn_<userId>.json
	•	Optional data files under data/ used by the shared backend (CSV/JSON)

This repo does not contain backend code. It works together with a shared Flask application hosted in a separate repository.

## How This Frontend Works With the Backend

### 1. Served by NGINX
	• NGINX serves this directory exactly as-is.
	• There is no build step or server-side rendering.

### 2. Per-client manifest (msn_<userId>.json)

Each client domain has a manifest file that tells the backend:
	•	which HTML file to serve (via default_entry)
	•	which data files the backend may expose (via backend_data)
	•	what assets belong to this client
	•	any configuration values needed by the Flask app

The frontend exposes this manifest via two meta-tags in index.html:
```html
<meta name="msn-id" content="<userId>">
<meta name="msn-config" content="msn_<userId>.json">
```
These allow the backend to detect which site is being served and load the right frontend and data.

---

## 3. API Access (via Shared Flask Backend)
The backend exposes APIs under:
```html
<meta name="msn-id" content="<userId>">
<meta name="msn-config" content="msn_<userId>.json">
```

Examples:
	•	/api/weather?location=...
	•	/api/data/<file>
	•	/api/inventory/... (if enabled)
	•	/api/donations/... (if enabled)

These APIs are provided by the global Flask backend, not this repo.

## Important for Agents
	•	Do not create backend files (app.py, modules, blueprints) in this repo.
	•	The backend is located in: Fruitful-Network-Development/flask-app
	•	To add new backend features, modify the appropriate module in that repo.

## CORS & Cross-Origin Usage

If the frontend is hosted separately (e.g., during local development), the backend may need CORS enabled.

The backend supports this via an environment variable:
```code
FLASK_ENABLE_CORS=1
```
Agents should not attempt to implement CORS logic in frontend JavaScript.
CORS configuration belongs in the backend only.

## Adding or Updating Frontend Files
Adding or Updating Frontend Files

### You can modify:
	•	index.html and other HTML files
	•	script.js, modules, frontend logic
	•	styles.css, UI components
	•	images/icons under assets/
	•	client-specific JSON under data/

### If you add a new JSON file under data/, update:

`msn_<userId>.json → backend_data array`

Otherwise the backend will reject access to that file.

### Example:
```json
"backend_data": [
  "crop_rotation_groups.json",
  "product_type_crop.json",
  "new_file.json"
]
```
Do NOT:
	•	write backend Python code here
	•	add Flask blueprints, modules, or app initialization
	•	modify server configs (those belong in aws-etc)

## Deployment Workflow

Frontend updates are deployed to the live server using a pull script:
```code
~/GH-etc/scripts/pull_ctv.sh
```
This script performs a fast-forward-only pull inside:
```code
/srv/webapps/clients/cuyahogaterravita.com
```
Meaning:
	•	you commit to GitHub →
	•	server pulls updates →
	•	site updates immediately (after browser cache clears)

No restarts or rebuilds required.

## Guidance for Agents
Before making changes in this repo, agents must understand:
    1.	This repo is only for static frontend content.
    2.	Backend behavior lives entirely in the shared Flask app repo.
    3.	The manifest controls how this site integrates with the backend.
	   4.	Do not generate backend files (e.g., app.py) here.
	   5.	API calls should target /api/... endpoints—never local filesystem paths.
	   6.	Data files must be whitelisted in the manifest.
	   7.	If cross-origin access is required, request FLASK_ENABLE_CORS=1 on backend.

## Summary

This repository defines:
	•	the public-facing website for cuyahogaterravita.com
	•	the manifest that tells the backend how to serve this site’s content
	•	the data that certain backend modules may expose when whitelisted

Agents modifying this repo should focus on UI/UX, layout, JS logic, and manifest updates, while keeping all backend changes strictly in the Flask application repository.

