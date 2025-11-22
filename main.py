import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import db, create_document, get_documents
from schemas import ForumPost

app = FastAPI(title="AiDUC API", description="AI for Inclusive Education")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ForumPostCreate(ForumPost):
    pass


class ForumPostOut(BaseModel):
    id: str
    title: str
    content: str
    author: str
    tags: Optional[List[str]] = []
    large_text: bool = False
    has_audio: bool = False
    subtitles: bool = False
    audio_url: Optional[str] = None
    attachment_url: Optional[str] = None


@app.get("/")
async def read_root():
    return {"name": "AiDUC API", "features": ["EyeRead", "NeoTutor", "Flexa", "Pathly", "EchoForum"]}


@app.get("/api/hello")
async def hello():
    return {"message": "Hello from AiDUC backend!"}


@app.get("/test")
async def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "❌ Unknown"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


# ---------- EchoForum endpoints ----------
@app.post("/forum", response_model=ForumPostOut)
async def create_forum_post(payload: ForumPostCreate):
    inserted_id = create_document("forumpost", payload)
    return ForumPostOut(id=inserted_id, **payload.model_dump())


@app.get("/forum", response_model=List[ForumPostOut])
async def list_forum_posts(limit: int = 50):
    docs = get_documents("forumpost", limit=min(max(limit, 1), 100))
    results: List[ForumPostOut] = []
    for d in docs:
        _id = str(d.get("_id"))
        d.pop("_id", None)
        results.append(ForumPostOut(id=_id, **d))
    return results


# ---------- NeoTutor ----------
class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Pertanyaan pelajaran")
    level: Optional[str] = Field("umum", description="Tingkat: sd/smp/sma/umum")

class AskResponse(BaseModel):
    answer: str
    steps: List[str]
    tips: List[str]

@app.post("/neotutor/ask", response_model=AskResponse)
async def neotutor_ask(payload: AskRequest):
    q = payload.question.strip()
    # Simple rule-based educational helper as placeholder
    tips = [
        "Baca soal perlahan dan tandai kata kunci.",
        "Ubah pertanyaan menjadi kalimat pernyataan untuk membantu memahami.",
        "Coba jelaskan kembali dengan bahasamu sendiri.",
    ]
    steps: List[str] = []
    answer = ""

    if any(k in q.lower() for k in ["rumus", "formula", "luas", "keliling"]):
        steps = [
            "Identifikasi besaran yang diketahui",
            "Tulis rumus yang sesuai",
            "Substitusi nilai, hitung tahap demi tahap",
            "Tulis jawaban dengan satuan yang benar",
        ]
        answer = "Untuk soal berhitung, gunakan rumus yang tepat lalu hitung tahap demi tahap."
    elif q.endswith("?"):
        steps = ["Pahami pertanyaan", "Cari konsep utama", "Berikan contoh sederhana", "Simpulkan"]
        answer = "Berikut penjelasan singkat dengan bahasa sederhana sesuai pertanyaanmu."
    else:
        steps = ["Pecah persoalan", "Cari definisi", "Hubungkan dengan contoh", "Simpulkan"]
        answer = "Ini adalah jawaban ringkas yang mudah diikuti."

    # Make answer friendlier by echoing topic keywords
    topic = q[:80]
    answer = f"Menjawab: '{topic}'. {answer}"

    return AskResponse(answer=answer, steps=steps, tips=tips)


# ---------- Flexa (format converter) ----------
class FlexaRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Teks sumber")

class FlexaResponse(BaseModel):
    audio_url: Optional[str] = None
    large_text: str
    summary: str
    sign_gloss: List[str]

@app.post("/flexa/convert", response_model=FlexaResponse)
async def flexa_convert(payload: FlexaRequest):
    text = payload.text.strip()
    # Large text: keep content, frontend will render with larger size; we also add simple spacing hints
    large_text = text
    # Summary: naive sentence truncation
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    summary = ". ".join(sentences[:2])
    if len(sentences) > 2:
        summary += "..."
    # Sign language gloss (placeholder): uppercase keywords split
    words = [w for w in text.replace("\n", " ").split(" ") if w]
    gloss = [w.upper() for w in words[:8]]

    return FlexaResponse(audio_url=None, large_text=large_text, summary=summary, sign_gloss=gloss)


# ---------- EyeRead (text-first MVP) ----------
class EyeReadRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Teks yang terbaca dari kamera/scan")

class EyeReadResponse(BaseModel):
    text: str
    summary: str
    audio_url: Optional[str] = None

@app.post("/eyeread/scan", response_model=EyeReadResponse)
async def eyeread_scan(payload: EyeReadRequest):
    text = payload.text.strip()
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    summary = ". ".join(sentences[:2])
    if len(sentences) > 2:
        summary += "..."
    return EyeReadResponse(text=text, summary=summary, audio_url=None)


# ---------- Pathly (adaptive path) ----------
class PathlyRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    proficiency: int = Field(3, ge=1, le=5, description="1 pemula - 5 mahir")

class PathItem(BaseModel):
    title: str
    objective: str
    activity: str

class PathlyResponse(BaseModel):
    level: str
    plan: List[PathItem]
    recommended: List[str]

@app.post("/pathly/plan", response_model=PathlyResponse)
async def pathly_plan(payload: PathlyRequest):
    topic = payload.topic.strip()
    p = payload.proficiency
    if p <= 2:
        level = "dasar"
        plan = [
            PathItem(title=f"Pengenalan {topic}", objective="Memahami konsep inti", activity="Baca ringkasan + 3 contoh"),
            PathItem(title="Latihan ringan", objective="Menguatkan pemahaman", activity="Kerjakan 5 soal pilihan ganda"),
        ]
        recommended = ["Video pengantar 5 menit", "Kartu ringkas istilah"]
    elif p == 3:
        level = "menengah"
        plan = [
            PathItem(title=f"Pendalaman {topic}", objective="Menghubungkan konsep", activity="Buat peta konsep sederhana"),
            PathItem(title="Latihan terarah", objective="Terapan dasar", activity="Kerjakan 5 soal cerita"),
        ]
        recommended = ["Artikel ringkas", "Latihan interaktif"]
    else:
        level = "lanjutan"
        plan = [
            PathItem(title=f"Aplikasi {topic}", objective="Pemecahan masalah", activity="Proyek mini 1 halaman"),
            PathItem(title="Refleksi", objective="Menjelaskan ke orang lain", activity="Tulis ringkasan 150 kata"),
        ]
        recommended = ["Bank soal tingkat lanjut", "Topik terkait untuk eksplorasi"]

    return PathlyResponse(level=level, plan=plan, recommended=recommended)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
