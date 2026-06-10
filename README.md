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

# friFarmAI

A Gradio crop and livestock health assistant for Kenyan smallholder farmers. It diagnoses likely conditions, provides cautious treatment guidance, and searches Google Places for nearby agrovets when a disease is identified.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env