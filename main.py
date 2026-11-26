from datetime import datetime, timezone
import io
import re
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader

app = FastAPI(title="DocuMind Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def time_ago(dt: datetime) -> str:
    seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
    if seconds < 60:
        return "Just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"


def infer_category(filename: str, text: str) -> str:
    combined = f"{filename} {text}".lower()
    if any(k in combined for k in ["admission", "transcript", "university", "jamb", "bachelor", "academic"]):
        return "Academic"
    if any(k in combined for k in ["passport", "nin", "driver", "license", "identity", "id card"]):
        return "Identity"
    if any(k in combined for k in ["income", "statement", "invoice", "bank", "tax", "financial", "salary"]):
        return "Financial"
    if any(k in combined for k in ["application", "recommendation", "resume", "cv"]):
        return "Application"
    return "Other"


def generate_summary(title: str, category: str, extracted_text: str) -> str:
    clean = re.sub(r"\s+", " ", extracted_text).strip()
    if not clean:
        return f"Uploaded {category.lower()} document ({title}) awaiting text extraction."
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    summary = " ".join(sentences[:2])
    return summary[:240] + ("..." if len(summary) > 240 else "")


def extract_pdf_text(file_bytes: bytes) -> tuple[str, int]:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        full_text = "\n".join(pages_text).strip()
        if len(full_text) >= 40:
            return full_text, 98
        if full_text:
            return full_text, 85
        return "Scanned or image-based PDF detected. No embedded selectable text found.", 72
    except Exception:
        return "Unable to parse document text directly.", 60


DOCUMENTS_DB: dict[str, dict] = {
    "doc_admission_01": {
        "id": "doc_admission_01",
        "title": "Admission Letter",
        "filename": "Admission Letter - University of Lagos.pdf",
        "category": "Academic",
        "owner": "Ada Okafor",
        "file_type": "PDF",
        "file_size": "1.8 MB",
        "uploaded_date": "May 24, 2025",
        "uploaded_at": datetime(2025, 5, 24, 10, 0, tzinfo=timezone.utc),
        "status": "Processed",
        "verification": "Verified",
        "ai_summary": (
            "Official admission letter confirming an offer to study Computer Science "
            "at the University of Lagos for the 2025/2026 academic session."
        ),
        "confidence": 98,
        "extracted_text": (
            "Dear Ada Okafor, we are pleased to offer you admission into the Bachelor of Science "
            "programme in Computer Science for the 2025/2026 academic session. Your JAMB registration "
            "number is 20255820419DF. Your recorded JAMB score is 286. Please accept this offer "
            "before June 14, 2025."
        ),
    },
    "doc_app_0482": {
        "id": "doc_app_0482",
        "title": "Student Application 0482",
        "filename": "Student_Application_0482.pdf",
        "category": "Application",
        "owner": "Sarah Mitchell",
        "file_type": "PDF",
        "file_size": "1.2 MB",
        "uploaded_date": "Nov 26, 2026",
        "uploaded_at": datetime.now(timezone.utc),
        "status": "Processed",
        "verification": "Verified",
        "ai_summary": "Completed undergraduate admissions application submitted by Sarah Mitchell with supporting academic records.",
        "confidence": 97,
        "extracted_text": "Applicant Name: Sarah Mitchell. Application ID: 0482. Program: Computer Science. Status: Complete.",
    },
    "doc_passport_jw": {
        "id": "doc_passport_jw",
        "title": "Passport James Wilson",
        "filename": "Passport_James_Wilson.pdf",
        "category": "Identity",
        "owner": "James Wilson",
        "file_type": "PDF",
        "file_size": "2.4 MB",
        "uploaded_date": "Nov 26, 2026",
        "uploaded_at": datetime.now(timezone.utc),
        "status": "Processed",
        "verification": "Verified",
        "ai_summary": "Valid international passport identity document verified for James Wilson.",
        "confidence": 99,
        "extracted_text": "PASSPORT | Surname: WILSON | Given Names: JAMES | Nationality: Verified | Status: Valid.",
    },
    "doc_transcript_emma": {
        "id": "doc_transcript_emma",
        "title": "Transcript 2024 Emma",
        "filename": "Transcript_2024_Emma.pdf",
        "category": "Academic",
        "owner": "Emma Thompson",
        "file_type": "PDF",
        "file_size": "950 KB",
        "uploaded_date": "Nov 26, 2026",
        "uploaded_at": datetime.now(timezone.utc),
        "status": "Processing",
        "verification": "Pending",
        "ai_summary": "2024 academic transcript for Emma Thompson currently undergoing automated grade verification.",
        "confidence": 91,
        "extracted_text": "Official Academic Transcript — Student: Emma Thompson — Academic Year 2024.",
    },
    "doc_income_rk": {
        "id": "doc_income_rk",
        "title": "Income Statement RK",
        "filename": "Income_Statement_RK.pdf",
        "category": "Financial",
        "owner": "Robert King",
        "file_type": "PDF",
        "file_size": "1.5 MB",
        "uploaded_date": "Nov 26, 2026",
        "uploaded_at": datetime.now(timezone.utc),
        "status": "Processed",
        "verification": "Flagged",
        "ai_summary": "Annual income statement for Robert King flagged for manual review due to variance in reported figures.",
        "confidence": 89,
        "extracted_text": "Statement of Income — Account Holder: Robert King — Period: FY 2025/2026.",
    },
    "doc_rec_letter": {
        "id": "doc_rec_letter",
        "title": "Recommendation Letter",
        "filename": "Recommendation_Letter.pdf",
        "category": "Application",
        "owner": "Noah Williams",
        "file_type": "PDF",
        "file_size": "640 KB",
        "uploaded_date": "Nov 26, 2026",
        "uploaded_at": datetime.now(timezone.utc),
        "status": "Processed",
        "verification": "Pending",
        "ai_summary": "Academic recommendation letter submitted on behalf of applicant Noah Williams.",
        "confidence": 96,
        "extracted_text": "To the Admissions Committee, I strongly recommend Noah Williams for admission into your program.",
    },
}


@app.get("/")
def health_check():
    return {"service": "DocuMind Backend", "status": "running"}


@app.get("/api/documents/recent")
def get_recent_activity(limit: int = 10):
    docs = sorted(
        DOCUMENTS_DB.values(),
        key=lambda d: d["uploaded_at"],
        reverse=True,
    )[:limit]

    return [
        {
            "id": d["id"],
            "document": d["filename"],
            "category": d["category"],
            "owner": d["owner"],
            "uploaded": time_ago(d["uploaded_at"]),
            "processing": d["status"],
            "verification": d["verification"],
        }
        for d in docs
    ]


@app.get("/api/documents/{doc_id}")
def get_document_details(doc_id: str):
    doc = DOCUMENTS_DB.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc["id"],
        "title": doc["title"],
        "filename": doc["filename"],
        "ai_summary": doc["ai_summary"],
        "details": {
            "category": doc["category"],
            "file_type": doc["file_type"],
            "file_size": doc["file_size"],
            "uploaded": doc["uploaded_date"],
            "status": doc["status"],
        },
        "extracted_text": doc["extracted_text"],
        "confidence": doc["confidence"],
        "verification": doc["verification"],
    }


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    owner: str = Form("Ada Okafor"),
    category: Optional[str] = Form(None),
):
    raw_bytes = await file.read()
    size_mb = len(raw_bytes) / (1024 * 1024)
    file_size_str = f"{size_mb:.1f} MB" if size_mb >= 0.1 else f"{max(1, len(raw_bytes) // 1024)} KB"

    filename = file.filename or "Untitled.pdf"
    ext = filename.rsplit(".", 1)[-1].upper() if "." in filename else "FILE"
    title = filename.rsplit(".", 1)[0].replace("_", " ")

    if ext == "PDF":
        extracted_text, confidence = extract_pdf_text(raw_bytes)
    else:
        extracted_text = raw_bytes.decode("utf-8", errors="ignore").strip() or "Uploaded document content."
        confidence = 95

    resolved_category = category or infer_category(filename, extracted_text)
    ai_summary = generate_summary(title, resolved_category, extracted_text)
    now = datetime.now(timezone.utc)
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    record = {
        "id": doc_id,
        "title": title,
        "filename": filename,
        "category": resolved_category,
        "owner": owner,
        "file_type": ext,
        "file_size": file_size_str,
        "uploaded_date": now.strftime("%b %d, %Y"),
        "uploaded_at": now,
        "status": "Processed",
        "verification": "Verified" if confidence >= 90 else "Pending",
        "ai_summary": ai_summary,
        "confidence": confidence,
        "extracted_text": extracted_text,
    }
    DOCUMENTS_DB[doc_id] = record

    return get_document_details(doc_id)
