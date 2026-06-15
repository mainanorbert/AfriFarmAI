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
license: mit
short_description: Diseases Identification and support for Kenyan farmers
tags:
  - track:backyard
  - sponsor:nvidia
  - achievement:fieldnotes
  - sponsor:modal
  - sponsor:openai
  - sponsor:cohere
  - achievement:off-brand
  - achievement:best-agent
---

# AfriFarmAI - Small AI Models, Practical Support for Kenyan Farmers

AfriFarmAI helps Kenyan smallholder farmers identify likely crop and livestock
health problems from text, voice, and photos. It returns cautious guidance in
English or Swahili, reads the response aloud, and finds nearby agrovets with
phone numbers and direct Google Maps directions.

The idea began with a friend who manages crop and livestock farms across Kenya.
His workers often noticed problems early but struggled to describe symptoms
accurately because of language and literacy barriers. AfriFarmAI lets them show
or describe the problem and quickly receive practical decision support.

## What It Does

1. Accepts typed symptoms, voice recordings, crop photos, or animal photos.
2. Transcribes and translates the farmer's input.
3. Produces a structured diagnosis with confidence, severity, treatment,
   prevention, and professional-escalation guidance.
4. Returns localized text and spoken guidance.
5. Finds nearby agrovets and displays their phone numbers, distances, addresses,
   and Google Maps links.

AfriFarmAI is decision support, not a replacement for a veterinarian,
agronomist, or agricultural extension officer. Uncertain, severe, urgent, or
worsening cases are escalated to professionals.

## Why This Fits Build Small

AfriFarmAI combines smaller, specialized models instead of relying on one large
frontier model:

| Model | Size | Role |
| --- | ---: | --- |
| [NVIDIA Nemotron Nano 12B V2 VL](https://build.nvidia.com/nvidia/nemotron-nano-12b-v2-vl/modelcard) | 12B | Analyzes symptoms and optional images, then returns structured crop or livestock diagnosis support. |
| [Tiny Aya Earth](https://huggingface.co/CohereLabs/tiny-aya-earth) | 3.35B | Translates Swahili input and localizes farmer-facing guidance. |
| [Whisper Large V3](https://huggingface.co/openai/whisper-large-v3) | 1.55B | Transcribes Swahili speech through Hugging Face Inference. |
| [Cohere Transcribe](https://docs.cohere.com/docs/models) | 2b | Transcribes English speech. |
| [VoxCPM2](https://huggingface.co/openbmb/VoxCPM2) | 2B | Generates spoken English and Swahili responses through Modal, with gTTS fallback. |

The application minimizes sensitive information, uses privacy-safe structured
logging, does not store farmer conversations, and uses browser location only
when searching for nearby agrovets.

## Tracks And Prizes

- **Backyard AI:** Practical agricultural support inspired by a real challenge
  faced by Kenyan farm workers.
- **Nemotron Hardware Prize:** Nemotron Nano 12B V2 VL is the core multimodal
  diagnosis model.
- **Best Use of Modal:** Modal hosts VoxCPM2 for multilingual spoken responses.
- **Cohere:** Cohere Transcribe handles English speech input, while Tiny Aya
  Earth translates Swahili input and localizes farmer-facing guidance.
- **Best Use of Codex:** Codex supported architecture, implementation, model
  integration, testing, safety checks, documentation, and deployment preparation.
- **Off Brand:** A custom responsive Gradio interface with light and dark themes.
- **Best Agent:** A multi-step pipeline coordinates transcription, translation,
  multimodal diagnosis, safety validation, localization, speech synthesis, and
  a Google Places agrovet-search tool.
- **Field Notes:** The linked build article explains the project story, model
  choices, accessibility goals, and development journey.

## Links

- **Live app:** https://build-small-hackathon-afri-farm-ai.hf.space/
- **GitHub:** https://github.com/mainanorbert/AfriFarmAI
- **Demo video:** https://www.youtube.com/watch?v=k14J4CnC_KE
- **Social post:** https://www.linkedin.com/posts/norbert-osiemo-0256a4144_afrifarmai-agritech-smallmodels-share-7472353158942318592-wCZY/
- **Build article:** [Building AfriFarmAI: Using Small, Specialized AI Models for Livestock and Diseases Identification](https://www.linkedin.com/pulse/building-afrifarmai-using-small-specialized-ai-models-norbert-osiemo-2c04f)

## How It Is Built

AfriFarmAI is a Python 3.12 Gradio application with Pydantic contracts and a
single-process orchestration pipeline. It calls NVIDIA, Cohere, Hugging Face,
Modal, and Google Places services through replaceable provider clients.
Structured output validation, confidence gating, cautious treatment guidance,
and professional escalation keep the experience practical and safety-focused.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

Add the required provider credentials to `.env`. Never commit `.env`.
