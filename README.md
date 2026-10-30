# PodBrief

A minimal SaaS-style podcast summarizer. Upload an audio file or paste a **direct audio-file URL**. The backend transcribes it with OpenAI Whisper and produces a structured summary with an OpenAI chat model.

## Features
- Audio upload: MP3, WAV, M4A, MP4, MPEG and WEBM
- Direct audio URL ingestion (MP3/M4A/etc.)
- AI episode overview
- 5–8 major discussion points
- Key takeaways, notable quotes and topic tags
- Timestamp fields when provided by the transcription/model

## Requirements
- Python 3.10+
- An OpenAI API key with access to audio transcription and chat completions

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Put your key in `.env`, then:
```bash
uvicorn app:app --reload
```
Open http://127.0.0.1:8000

## Important limitations
- The transcription API currently accepts files up to 25 MB; this demo enforces a 24 MB limit. Long episodes may need compression or chunking before upload.
- URL mode expects a **direct public audio file URL**. Spotify, Apple Podcasts, YouTube and other episode webpage links are not direct audio files and will not work unless you obtain the direct audio/enclosure URL.
- Timestamp precision depends on the transcript/model output; timestamps may be omitted rather than guessed.
- This starter app does not include accounts, billing, persistent history, background jobs, or production deployment hardening.
- Audio is held temporarily on the server for processing and deleted afterward. Configure hosting, retention and privacy policies before public deployment.
- Add rate limiting, file scanning, SSRF protections and authentication before exposing the service publicly.
