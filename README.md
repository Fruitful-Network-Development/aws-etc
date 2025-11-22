# infra-aws-linux

## Overview

---

## Project Layout
          
- /infra-aws-linux                  # <-- project folder
- ├── /ect 
  - └── nginx/
    - ├── nginx.conf
    - ├── sites-available/
      - ├── client1-example.com.conf
      - └── client2-nonprofit.org.conf
    - └── sites-enabled/
      - ├── client1-example.com.conf        # -> ../sites-available/client1-example.com.conf
      - └── client2-nonprofit.org.conf      # -> ../sites-available/client2-nonprofit.org.conf
- ├── /srv
  - └── webapps/
    - ├── platform/                         # shared Flask backend
      - ├── app.py                          # main Flask app
      - ├── client_context.py               # figure out which client from Host etc.
      - ├── data_access.py                  # read/write JSON (or DB later)
      - ├── modules/                        # reusable backend "tools"
        - ├── __init__.py
        - ├── donations.py                  # shared donation logic
        - ├── payments.py                   # shared PayPal logic
        - └── pos_integration.py            # shared POS logic
      - └── requirements.txt
    - └── clients/
      - ├── front9farm.com/
        - ├── frontend/
          - ├── index.html                  # main entry; links to pages/ or SPA
          - ├── pages/
            - ├── product_browser.html
            - ├── csa_browser.html
            - ├── happenings.html
            - ├── about_us.html
            - ├── about_csa_program.html
          - ├── assets/
            - ├── style.css
            - ├── imgs/
              - ...
          - ├── widgets/                    # client-specific UI components
            - ├── product/
              - ...                         # templates/js for product widget(s)
            - ├── csa/
              - ...
          - ├── js/
            - ├── widget-loader.js          # loads widgets, calls /api endpoints
        - ├── data/                         # NOT web-exposed; backend only
          inventory.json
          products.json                     # (I'd add .json here)
          csa_offerings.json                # (give it an extension)
          customers.json

        - └── config/                       # (I'd add this back)
          settings.json                     # feature flags, widget config, etc.
          paypal.json                       # client-specific credentials
          pos.json                          # POS API keys/urls
      - ├── CuyahogaValleyCountryside.com/
        - ...
      - ├── front9farm.com/
        - ...
      - ├── FruitfulNetwork.com/
        - ...
      - └── TrappFamilyFarm.com/
        - ...
- └── [README](README.md)                   # <-- this file

---

## Core Components

---

## How It Works

---

## Background Concepts (for reference)

---

## Development Roadmap

---

## License

---

## Acknowledgments

Built and authored by Dylan Montgomery

MODIFIED:	####-##-##
VERSION:	##.##.##
STATUS:     Active prototyping and architectural refinement
