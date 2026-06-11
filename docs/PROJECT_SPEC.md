# Capstone Spec - AFRIFARMAI: AI-Powered Crop & Livestock Health Assistant

## Problem Statement

Smallholder farmers across Kenya frequently struggle to identify crop diseases and livestock illnesses early enough to prevent major losses. Access to agricultural extension officers, veterinarians, and agronomists is often limited, especially in rural communities. Language barriers, low literacy levels, and lack of localized agricultural support further reduce access to timely expert guidance.

ShambaAI is a multilingual AI-powered agricultural assistant that enables farmers to describe symptoms using voice or text in Swahili or English, upload images of affected crops or animals, receive disease diagnosis and treatment recommendations, and locate nearby agro-dealers for agricultural supplies and veterinary products.

## What Success Looks Like

* Farmers can describe crop or livestock symptoms using voice or text.
* Farmers can upload images of affected crops or animals for analysis.
* Voice messages are automatically transcribed into text.
* Swahili inputs are translated for AI analysis.
* Crop and livestock images are analyzed using multimodal AI models.
* The system identifies likely diseases or health conditions.
* Disease severity is classified as mild, moderate, or severe.
* Farmers receive practical treatment recommendations.
* Farmers receive prevention guidance to reduce future outbreaks.
* Responses are returned in the farmer's preferred language.
* Audio responses are generated for users with limited literacy.
* Nearby agro-dealers are recommended using GPS location data.
* Agro-dealer contact information and specialties are displayed.
* The system provides safe fallback responses when confidence is low.
* The application is publicly accessible through Hugging Face Spaces.
* Frontend and backend validation tests pass before submission.

## Tech Stack

### Frontend

* Gradio

### Backend

* Python 3.12
* FastAPI
* SQLAlchemy
* Pydantic
* Uvicorn

### AI Models

* Cohere Transcribe
* Tiny Aya
* MiniCPM-V 4.6
* Nemotron Nano Omni 30B-A3B

### Database

* PostgreSQL

### External Services

* Hugging Face Inference API
* NVIDIA API
* Cohere API
* VoxCPM2 hosted on Modal, with gTTS fallback

### Deployment

* Hugging Face Spaces
* Docker

## Task List

1. Create Codex instruction files and capstone specification.
2. Set up frontend and backend project architecture.
3. Configure PostgreSQL database and data models.
4. Build FastAPI endpoints for diagnosis workflows.
5. Integrate Cohere Transcribe for speech-to-text.
6. Integrate Tiny Aya for multilingual translation.
7. Integrate MiniCPM-V for crop and livestock image analysis.
8. Integrate Nemotron for diagnosis reasoning and treatment recommendations.
9. Design agro-dealer database schema.
10. Create agro-dealer ingestion and management workflows.
11. Implement GPS-based agro-dealer recommendation engine.
12. Build multilingual voice and text input workflows.
13. Implement crop disease diagnosis workflows.
14. Implement livestock disease diagnosis workflows.
15. Generate treatment recommendations and prevention guidance.
16. Generate multilingual responses.
17. Generate audio responses using text-to-speech.
18. Build diagnosis dashboard and results interface.
19. Add confidence scoring and fallback responses.
20. Implement logging and monitoring.
21. Add validation and error handling.
22. Test voice-only diagnosis workflows.
23. Test image-only diagnosis workflows.
24. Test multimodal diagnosis workflows.
25. Test agro-dealer recommendation accuracy.
26. Deploy application to Hugging Face Spaces.
27. Create README documentation.

## Out of Scope for MVP

* Satellite imagery analysis.
* Drone-based crop monitoring.
* Real-time disease outbreak prediction.
* Automated pesticide procurement.
* Agro-dealer inventory synchronization.
* Farm management dashboards.
* Weather forecasting systems.
* Government subsidy integrations.
* Agricultural loan recommendations.
* Offline mobile synchronization.
* Custom model fine-tuning using farmer conversations.
