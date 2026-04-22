import io
import logging
import os
import uuid
import zipfile
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from sqlalchemy import text

from database import SessionLocal, engine
from models import Base, CandidateReport, SpeakingReport
from report_generator import generate_reading_report, generate_speaking_report
from scoring import (
    run_reading_pass_chain,
    run_listening_pass_chain,
    run_writing_score,
    run_speaking_score,
)

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cefr")

Base.metadata.create_all(bind=engine)

# ── Idempotent migrations ───────────────────────────────────────────────────
with engine.begin() as conn:
    conn.execute(text("ALTER TABLE candidate_reports ADD COLUMN IF NOT EXISTS writing_weighted_score FLOAT"))
    conn.execute(text("ALTER TABLE candidate_reports ADD COLUMN IF NOT EXISTS writing_cefr_display VARCHAR"))
    conn.execute(text("ALTER TABLE candidate_reports ADD COLUMN IF NOT EXISTS writing_scale_score INTEGER"))

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

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


# ── Helpers ─────────────────────────────────────────────────────────────────
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


def _parse_file(content: bytes, filename: str) -> pd.DataFrame:
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(content))
    else:
        df = pd.read_csv(io.BytesIO(content))
    df.columns = df.columns.str.strip()
    return df


def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


# ── LRW processing ──────────────────────────────────────────────────────────
def _process_lrw(df: pd.DataFrame, db: Session) -> list:
    """Returns list of result dicts (one per row)."""
    results = []

    # Drop unused input column
    df.drop(columns=[c for c in ["_Scenario_Description"] if c in df.columns], inplace=True)

    for _, row in df.iterrows():
        row = row.where(pd.notna(row), None)

        # Reading — primary names from 102-column format; old parenthesis format as fallback
        a2_candidate = _get(row, "Reading A2_Candidate_Score",  "Reading (A2)_Candidate_Score")
        a2_total     = _get(row, "Reading A2_Total_Score",       "Reading (A2)_Total_Score",      default=6)
        b1_candidate = _get(row, "Reading B1_Candidate_Score",  "Reading (B1)_Candidate_Score")
        b1_total     = _get(row, "Reading B1_Total_Score",       "Reading (B1)_Total_Score",      default=9)
        b2_candidate = _get(row, "Reading B2_Candidate_Score",  "Reading (B2-C1)_Candidate_Score")
        b2_total     = _get(row, "Reading B2_Total_Score",       "Reading (B2-C1)_Total_Score",   default=11)

        # Listening — same pattern
        la2_candidate = _get(row, "Listening A2_Candidate_Score", "Listening (A2)_Candidate_Score")
        la2_total     = _get(row, "Listening A2_Total_Score",      "Listening (A2)_Total_Score",    default=6)
        lb1_candidate = _get(row, "Listening B1_Candidate_Score", "Listening (B1)_Candidate_Score")
        lb1_total     = _get(row, "Listening B1_Total_Score",      "Listening (B1)_Total_Score",    default=9)
        lb2_candidate = _get(row, "Listening B2_Candidate_Score", "Listening (B2-C1)_Candidate_Score")
        lb2_total     = _get(row, "Listening B2_Total_Score",      "Listening (B2-C1)_Total_Score", default=11)

        # Writing sub-skills — primary names from 102-column format
        w_grammar  = _get(row, "Writing_Grammar_Percentage",              "Email Writing_Grammar_Percentage")
        w_vocab    = _get(row, "Writing_Vocabulary_Percentage",           "Email Writing_Vocabulary_Percentage")
        w_comp     = _get(row, "Writing_Comprehension_Percentage",        "Email Writing_Comprehension_Percentage")
        w_ortho    = _get(row, "Writing_Orthographic_Control_Percentage", "Email Writing_Orthographic_Control_Percentage")
        w_coher    = _get(row, "Writing_CoherenceAndCohesion_Percentage", "Email Writing_CoherenceAndCohesion_Percentage")
        w_thematic = _get(row, "Writing_Thematic_Development_Percentage", "Email Writing_Thematic_Development_Percentage")

        reading_scoring   = run_reading_pass_chain(a2_candidate, b1_candidate, b2_candidate, a2_total=a2_total, b1_total=b1_total, b2_total=b2_total)
        listening_scoring = run_listening_pass_chain(la2_candidate, lb1_candidate, lb2_candidate, a2_total=la2_total, b1_total=lb1_total, b2_total=lb2_total)
        writing_scoring   = run_writing_score(w_grammar, w_vocab, w_comp, w_ortho, w_coher, w_thematic)

        # Raw sums of all three band scores (always full sum regardless of pass chain)
        reading_total_score   = a2_candidate + b1_candidate + b2_candidate
        listening_total_score = la2_candidate + lb1_candidate + lb2_candidate

        candidate = {
            "name":       _str(row, "Employee_Full_Name"),
            "id":         _str(row, "Employee_ID"),
            "email":      _str(row, "Employee_Email_Address"),
            "company":    _str(row, "Test_Link_Name", "Invited_By_Email_Address"),
            "appeared_on": _str(row, "Appeared_On"),
            "report_generated_on": datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC"),
        }

        report_link = ""
        try:
            pdf_bytes = generate_reading_report(candidate, reading_scoring, listening_scoring, writing_scoring)
            if not pdf_bytes:
                raise ValueError("generator returned empty bytes")

            report_uuid = str(uuid.uuid4())
            db.add(CandidateReport(
                report_uuid=report_uuid,
                candidate_name=candidate["name"], candidate_id=candidate["id"],
                employee_email=candidate["email"], company=candidate["company"],
                appeared_on=candidate["appeared_on"],
                reading_a2_candidate=a2_candidate, reading_a2_total=a2_total,
                reading_b1_candidate=b1_candidate, reading_b1_total=b1_total,
                reading_b2_candidate=b2_candidate, reading_b2_total=b2_total,
                reading_cefr_display=reading_scoring["cefr_display"],
                reading_scale_score=reading_scoring["scale_score"],
                reading_performance_pct=reading_scoring["performance_pct"],
                listening_a2_candidate=la2_candidate, listening_a2_total=la2_total,
                listening_b1_candidate=lb1_candidate, listening_b1_total=lb1_total,
                listening_b2_candidate=lb2_candidate, listening_b2_total=lb2_total,
                listening_cefr_display=listening_scoring["cefr_display"],
                listening_scale_score=listening_scoring["scale_score"],
                listening_performance_pct=listening_scoring["performance_pct"],
                writing_weighted_score=writing_scoring["weighted_score"],
                writing_cefr_display=writing_scoring["cefr_display"],
                writing_scale_score=writing_scoring["scale_score"],
                pdf_data=pdf_bytes,
            ))
            db.commit()
            report_link = f"{BASE_URL}/report/{report_uuid}"

        except Exception as err:
            logger.exception("LRW PDF failed for %s", candidate["name"])

        results.append({
            "reading_total_score":    reading_total_score,
            "reading_cefr":           reading_scoring["cefr_display"],
            "reading_scale_score":    reading_scoring["scale_score"],
            "listening_total_score":  listening_total_score,
            "listening_cefr":         listening_scoring["cefr_display"],
            "listening_scale_score":  listening_scoring["scale_score"],
            "writing_cefr":           writing_scoring["cefr_display"],
            "writing_weighted_score": writing_scoring["weighted_score"],
            "writing_scale_score":    writing_scoring["scale_score"],
            "lrw_report_link":        report_link,
        })

    return results


