# DocuMind Backend API

Backend service for document upload, PDF text extraction, confidence scoring, AI summaries, and workspace recent activity.

## Run Locally
- Create venv: `python3 -m venv venv && source venv/bin/activate`
- Install packages: `pip install -r requirements.txt`
- Start server: `uvicorn main:app --reload --port 8000`
- API Docs: `http://127.0.0.1:8000/docs`

## Endpoints
- `GET /api/documents/recent` — Returns recent document activity (`document`, `category`, `owner`, `uploaded`, `processing`, `verification`).
- `GET /api/documents/{doc_id}` — Returns document summary, metadata (`category`, `file_type`, `file_size`, `uploaded`, `status`), `extracted_text`, and `confidence`.
- `POST /api/documents/upload` — Multipart form upload (`file`, `owner`, optional `category`) that extracts text, generates a summary, and returns the saved document record.
