# AfriFarmAI NVIDIA Chat Test

A simple Gradio chat interface that sends each prompt to NVIDIA's
OpenAI-compatible chat API and displays the model's final answer.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set the NVIDIA configuration in the project-root `.env` file:

```dotenv
NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_MODEL_NAME=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

Run the interface:

```bash
source .venv/bin/activate
python -m frontend.app_ui
```

Open `http://localhost:7860`.