# ── Speaking processing ─────────────────────────────────────────────────────
def _process_speaking(df: pd.DataFrame, db: Session) -> list:
    """Returns list of result dicts (one per row)."""
    results = []

    # Drop only legacy mock-file columns not present in real input format
    drop_cols = ["_Expected_CEFR", "_Weighted_Score"]
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    for _, row in df.iterrows():
        row = row.where(pd.notna(row), None)

        # Primary names from 44-column real format; old mock/workplace names as fallback
        fluency = _get(
            row,
            "Speaking_OralFluency_Percentage",
            "Speaking_Hard (Workplace)_OralFluency_Percentage",
        )
        vocab = _get(
            row,
            "Speaking_Vocabulary_Percentage",
            "Speaking_Hard (Workplace)_Vocabulary_Percentage",
        )
        grammar = _get(
            row,
            "SpeakingGrammar_Percentage",
            "Speaking_Hard (Workplace)_Grammar_Percentage",
            "Speaking_Hard (Workplace)Grammar_Percentage",
        )
        phonological = _get(
            row,
            "Speaking_Phonological_Control_Percentage",
            "Speaking_Hard (Workplace)_Phonological_Control_Percentage",
        )
        comprehension = _get(
            row,
            "Speaking_Comprehension_Percentage",
            "Speaking_Hard (Workplace)_Comprehension_Percentage",
        )

        speaking_scoring = run_speaking_score(fluency, vocab, grammar, phonological, comprehension)

        candidate = {
            "name":       _str(row, "Employee_Full_Name"),
            "id":         _str(row, "Employee_ID"),
            "email":      _str(row, "Employee_Email_Address"),
            "company":    _str(row, "Test_Link_Name", "Invited_By_Email_Address"),
            "appeared_on": _str(row, "Appeared_On"),
            "report_generated_on": datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC"),
        }

        report_link = ""

        # Skip candidates with no speaking data
        if fluency == 0 and vocab == 0 and grammar == 0 and phonological == 0 and comprehension == 0:
            logger.info("Skipping %s — no Speaking sub-skill data", candidate["name"])
        else:
            try:
                pdf_bytes = generate_speaking_report(candidate, speaking_scoring)
                if not pdf_bytes:
                    raise ValueError("generator returned empty bytes")

                report_uuid = str(uuid.uuid4())
                db.add(SpeakingReport(
                    report_uuid=report_uuid,
                    candidate_name=candidate["name"], candidate_id=candidate["id"],
                    employee_email=candidate["email"], company=candidate["company"],
                    appeared_on=candidate["appeared_on"],
                    speaking_fluency=fluency, speaking_vocab=vocab,
                    speaking_grammar=grammar, speaking_phonological=phonological,
                    speaking_comprehension=comprehension,
                    speaking_weighted_score=speaking_scoring["weighted_score"],
                    speaking_cefr_display=speaking_scoring["cefr_display"],
                    speaking_scale_score=speaking_scoring["scale_score"],
                    pdf_data=pdf_bytes,
                ))
                db.commit()
                report_link = f"{BASE_URL}/speaking-report/{report_uuid}"

            except Exception as err:
                logger.exception("Speaking PDF failed for %s", candidate["name"])

        results.append({
            "weighted_score":        speaking_scoring["weighted_score"],
            "speaking_cefr":         speaking_scoring["cefr_display"],
            "speaking_scale_score":  speaking_scoring["scale_score"],
            "speaking_report_link":  report_link,
        })

    return results


