import io
import os
import uuid
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, CandidateReport
from report_generator import generate_reading_report
from scoring import run_reading_pass_chain, run_listening_pass_chain

load_dotenv()
Base.metadata.create_all(bind=engine)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

app = FastAPI(title="CEFR Report Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Column name aliases (handles slight CSV header variations) ─────────────────
def _get(row, *keys, default=0):
    for k in keys:
        if k in row and row[k] is not None and str(row[k]).strip() not in ("", "nan"):
            try:
                return float(row[k])
            except (ValueError, TypeError):
                pass
    return float(default)


def _str(row, *keys, default="—"):
    for k in keys:
        if k in row and str(row[k]).strip() not in ("", "nan", "None"):
            return str(row[k]).strip()
    return default


# ── Upload endpoint ────────────────────────────────────────────────────────────
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Accept a CSV (or Excel) export from iMocha.
    Scores every candidate's Reading section, generates a PDF per candidate,
    stores everything in Postgres, and returns the original file with a new
    'Report_Link' column appended.
    """
    content = await file.read()
    filename = file.filename or ""

    # Parse file
    try:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    # Strip trailing/leading spaces from column names (common in iMocha exports)
    df.columns = df.columns.str.strip()

    db: Session = SessionLocal()
    report_links = []
    results = []

    for _, row in df.iterrows():
        row = row.where(pd.notna(row), None)  # normalise NaN → None

        # ── Extract Reading scores ─────────────────────────────────────────
        a2_candidate = _get(row, "Reading (A2)_Candidate_Score")
        a2_total     = _get(row, "Reading (A2)_Total_Score", default=6)
        b1_candidate = _get(row, "Reading (B1)_Candidate_Score")
        b1_total     = _get(row, "Reading (B1)_Total_Score", default=9)
        b2_candidate = _get(row, "Reading (B2-C1)_Candidate_Score")
        b2_total     = _get(row, "Reading (B2-C1)_Total_Score", default=11)

        # ── Extract Listening scores ───────────────────────────────────────
        la2_candidate = _get(row, "Listening (A2)_Candidate_Score")
        la2_total     = _get(row, "Listening (A2)_Total_Score", default=6)
        lb1_candidate = _get(row, "Listening (B1)_Candidate_Score")
        lb1_total     = _get(row, "Listening (B1)_Total_Score", default=9)
        lb2_candidate = _get(row, "Listening (B2-C1)_Candidate_Score")
        lb2_total     = _get(row, "Listening (B2-C1)_Total_Score", default=11)

        # ── Run scoring engines ────────────────────────────────────────────
        reading_scoring = run_reading_pass_chain(
            a2_candidate, b1_candidate, b2_candidate,
            a2_total=a2_total, b1_total=b1_total, b2_total=b2_total,
        )
        listening_scoring = run_listening_pass_chain(
            la2_candidate, lb1_candidate, lb2_candidate,
            a2_total=la2_total, b1_total=lb1_total, b2_total=lb2_total,
        )

        # ── Candidate metadata ─────────────────────────────────────────────
        candidate = {
            "name":       _str(row, "Employee_Full_Name"),
            "id":         _str(row, "Employee_ID"),
            "email":      _str(row, "Employee_Email_Address"),
            "company":    _str(row, "Test_Link_Name", "Invited_By_Email_Address"),
            "appeared_on": _str(row, "Appeared_On"),
            "report_generated_on": datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC"),
        }

        # ── Generate PDF ───────────────────────────────────────────────────
        pdf_bytes = generate_reading_report(candidate, reading_scoring, listening_scoring)

        # ── Persist to DB ──────────────────────────────────────────────────
        report_uuid = str(uuid.uuid4())
        record = CandidateReport(
            report_uuid=report_uuid,
            candidate_name=candidate["name"],
            candidate_id=candidate["id"],
            employee_email=candidate["email"],
            company=candidate["company"],
            appeared_on=candidate["appeared_on"],
            reading_a2_candidate=a2_candidate,
            reading_a2_total=a2_total,
            reading_b1_candidate=b1_candidate,
            reading_b1_total=b1_total,
            reading_b2_candidate=b2_candidate,
            reading_b2_total=b2_total,
            reading_cefr_display=reading_scoring["cefr_display"],
            reading_scale_score=reading_scoring["scale_score"],
            reading_performance_pct=reading_scoring["performance_pct"],
            listening_a2_candidate=la2_candidate,
            listening_a2_total=la2_total,
            listening_b1_candidate=lb1_candidate,
            listening_b1_total=lb1_total,
            listening_b2_candidate=lb2_candidate,
            listening_b2_total=lb2_total,
            listening_cefr_display=listening_scoring["cefr_display"],
            listening_scale_score=listening_scoring["scale_score"],
            listening_performance_pct=listening_scoring["performance_pct"],
            pdf_data=pdf_bytes,
        )
        db.add(record)
        db.commit()

        link = f"{BASE_URL}/report/{report_uuid}"
        report_links.append(link)
        results.append({
            "candidate_name": candidate["name"],
            "candidate_id": candidate["id"],
            "reading_cefr": reading_scoring["cefr_display"],
            "listening_cefr": listening_scoring["cefr_display"],
            "report_link": link,
        })

    db.close()

    # ── Append Report_Link column and return modified Excel ────────────────
    df["Report_Link"] = report_links
    out = io.BytesIO()
    df.to_excel(out, index=False)
    out.seek(0)

    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=cefr_reports_with_links.xlsx",
            "X-Results": str(len(results)),
        },
    )


# ── Report viewer endpoint ─────────────────────────────────────────────────────
@app.get("/report/{report_uuid}")
def get_report(report_uuid: str):
    """Serve the candidate's PDF report inline (opens in browser)."""
    db: Session = SessionLocal()
    record = (
        db.query(CandidateReport)
        .filter(CandidateReport.report_uuid == report_uuid)
        .first()
    )
    db.close()

    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")

    return Response(
        content=record.pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="cefr_report_{report_uuid[:8]}.pdf"',
            "Cache-Control": "no-store",
        },
    )


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}
