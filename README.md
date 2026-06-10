---
title: AfriFarmAI
emoji: 🌱
colorFrom: green
colorTo: yellow
sdk: gradio
sdk_version: "6.17.3"
python_version: "3.12"
app_file: app.py
pinned: false
short_description: Multilingual crop and livestock health support for Kenyan farmers
---

# AfriFarmAI

A Gradio crop and livestock health assistant for Kenyan smallholder farmers.
It diagnoses likely conditions, provides cautious treatment guidance, and
searches Google Places for nearby agrovets when a disease is identified.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set provider configuration in the project-root `.env` file:

```dotenv
NVIDIA_API_KEY=your_nvidia_api_key
GOOGLE_PLACES_API_KEY=your_server_side_google_places_key
```

Enable Places API (New) for the Google key. The key is used only by backend
requests and must never be placed in frontend JavaScript.

Run the interface from the project virtual environment:

```bash
source .venv/bin/activate
python app.py
```

Open `http://localhost:7860`.

The browser requests location permission automatically. If permission is
denied, use the compact location icon beside the theme and language controls
to retry.