# ── Upload endpoint ─────────────────────────────────────────────────────────
@app.post("/upload")
async def upload_csv(
    lrw_file:      UploadFile = File(...),
    speaking_file: UploadFile = File(...),
):
    """
    Accept LRW file + Speaking file.
    Returns a ZIP containing two separate Excel files:
      - lrw_report.xlsx    (original LRW columns + computed scoring columns)
      - speaking_report.xlsx (original Speaking columns + computed scoring columns)
    """
    lrw_content      = await lrw_file.read()
    speaking_content = await speaking_file.read()

    logger.info("LRW upload: %s (%d bytes)", lrw_file.filename, len(lrw_content))
    logger.info("Speaking upload: %s (%d bytes)", speaking_file.filename, len(speaking_content))

    try:
        lrw_df = _parse_file(lrw_content, lrw_file.filename or "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse LRW file: {e}")

    try:
        spk_df = _parse_file(speaking_content, speaking_file.filename or "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse Speaking file: {e}")

    logger.info("Parsed LRW: %d rows | Speaking: %d rows", len(lrw_df), len(spk_df))

    db: Session = SessionLocal()
    lrw_results = _process_lrw(lrw_df, db)
    spk_results = _process_speaking(spk_df, db)
    db.close()

    logger.info("LRW processed: %d rows | Speaking processed: %d rows",
                len(lrw_results), len(spk_results))

    # ── Build LRW output Excel ─────────────────────────────────────────────
    lrw_df["Reading - Total Score"]   = [r["reading_total_score"]    for r in lrw_results]
    lrw_df["Reading - CEFR Level"]    = [r["reading_cefr"]           for r in lrw_results]
    lrw_df["Reading Scale Score"]     = [r["reading_scale_score"]    for r in lrw_results]
    lrw_df["Reading Scale CEFR"]      = [r["reading_cefr"]           for r in lrw_results]
    lrw_df["Listening - Total Score"] = [r["listening_total_score"]  for r in lrw_results]
    lrw_df["Listening - CEFR Level"]  = [r["listening_cefr"]         for r in lrw_results]
    lrw_df["Listening Scale Score"]   = [r["listening_scale_score"]  for r in lrw_results]
    lrw_df["Listening Scale CEFR"]    = [r["listening_cefr"]         for r in lrw_results]
    lrw_df["Writing CEFR"]            = [r["writing_cefr"]           for r in lrw_results]
    lrw_df["Writing Total Weighted Score"] = [r["writing_weighted_score"] for r in lrw_results]
    lrw_df["Writing Scale"]           = [r["writing_scale_score"]    for r in lrw_results]
    lrw_df["Writing Scale CEFR"]      = [r["writing_cefr"]           for r in lrw_results]
    lrw_df["LRW_Report_Link"]         = [r["lrw_report_link"]        for r in lrw_results]

    # ── Build Speaking output Excel ────────────────────────────────────────
    spk_df["_Weighted_Score"]        = [r["weighted_score"]       for r in spk_results]
    spk_df["Speaking CEFR"]          = [r["speaking_cefr"]        for r in spk_results]
    spk_df["Speaking Scale Score"]   = [r["speaking_scale_score"] for r in spk_results]
    spk_df["Speaking Scale CEFR"]    = [r["speaking_cefr"]        for r in spk_results]
    spk_df["Speaking_Report_Link"]   = [r["speaking_report_link"] for r in spk_results]

    lrw_excel_bytes = _df_to_excel_bytes(lrw_df)
    spk_excel_bytes = _df_to_excel_bytes(spk_df)

    # ── Pack both Excel files into a ZIP ───────────────────────────────────
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("lrw_report.xlsx", lrw_excel_bytes)
        zf.writestr("speaking_report.xlsx", spk_excel_bytes)
    zip_buf.seek(0)

    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=cefr_reports.zip",
            "X-LRW-Count":     str(len(lrw_results)),
            "X-Speaking-Count": str(len(spk_results)),
        },
    )


# ── Report viewer endpoints ─────────────────────────────────────────────────
@app.get("/report/{report_uuid}")
def get_report(report_uuid: str):
    db: Session = SessionLocal()
    record = db.query(CandidateReport).filter(CandidateReport.report_uuid == report_uuid).first()
    db.close()
    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")
    return Response(
        content=record.pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="lrw_report_{report_uuid[:8]}.pdf"',
                 "Cache-Control": "no-store"},
    )


@app.get("/speaking-report/{report_uuid}")
def get_speaking_report(report_uuid: str):
    db: Session = SessionLocal()
    record = db.query(SpeakingReport).filter(SpeakingReport.report_uuid == report_uuid).first()
    db.close()
    if not record:
        raise HTTPException(status_code=404, detail="Speaking report not found.")
    return Response(
        content=record.pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="speaking_report_{report_uuid[:8]}.pdf"',
                 "Cache-Control": "no-store"},
    )


# ── Health check ────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}
