import io
import logging
import os
import uuid
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from sqlalchemy import text

from database import SessionLocal, engine
from models import Base, CandidateReport
from report_generator import generate_reading_report
from scoring import run_reading_pass_chain, run_listening_pass_chain, run_writing_score

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cefr")

Base.metadata.create_all(bind=engine)

# ── Idempotent migration: add Writing columns if they don't exist ────────────
# `create_all` doesn't ALTER existing tables, so older Railway DBs need this.
with engine.begin() as conn:
    conn.execute(text("ALTER TABLE candidate_reports ADD COLUMN IF NOT EXISTS writing_weighted_score FLOAT"))
    conn.execute(text("ALTER TABLE candidate_reports ADD COLUMN IF NOT EXISTS writing_cefr_display VARCHAR"))
    conn.execute(text("ALTER TABLE candidate_reports ADD COLUMN IF NOT EXISTS writing_scale_score INTEGER"))

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# CORS: comma-separated list of allowed origins via FRONTEND_ORIGINS env var.
# Default keeps local dev working; production should set explicit origins.
_origins_env = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
)
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

app = FastAPI(title="CEFR Report Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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
    logger.info("Upload received: filename=%s size=%d bytes", filename, len(content))

    # Parse file
    try:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        logger.exception("File parse failed for %s", filename)
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    logger.info("Parsed %d rows from %s", len(df), filename)

    # Strip trailing/leading spaces from column names (common in iMocha exports)
    df.columns = df.columns.str.strip()

    db: Session = SessionLocal()
    report_links = []
    results = []

    for _, row in df.iterrows():
        row = row.where(pd.notna(row), None)  # normalise NaN → None

        # ── Extract Reading scores ─────────────────────────────────────────
        a2_candidate = _get(row, "Reading (A2)_Candidate_Score", "Reading A2_Candidate_Score")
        a2_total     = _get(row, "Reading (A2)_Total_Score",     "Reading A2_Total_Score",     default=6)
        b1_candidate = _get(row, "Reading (B1)_Candidate_Score", "Reading B1_Candidate_Score")
        b1_total     = _get(row, "Reading (B1)_Total_Score",     "Reading B1_Total_Score",     default=9)
        b2_candidate = _get(row, "Reading (B2-C1)_Candidate_Score", "Reading B2_Candidate_Score")
        b2_total     = _get(row, "Reading (B2-C1)_Total_Score",     "Reading B2_Total_Score",  default=11)

        # ── Extract Listening scores ───────────────────────────────────────
        la2_candidate = _get(row, "Listening (A2)_Candidate_Score", "Listening A2_Candidate_Score")
        la2_total     = _get(row, "Listening (A2)_Total_Score",     "Listening A2_Total_Score",     default=6)
        lb1_candidate = _get(row, "Listening (B1)_Candidate_Score", "Listening B1_Candidate_Score")
        lb1_total     = _get(row, "Listening (B1)_Total_Score",     "Listening B1_Total_Score",     default=9)
        lb2_candidate = _get(row, "Listening (B2-C1)_Candidate_Score", "Listening B2_Candidate_Score")
        lb2_total     = _get(row, "Listening (B2-C1)_Total_Score",     "Listening B2_Total_Score",  default=11)

        # ── Extract Writing sub-skill percentages ─────────────────────────
        w_grammar  = _get(row, "Email Writing_Grammar_Percentage",              "Writing_Grammar_Percentage")
        w_vocab    = _get(row, "Email Writing_Vocabulary_Percentage",           "Writing_Vocabulary_Percentage")
        w_comp     = _get(row, "Email Writing_Comprehension_Percentage",        "Writing_Comprehension_Percentage")
        w_ortho    = _get(row, "Email Writing_Orthographic_Control_Percentage", "Writing_Orthographic_Control_Percentage")
        w_coher    = _get(row, "Email Writing_CoherenceAndCohesion_Percentage", "Writing_CoherenceAndCohesion_Percentage")
        w_thematic = _get(row, "Email Writing_Thematic_Development_Percentage", "Writing_Thematic_Development_Percentage")

        # ── Run scoring engines ────────────────────────────────────────────
        reading_scoring = run_reading_pass_chain(
            a2_candidate, b1_candidate, b2_candidate,
            a2_total=a2_total, b1_total=b1_total, b2_total=b2_total,
        )
        listening_scoring = run_listening_pass_chain(
            la2_candidate, lb1_candidate, lb2_candidate,
            a2_total=la2_total, b1_total=lb1_total, b2_total=lb2_total,
        )
        writing_scoring = run_writing_score(
            w_grammar, w_vocab, w_comp, w_ortho, w_coher, w_thematic,
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
        try:
            pdf_bytes = generate_reading_report(
                candidate, reading_scoring, listening_scoring, writing_scoring,
            )
            if not pdf_bytes:
                raise ValueError("generator returned empty bytes")
        except Exception as err:
            logger.exception(
                "PDF generation failed for candidate %s (%s); skipping row.",
                candidate["name"], candidate["id"],
            )
            report_links.append("")
            results.append({
                "candidate_name":          candidate["name"],
                "candidate_id":            candidate["id"],
                "reading_cefr_level":      reading_scoring["cefr_display"],
                "reading_cefr_total_score": reading_scoring["performance_pct"],
                "reading_scale_score":     reading_scoring["scale_score"],
                "reading_scale_cefr":      reading_scoring["cefr_display"],
                "listening_cefr_level":    listening_scoring["cefr_display"],
                "listening_cefr_total_score": listening_scoring["performance_pct"],
                "listening_scale_score":   listening_scoring["scale_score"],
                "listening_scale_cefr":    listening_scoring["cefr_display"],
                "writing_score":           writing_scoring["performance_pct"],
                "writing_cefr":            writing_scoring["cefr_display"],
                "writing_scale":           writing_scoring["scale_score"],
                "writing_scale_cefr":      writing_scoring["cefr_display"],
                "report_link":             "",
                "error":                   f"PDF generation failed: {err}",
            })
            continue

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
            writing_weighted_score=writing_scoring["performance_pct"],
            writing_cefr_display=writing_scoring["cefr_display"],
            writing_scale_score=writing_scoring["scale_score"],
            pdf_data=pdf_bytes,
        )
        db.add(record)
        db.commit()

        link = f"{BASE_URL}/report/{report_uuid}"
        report_links.append(link)
        results.append({
            "candidate_name":          candidate["name"],
            "candidate_id":            candidate["id"],
            "reading_cefr_level":      reading_scoring["cefr_display"],
            "reading_cefr_total_score": reading_scoring["performance_pct"],
            "reading_scale_score":     reading_scoring["scale_score"],
            "reading_scale_cefr":      reading_scoring["cefr_display"],
            "listening_cefr_level":    listening_scoring["cefr_display"],
            "listening_cefr_total_score": listening_scoring["performance_pct"],
            "listening_scale_score":   listening_scoring["scale_score"],
            "listening_scale_cefr":    listening_scoring["cefr_display"],
            "writing_score":           writing_scoring["performance_pct"],
            "writing_cefr":            writing_scoring["cefr_display"],
            "writing_scale":           writing_scoring["scale_score"],
            "writing_scale_cefr":      writing_scoring["cefr_display"],
            "report_link":             link,
        })

    db.close()

    failed = sum(1 for r in results if r.get("error"))
    logger.info(
        "Upload complete: %d rows, %d succeeded, %d failed",
        len(results), len(results) - failed, failed,
    )

    # ── Append scoring columns and Report_Link, then return modified Excel ─
    df["Reading - CEFR Level"]       = [r["reading_cefr_level"]       for r in results]
    df["Reading - CEFR Total Score"] = [r["reading_cefr_total_score"] for r in results]
    df["Reading Scale Score"]        = [r["reading_scale_score"]      for r in results]
    df["Reading Scale CEFR"]         = [r["reading_scale_cefr"]       for r in results]
    df["Listening - CEFR Level"]       = [r["listening_cefr_level"]       for r in results]
    df["Listening - CEFR Total Score"] = [r["listening_cefr_total_score"] for r in results]
    df["Listening Scale Score"]        = [r["listening_scale_score"]      for r in results]
    df["Listening Scale CEFR"]         = [r["listening_scale_cefr"]       for r in results]
    df["Writing Score"]                = [r["writing_score"]              for r in results]
    df["Writing CEFR"]                 = [r["writing_cefr"]               for r in results]
    df["Writing Scale"]                = [r["writing_scale"]              for r in results]
    df["Writing Scale CEFR"]           = [r["writing_scale_cefr"]         for r in results]
    df["Report_Link"]                  = report_links
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
