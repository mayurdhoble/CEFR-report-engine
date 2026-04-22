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
    # speaking_reports created by create_all above; no ALTER needed

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


# ── LRW processing ──────────────────────────────────────────────────────────
def _process_lrw(df: pd.DataFrame, db: Session) -> tuple[list, list]:
    """Returns (results_list, report_links_list)."""
    results, report_links = [], []

    for _, row in df.iterrows():
        row = row.where(pd.notna(row), None)

        a2_candidate = _get(row, "Reading (A2)_Candidate_Score", "Reading A2_Candidate_Score")
        a2_total     = _get(row, "Reading (A2)_Total_Score",     "Reading A2_Total_Score",     default=6)
        b1_candidate = _get(row, "Reading (B1)_Candidate_Score", "Reading B1_Candidate_Score")
        b1_total     = _get(row, "Reading (B1)_Total_Score",     "Reading B1_Total_Score",     default=9)
        b2_candidate = _get(row, "Reading (B2-C1)_Candidate_Score", "Reading B2_Candidate_Score")
        b2_total     = _get(row, "Reading (B2-C1)_Total_Score",     "Reading B2_Total_Score",  default=11)

        la2_candidate = _get(row, "Listening (A2)_Candidate_Score", "Listening A2_Candidate_Score")
        la2_total     = _get(row, "Listening (A2)_Total_Score",     "Listening A2_Total_Score",     default=6)
        lb1_candidate = _get(row, "Listening (B1)_Candidate_Score", "Listening B1_Candidate_Score")
        lb1_total     = _get(row, "Listening (B1)_Total_Score",     "Listening B1_Total_Score",     default=9)
        lb2_candidate = _get(row, "Listening (B2-C1)_Candidate_Score", "Listening B2_Candidate_Score")
        lb2_total     = _get(row, "Listening (B2-C1)_Total_Score",     "Listening B2_Total_Score",  default=11)

        w_grammar  = _get(row, "Email Writing_Grammar_Percentage",              "Writing_Grammar_Percentage")
        w_vocab    = _get(row, "Email Writing_Vocabulary_Percentage",           "Writing_Vocabulary_Percentage")
        w_comp     = _get(row, "Email Writing_Comprehension_Percentage",        "Writing_Comprehension_Percentage")
        w_ortho    = _get(row, "Email Writing_Orthographic_Control_Percentage", "Writing_Orthographic_Control_Percentage")
        w_coher    = _get(row, "Email Writing_CoherenceAndCohesion_Percentage", "Writing_CoherenceAndCohesion_Percentage")
        w_thematic = _get(row, "Email Writing_Thematic_Development_Percentage", "Writing_Thematic_Development_Percentage")

        reading_scoring  = run_reading_pass_chain(a2_candidate, b1_candidate, b2_candidate, a2_total=a2_total, b1_total=b1_total, b2_total=b2_total)
        listening_scoring = run_listening_pass_chain(la2_candidate, lb1_candidate, lb2_candidate, a2_total=la2_total, b1_total=lb1_total, b2_total=lb2_total)
        writing_scoring  = run_writing_score(w_grammar, w_vocab, w_comp, w_ortho, w_coher, w_thematic)

        candidate = {
            "name":       _str(row, "Employee_Full_Name"),
            "id":         _str(row, "Employee_ID"),
            "email":      _str(row, "Employee_Email_Address"),
            "company":    _str(row, "Test_Link_Name", "Invited_By_Email_Address"),
            "appeared_on": _str(row, "Appeared_On"),
            "report_generated_on": datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC"),
        }

        try:
            pdf_bytes = generate_reading_report(candidate, reading_scoring, listening_scoring, writing_scoring)
            if not pdf_bytes:
                raise ValueError("generator returned empty bytes")
        except Exception as err:
            logger.exception("LRW PDF failed for %s", candidate["name"])
            report_links.append("")
            results.append({**_lrw_result(candidate, reading_scoring, listening_scoring, writing_scoring), "report_link": "", "error": str(err)})
            continue

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
            writing_weighted_score=writing_scoring["performance_pct"],
            writing_cefr_display=writing_scoring["cefr_display"],
            writing_scale_score=writing_scoring["scale_score"],
            pdf_data=pdf_bytes,
        ))
        db.commit()

        link = f"{BASE_URL}/report/{report_uuid}"
        report_links.append(link)
        results.append({**_lrw_result(candidate, reading_scoring, listening_scoring, writing_scoring), "report_link": link})

    return results, report_links


def _lrw_result(candidate, rs, ls, ws):
    return {
        "candidate_name":      candidate["name"],
        "candidate_id":        candidate["id"],
        "candidate_email":     candidate["email"],
        "reading_cefr":        rs["cefr_display"],
        "reading_scale_score": rs["scale_score"],
        "listening_cefr":      ls["cefr_display"],
        "listening_scale_score": ls["scale_score"],
        "writing_cefr":        ws["cefr_display"],
        "writing_scale_score": ws["scale_score"],
    }


