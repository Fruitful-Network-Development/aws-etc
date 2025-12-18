# fnd-web
Website for fruitfulnetwork development

## Mycite Framework
The Mycite concept separates profile data from presentation so any host can share and reinterpret the same information.

### Goals
1. Provide a standardized profile schema (Compendium, Oeuvre, Anthology) stored in `msn_<userId>.json` alongside the site.
2. Let creative frontends render that schema freely without layout constraints.
3. Enable third parties (directories, co-ops, marketplaces) to consume the same JSON and display consistent views.

### Rationale
- A single canonical JSON profile ensures interoperability across sites and future extensions.
- Free-form frontends can evolve without changing the underlying data contract.
- New sections (videos, certifications, links, grouped projects) can be added to the JSON without breaking existing renderers.
