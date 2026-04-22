import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, LargeBinary
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CandidateReport(Base):
    __tablename__ = "candidate_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_uuid = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Candidate identity
    candidate_name = Column(String)
    candidate_id = Column(String)
    employee_email = Column(String)
    company = Column(String)
    appeared_on = Column(String)

    # Raw reading scores from CSV
    reading_a2_candidate = Column(Float)
    reading_a2_total = Column(Float)
    reading_b1_candidate = Column(Float)
    reading_b1_total = Column(Float)
    reading_b2_candidate = Column(Float)
    reading_b2_total = Column(Float)

    # Computed by scoring engine — Reading
    reading_cefr_display = Column(String)
    reading_scale_score = Column(Integer)
    reading_performance_pct = Column(Float)

    # Raw listening scores from CSV
    listening_a2_candidate = Column(Float)
    listening_a2_total = Column(Float)
    listening_b1_candidate = Column(Float)
    listening_b1_total = Column(Float)
    listening_b2_candidate = Column(Float)
    listening_b2_total = Column(Float)

    # Computed by scoring engine — Listening
    listening_cefr_display = Column(String)
    listening_scale_score = Column(Integer)
    listening_performance_pct = Column(Float)

    # Computed by scoring engine — Writing
    writing_weighted_score = Column(Float)
    writing_cefr_display   = Column(String)
    writing_scale_score    = Column(Integer)

    # PDF blob
    pdf_data = Column(LargeBinary, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class SpeakingReport(Base):
    __tablename__ = "speaking_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_uuid = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Candidate identity
    candidate_name  = Column(String)
    candidate_id    = Column(String)
    employee_email  = Column(String)
    company         = Column(String)
    appeared_on     = Column(String)

    # Raw Speaking sub-skill percentages
    speaking_fluency       = Column(Float)
    speaking_vocab         = Column(Float)
    speaking_grammar       = Column(Float)
    speaking_phonological  = Column(Float)
    speaking_comprehension = Column(Float)

    # Computed by scoring engine
    speaking_weighted_score = Column(Float)
    speaking_cefr_display   = Column(String)
    speaking_scale_score    = Column(Integer)

    # PDF blob
    pdf_data = Column(LargeBinary, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
