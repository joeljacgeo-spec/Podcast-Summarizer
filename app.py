import os, tempfile, json, re
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app = FastAPI(title="PodBrief API")
app.mount("/static", StaticFiles(directory="static"), name="static")

class URLRequest(BaseModel):
    url: HttpUrl

@app.get("/")
async def home():
    return FileResponse("static/index.html")

def client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(503, "Add OPENAI_API_KEY to your .env file to enable AI summaries.")
    return OpenAI(api_key=key)

def summarize_transcript(transcript: str):
    prompt = """You are PodBrief, an accurate podcast editor. Analyze the transcript and return ONLY valid JSON with this schema:
{
 "title": "short episode title",
 "overview": "2-3 sentence overview",
 "discussion_points": [{"heading":"topic","detail":"concise explanation","timestamp":"MM:SS or null"}],
 "key_takeaways": ["takeaway"],
 "notable_quotes": [{"quote":"short exact quote from transcript","timestamp":"MM:SS or null"}],
 "topics": ["topic"]
}
Rules: capture the central arguments and meaningful disagreements; do not invent facts, speakers, quotes or timestamps. If timestamps are unavailable, use null. Aim for 5-8 discussion points and 3-5 takeaways. Keep the language clear and concise."""
    response = client().chat.completions.create(
        model=os.getenv("SUMMARY_MODEL", "gpt-4o-mini"),
        response_format={"type":"json_object"},
        messages=[
            {"role":"system","content":prompt},
            {"role":"user","content":transcript[:100000]}
        ],
        temperature=0.2
    )
    return json.loads(response.choices[0].message.content)

def transcribe(path: str):
    size = os.path.getsize(path)
    if size > 24 * 1024 * 1024:
        raise HTTPException(413, "Audio is larger than 24 MB. Please upload a shorter or compressed audio file.")
    with open(path, "rb") as audio:
        result = client().audio.transcriptions.create(
            model=os.getenv("TRANSCRIPTION_MODEL", "whisper-1"),
            file=audio,
            response_format="text"
        )
    return str(result)

@app.post("/api/summarize/upload")
async def summarize_upload(audio: UploadFile = File(...)):
    allowed = {".mp3",".wav",".m4a",".mp4",".mpeg",".mpga",".webm"}
    suffix = Path(audio.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, "Supported formats: MP3, WAV, M4A, MP4, MPEG and WEBM.")
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            tmp = f.name
            while chunk := await audio.read(1024 * 1024):
                f.write(chunk)
        transcript = transcribe(tmp)
        result = summarize_transcript(transcript)
        result["transcript"] = transcript
        result["source_name"] = audio.filename
        return result
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)

@app.post("/api/summarize/url")
async def summarize_url(body: URLRequest):
    url = str(body.url)
    host = (urlparse(url).hostname or "").lower()
    if not host or not re.match(r"^[a-z0-9.-]+$", host):
        raise HTTPException(400, "Please provide a valid public podcast or audio URL.")
    # Download only direct audio files. For platform pages, request an audio enclosure/direct file URL.
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix not in {".mp3",".wav",".m4a",".mp4",".mpeg",".mpga",".webm"}:
        raise HTTPException(400, "This URL does not look like a direct audio file. Paste the episode's direct MP3/M4A audio link.")
    import requests
    tmp = None
    try:
        with requests.get(url, stream=True, timeout=30, headers={"User-Agent":"PodBrief/1.0"}) as r:
            r.raise_for_status()
            content_type = r.headers.get("content-type","").lower()
            if not (content_type.startswith("audio/") or "octet-stream" in content_type or "video/mp4" in content_type):
                raise HTTPException(400, "The link did not return an audio file.")
            total = 0
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                tmp = f.name
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        total += len(chunk)
                        if total > 24 * 1024 * 1024:
                            raise HTTPException(413, "Audio is larger than 24 MB. Please use a shorter or compressed file.")
                        f.write(chunk)
        transcript = transcribe(tmp)
        result = summarize_transcript(transcript)
        result["transcript"] = transcript
        result["source_name"] = urlparse(url).path.split("/")[-1] or "Podcast URL"
        return result
    except requests.RequestException as e:
        raise HTTPException(400, f"Could not retrieve that audio URL: {e}")
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)

@app.get("/api/health")
async def health():
    return {"ok": True, "ai_configured": bool(os.getenv("OPENAI_API_KEY"))}