# ── Speaking processing ─────────────────────────────────────────────────────
def _process_speaking(df: pd.DataFrame, db: Session) -> tuple[list, list]:
    """Returns (results_list, report_links_list)."""
    results, report_links = [], []

    for _, row in df.iterrows():
        row = row.where(pd.notna(row), None)

        fluency = _get(
            row,
            "Speaking_Hard (Workplace)_OralFluency_Percentage",
            "Speaking_OralFluency_Percentage",
        )
        vocab = _get(
            row,
            "Speaking_Hard (Workplace)_Vocabulary_Percentage",
            "Speaking_Vocabulary_Percentage",
        )
        grammar = _get(
            row,
            "Speaking_Hard (Workplace)_Grammar_Percentage",
            "Speaking_Hard (Workplace)Grammar_Percentage",
            "SpeakingGrammar_Percentage",
        )
        phonological = _get(
            row,
            "Speaking_Hard (Workplace)_Phonological_Control_Percentage",
            "Speaking_Phonological_Control_Percentage",
        )
        comprehension = _get(
            row,
            "Speaking_Hard (Workplace)_Comprehension_Percentage",
            "Speaking_Comprehension_Percentage",
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

        # Skip candidates with no speaking data (all zeros)
        if fluency == 0 and vocab == 0 and grammar == 0 and phonological == 0 and comprehension == 0:
            logger.info("Skipping %s — no Speaking sub-skill data", candidate["name"])
            report_links.append("")
            results.append({**_speaking_result(candidate, speaking_scoring), "speaking_report_link": "", "skip": True})
            continue

        try:
            pdf_bytes = generate_speaking_report(candidate, speaking_scoring)
            if not pdf_bytes:
                raise ValueError("generator returned empty bytes")
        except Exception as err:
            logger.exception("Speaking PDF failed for %s", candidate["name"])
            report_links.append("")
            results.append({**_speaking_result(candidate, speaking_scoring), "speaking_report_link": "", "error": str(err)})
            continue

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

        link = f"{BASE_URL}/speaking-report/{report_uuid}"
        report_links.append(link)
        results.append({**_speaking_result(candidate, speaking_scoring), "speaking_report_link": link})

    return results, report_links


def _speaking_result(candidate, ss):
    return {
        "candidate_name":          candidate["name"],
        "candidate_id":            candidate["id"],
        "candidate_email":         candidate["email"],
        "speaking_cefr":           ss["cefr_display"],
        "speaking_scale_score":    ss["scale_score"],
    }


# ── Upload endpoint ─────────────────────────────────────────────────────────
@app.post("/upload")
async def upload_csv(
    lrw_file:      UploadFile = File(...),
    speaking_file: UploadFile = File(...),
):
    """
    Accept LRW file + Speaking file.
    Scores all candidates, generates two PDFs per candidate (LRW + Speaking),
    merges both DataFrames on common identity columns, and returns one Excel
    with all original columns plus scoring columns and both report links.
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

    lrw_results, lrw_links     = _process_lrw(lrw_df, db)
    spk_results, spk_links     = _process_speaking(spk_df, db)

    db.close()

    failed_lrw = sum(1 for r in lrw_results if r.get("error"))
    failed_spk = sum(1 for r in spk_results if r.get("error"))
    logger.info("LRW: %d rows, %d failed | Speaking: %d rows, %d failed",
                len(lrw_results), failed_lrw, len(spk_results), failed_spk)

    # ── Append LRW scoring columns ─────────────────────────────────────────
    lrw_df["Reading - CEFR Level"]   = [r["reading_cefr"]        for r in lrw_results]
    lrw_df["Reading Scale Score"]    = [r["reading_scale_score"]  for r in lrw_results]
    lrw_df["Reading Scale CEFR"]     = [r["reading_cefr"]         for r in lrw_results]
    lrw_df["Listening - CEFR Level"] = [r["listening_cefr"]       for r in lrw_results]
    lrw_df["Listening Scale Score"]  = [r["listening_scale_score"] for r in lrw_results]
    lrw_df["Listening Scale CEFR"]   = [r["listening_cefr"]       for r in lrw_results]
    lrw_df["Writing CEFR"]           = [r["writing_cefr"]         for r in lrw_results]
    lrw_df["Writing Scale"]          = [r["writing_scale_score"]  for r in lrw_results]
    lrw_df["Writing Scale CEFR"]     = [r["writing_cefr"]         for r in lrw_results]
    lrw_df["LRW_Report_Link"]        = lrw_links
    lrw_df.drop(columns=[c for c in ["_Scenario_Description"] if c in lrw_df.columns], inplace=True)

    # ── Append Speaking scoring columns ────────────────────────────────────
    spk_df["Speaking CEFR"]            = [r["speaking_cefr"]        for r in spk_results]
    spk_df["Speaking Scale Score"]     = [r["speaking_scale_score"] for r in spk_results]
    spk_df["Speaking Scale CEFR"]      = [r["speaking_cefr"]        for r in spk_results]
    spk_df["Speaking_Report_Link"]     = spk_links
    spk_df.drop(columns=[c for c in ["_Scenario_Description"] if c in spk_df.columns], inplace=True)

    # ── Merge on email (most reliable common key) ──────────────────────────
    # Normalise email column in both frames
    email_col = "Employee_Email_Address"
    lrw_df[email_col] = lrw_df[email_col].astype(str).str.strip()
    spk_df[email_col] = spk_df[email_col].astype(str).str.strip()

    # Columns in Speaking df that also exist in LRW df — keep only the new ones
    spk_new_cols = [c for c in spk_df.columns if c not in lrw_df.columns or c == email_col]
    merged = lrw_df.merge(spk_df[spk_new_cols], on=email_col, how="left")

    out = io.BytesIO()
    merged.to_excel(out, index=False)
    out.seek(0)

    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=cefr_reports_with_links.xlsx",
            "X-Results": str(len(lrw_results)),
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
