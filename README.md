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
short_description: Crop and livestock health support for Kenyan farmers
---

# AfriFarmAI

AfriFarmAI is an AI-powered crop and livestock health assistant for Kenyan
smallholder farmers. It accepts text, voice, and images, then returns cautious
diagnosis support, treatment and prevention guidance, spoken responses, and
nearby agrovets where farmers can get further professional guidance and access
recommended agricultural or veterinary supplies.

## The Problem

Smallholder farmers often struggle to identify crop diseases and livestock
illnesses early and accurately. Veterinarians, agronomists, and agricultural
extension officers may be difficult to reach, especially in rural areas, so a
delayed or incorrect response can lead to major losses.

Many digital tools also fail to serve these farmers effectively. Language and
literacy barriers make it difficult to describe symptoms or understand advice,
while manually searching for a nearby agrovet takes time. Large frontier AI
models can provide useful analysis, but their higher inference costs can make
them difficult to use in an affordable, accessible agricultural support tool.

## The Solution

AfriFarmAI combines smaller, specialized AI models with a multimodal reasoning
model to provide practical and cost-conscious agricultural decision support:

- Accepting typed symptoms, voice recordings, and crop or animal photos.
- Transcribing English speech with Cohere Transcribe and Swahili speech with
  Whisper, reducing the language barrier at input.
- Using Tiny Aya Earth, a small multilingual model, to translate Swahili into
  English for analysis and return advice in the farmer's language. Its smaller
  size helps reduce inference cost.
- Using a multimodal Nemotron model to consider both symptoms and images, then
  returning a structured diagnosis with severity, confidence, treatment, and
  prevention guidance.
- Falling back to GPT-5.4 vision for image-backed requests when Nemotron is
  unavailable, while preserving the same structured diagnosis and safety gates.
- Applying a confidence threshold and safety checks. Uncertain, severe, urgent,
  or worsening cases are directed to an agricultural or veterinary
  professional rather than presented as certain diagnoses.
- Automatically searching Google Places for nearby agrovets after a usable
  diagnosis, using the farmer's browser location only for that search.
- Reading the response aloud with VoxCPM2, with gTTS as a fallback, so farmers
  with limited literacy can speak to the application and hear its guidance.

## How It Works

1. A farmer types symptoms, records a voice message, uploads a photo, or
   combines these inputs.
2. Voice is transcribed and Swahili text is translated into English.
3. Nemotron analyzes the text and optional image and returns structured,
   cautious diagnosis support. If an image-backed Nemotron request fails,
   GPT-5.4 vision performs the image diagnosis fallback.
4. Safety rules validate the result and trigger a low-confidence fallback or
   professional escalation when needed.
5. For a usable diagnosis, the application calls its Google Places agrovet
   search tool and ranks nearby results by distance.
6. Tiny Aya localizes the guidance, and VoxCPM2 generates a spoken reply.

## Why AI Is Essential

AI makes the experience accessible without requiring the farmer to manually
translate symptoms, search disease catalogs, or inspect maps for suppliers.
Multilingual translation and speech recognition reduce language and literacy
barriers, while multimodal reasoning combines symptom descriptions with visual
evidence for more useful support. The application orchestration can also call
the nearby-agrovet search tool automatically after diagnosis.

Reliability is supported by structured model output, Pydantic validation,
low-temperature inference, confidence gating, safe fallbacks, and clear
escalation to professionals. AfriFarmAI is decision support, not a replacement
for a veterinarian, agronomist, or extension officer.

## Models Used

| Model | Published size | Use in AfriFarmAI |
| --- | ---: | --- |
| [Tiny Aya Earth](https://huggingface.co/CohereLabs/tiny-aya-earth) | 3.35B parameters | Hosted through Cohere and used for Swahili-to-English translation and farmer-facing localization. It is specialized for African and West Asian languages and offers a lower-cost multilingual step. |
| [Cohere Transcribe `cohere-transcribe-03-2026`](https://docs.cohere.com/docs/models) | Not publicly disclosed | Performs English speech-to-text transcription. |
| [Whisper Large V3](https://huggingface.co/openai/whisper-large-v3) | 1.55B parameters | Performs Swahili speech-to-text through Hugging Face Inference because Cohere Transcribe does not support Swahili in this application. |
| [NVIDIA Nemotron 3 Nano Omni 30B-A3B Reasoning](https://build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning/modelcard) | 30B total, about 3B active parameters | Uses text and optional images for crop or livestock diagnosis reasoning, severity, confidence, treatment, and prevention guidance. The sparse active parameter count improves inference efficiency. |
| OpenAI GPT-5.4 | Not publicly disclosed | Fallback image analysis and disease identification when an image-backed Nemotron request fails. |
| [VoxCPM2](https://huggingface.co/openbmb/VoxCPM2) | 2B parameters | Hosted on Modal and used for multilingual text-to-speech replies, with gTTS fallback. VoxCPM2 is TTS, not STT; the current integration does not clone or preserve the farmer's recorded voice or accent. |

## How Codex Was Used

Codex supported the project from initial scaffolding through implementation,
testing, review, and documentation. It first helped create the project
instructions in `AGENTS.md` and the architecture and implementation guidance in
`docs/`, including setup commands, coding conventions, safety rules, and the
documented folder structure.

Codex MCP servers were configured in `~/.codex/config.toml` to provide
filesystem access, GitHub workflows, and current OpenAI developer
documentation. Two project-specific Codex skills were also created:

- `afri-farm-ai-review` reviews changes for bugs, architecture compliance,
  agricultural safety, privacy-safe logging, missing tests, and exposed
  secrets.
- `afri-farm-commit` prepares scoped, verified commits, checks project
  conventions, stages only intended files, and pushes only when explicitly
  requested.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with the required provider credentials. Never commit `.env`.

## Run The Project

AfriFarmAI uses a Gradio interface. From the project root, with `.venv`
activated, run:

```bash
python app.py
```

Open the Gradio URL printed in the terminal.

## Screenshots And GIFs

> Placeholder: Add screenshots of text, voice, image, diagnosis, and nearby
> agrovet workflows.

## Demo Video

> Placeholder: Add demo video link.

## Social Post

> Placeholder: Add social post link.
