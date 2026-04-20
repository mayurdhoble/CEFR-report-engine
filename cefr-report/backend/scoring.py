# ──────────────────────────────────────────────────────────────────────────────
# Reading: Consecutive Pass Chain + Scale Score
# Source: CEFR Test → Score → Report Workflow v2
# ──────────────────────────────────────────────────────────────────────────────

# Pass thresholds (marks required to pass each band)
READING_THRESHOLDS = {
    "A2": 5,   # out of 6  (75%)
    "B1": 6,   # out of 9  (65%)
    "B2": 7,   # out of 11 (63%)
}

# Scale score lookup per outcome
# denominator = total marks pool used in the performance% formula
READING_BANDS = {
    "BelowA2": {"denominator": 6,  "band_start": 100, "band_range": 19},
    "A2":      {"denominator": 15, "band_start": 120, "band_range": 19},
    "B1":      {"denominator": 26, "band_start": 140, "band_range": 19},
    "B2":      {"denominator": 26, "band_start": 160, "band_range": 9},
    "B2+":     {"denominator": 26, "band_start": 170, "band_range": 9},
}

# Human-readable labels
PROFICIENCY_LABELS = {
    "Pre A1":  "Pre-Beginner User",
    "BelowA2": "Beginner User",
    "A1":      "Beginner User",
    "A2":      "Elementary User",
    "B1":      "Intermediate User",
    "B2":      "Independent User",
    "B2+":     "Independent User",
    "C1":      "Proficient User",
    "C2":      "Mastery",
}

# Candidate capability statements for Reading per CEFR outcome
READING_CAPABILITY = {
    "BelowA2": (
        "Candidate can recognise isolated familiar words and very basic phrases. "
        "Understanding of written English is limited to simple labels and short instructions."
    ),
    "A2": (
        "Candidate can understand short, simple texts and find specific, predictable information "
        "in simple everyday material such as emails, notices, and short descriptions."
    ),
    "B1": (
        "Candidate can read straightforward factual texts on subjects of personal and professional "
        "interest and understand the main points of clearly written messages and reports."
    ),
    "B2": (
        "Candidate reads, understands, and responds to texts on everyday and workplace topics at a "
        "moderate pace. Can understand articles with specific viewpoints, though some complex details "
        "may be lost."
    ),
    "B2+": (
        "Candidate reads with a high degree of independence, adapting style and speed to different "
        "text types. Can handle most unfamiliar vocabulary through context without a dictionary."
    ),
}

READING_SKILL_DEFINITION = (
    "Reading reflects the ability to understand written English texts on everyday and workplace "
    "topics. The score is based on the ability to operate at functional speeds to extract details "
    "and main ideas, infer the message, and construct meaning."
)


# ── Listening ──────────────────────────────────────────────────────────────────

LISTENING_BANDS = {
    "BelowA2": {"denominator": 6,  "band_start": 100, "band_range": 19},
    "A2":      {"denominator": 15, "band_start": 120, "band_range": 19},
    "B1":      {"denominator": 26, "band_start": 140, "band_range": 19},
    "B2":      {"denominator": 26, "band_start": 160, "band_range": 9},
    "B2+":     {"denominator": 26, "band_start": 170, "band_range": 9},
}

LISTENING_CAPABILITY = {
    "BelowA2": (
        "Candidate can follow very slow, carefully articulated speech and recognise familiar words "
        "and basic phrases when spoken clearly and with repetition."
    ),
    "A2": (
        "Candidate can understand phrases and expressions related to everyday topics such as "
        "personal information, simple instructions, and short announcements."
    ),
    "B1": (
        "Candidate can understand the main points of clear standard speech on familiar workplace "
        "and personal topics, including short narratives and straightforward factual information."
    ),
    "B2": (
        "Candidate can follow extended speech and complex lines of argument on workplace topics, "
        "though may miss detail when speech is fast or heavily accented."
    ),
    "B2+": (
        "Candidate can follow extended speech with ease, understanding implicit meaning, tone, and "
        "attitude. Can handle a variety of accents and speaking speeds in professional contexts."
    ),
}

LISTENING_SKILL_DEFINITION = (
    "Listening reflects the ability to understand spoken English in everyday and workplace contexts. "
    "The score is based on the ability to extract key information, follow discourse structure, "
    "and comprehend meaning from audio at natural speaking speeds."
)


# ── Writing ────────────────────────────────────────────────────────────────────

WRITING_BANDS = {
    "Pre A1": {"band_start": 80,  "band_range": 19},
    "A1":     {"band_start": 100, "band_range": 19},
    "A2":     {"band_start": 120, "band_range": 19},
    "B1":     {"band_start": 140, "band_range": 19},
    "B2":     {"band_start": 160, "band_range": 19},
    "C1":     {"band_start": 180, "band_range": 19},
    "C2":     {"band_start": 200, "band_range": 30},
}

WRITING_CAPABILITY = {
    "Pre A1": (
        "Candidate cannot yet produce recognisable written English. "
        "Writing is limited to isolated words or copied text with no coherent structure."
    ),
    "A1": (
        "Candidate can write simple isolated phrases and sentences about personal details "
        "using basic vocabulary and very simple sentence structures."
    ),
    "A2": (
        "Candidate can write short, simple messages and fill in basic forms. "
        "Can produce simple connected sentences on familiar topics using common connectors."
    ),
    "B1": (
        "Candidate can write straightforward connected text on familiar subjects. "
        "Can produce personal letters and structured emails describing experiences and opinions."
    ),
    "B2": (
        "Candidate can write clear, detailed text on a variety of subjects. "
        "Can write essays or reports that develop an argument and highlight key points."
    ),
    "C1": (
        "Candidate can express themselves in clear, well-structured text with controlled use of "
        "organisational patterns and connectors. Writing shows flexibility and precision."
    ),
    "C2": (
        "Candidate can write clear, smooth-flowing, complex texts with an appropriate and effective "
        "style. Can produce sophisticated reports and articles with a high degree of accuracy."
    ),
}

WRITING_SKILL_DEFINITION = (
    "Writing reflects the ability to produce clear, structured, and accurate written English "
    "in workplace and everyday contexts. The score is based on grammar, vocabulary, coherence, "
    "comprehension, orthographic control, and thematic development."
)


def run_writing_score(
    grammar: float,
    vocabulary: float,
    comprehension: float,
    orthographic: float,
    coherence: float,
    thematic: float,
) -> dict:
    """
    Computes Writing CEFR level and Cambridge scale score from sub-skill percentages (0-100 each).

    Weightages: Grammar 20%, Vocabulary 10%, Comprehension 30%,
                Orthographic 10%, Coherence 20%, Thematic 10%.
    Band lookup: direct threshold (no pass chain).
    """
    weighted = round(
        grammar      * 0.20 +
        vocabulary   * 0.10 +
        comprehension * 0.30 +
        orthographic * 0.10 +
        coherence    * 0.20 +
        thematic     * 0.10,
        1,
    )

    if weighted > 90:
        display = "C2"
    elif weighted >= 76:
        display = "C1"
    elif weighted >= 56:
        display = "B2"
    elif weighted >= 47:
        display = "B1"
    elif weighted >= 35:
        display = "A2"
    elif weighted >= 20:
        display = "A1"
    else:
        display = "Pre A1"

    band        = WRITING_BANDS[display]
    scale_score = band["band_start"] + round(weighted * band["band_range"] / 100)

    return {
        "cefr_display":         display,
        "scale_score":          scale_score,
        "performance_pct":      weighted,
        "proficiency_label":    PROFICIENCY_LABELS.get(display, ""),
        "capability_statement": WRITING_CAPABILITY.get(display, ""),
        "skill_definition":     WRITING_SKILL_DEFINITION,
    }


def run_listening_pass_chain(
    a2_candidate: float,
    b1_candidate: float,
    b2_candidate: float,
    a2_total: float = 6,
    b1_total: float = 9,
    b2_total: float = 11,
) -> dict:
    """Runs the consecutive pass chain for Listening. Same logic as Reading."""
    import math
    a2_candidate = int(round(a2_candidate))
    b1_candidate = int(round(b1_candidate))
    b2_candidate = int(round(b2_candidate))
    a2_total     = max(int(round(a2_total)), 1)
    b1_total     = max(int(round(b1_total)), 1)
    b2_total     = max(int(round(b2_total)), 1)

    a2_thresh = math.ceil(0.75 * a2_total)
    b1_thresh = math.ceil(0.65 * b1_total)
    b2_thresh = math.ceil(0.63 * b2_total)

    if a2_candidate < a2_thresh:
        display     = "BelowA2"
        total_marks = a2_candidate
    elif b1_candidate < b1_thresh:
        display     = "A2"
        total_marks = a2_candidate + b1_candidate
    elif b2_candidate < b2_thresh:
        display     = "B1"
        total_marks = a2_candidate + b1_candidate + b2_candidate
    elif b2_candidate <= 8:
        display     = "B2"
        total_marks = a2_candidate + b1_candidate + b2_candidate
    else:
        display     = "B2+"
        total_marks = a2_candidate + b1_candidate + b2_candidate

    band            = LISTENING_BANDS[display]
    denominator     = band["denominator"]
    performance_pct = round(total_marks / denominator * 100, 1)
    scale_score     = band["band_start"] + round(performance_pct * band["band_range"] / 100)

    return {
        "cefr_display":       display,
        "scale_score":        scale_score,
        "performance_pct":    performance_pct,
        "total_marks":        total_marks,
        "denominator":        denominator,
        "proficiency_label":  PROFICIENCY_LABELS.get(display, ""),
        "capability_statement": LISTENING_CAPABILITY.get(display, ""),
        "skill_definition":   LISTENING_SKILL_DEFINITION,
    }


def run_reading_pass_chain(
    a2_candidate: float,
    b1_candidate: float,
    b2_candidate: float,
    a2_total: float = 6,
    b1_total: float = 9,
    b2_total: float = 11,
) -> dict:
    """
    Runs the consecutive pass chain for Reading.

    Args:
        a2_candidate: marks scored at A2 band
        b1_candidate: marks scored at B1 band
        b2_candidate: marks scored at B2 band
        a2_total / b1_total / b2_total: max marks per band from the CSV
            (used to compute dynamic thresholds so any test version works)

    Returns dict with:
        cefr_display    – e.g. "B1", "B2+", "BelowA2"
        scale_score     – integer on Cambridge 100-230 scale
        performance_pct – float used as "Total Score x/100" in report
        total_marks     – numerator used in formula
        denominator     – denominator used in formula
    """
    a2_candidate = int(round(a2_candidate))
    b1_candidate = int(round(b1_candidate))
    b2_candidate = int(round(b2_candidate))
    a2_total     = max(int(round(a2_total)), 1)
    b1_total     = max(int(round(b1_total)), 1)
    b2_total     = max(int(round(b2_total)), 1)

    # Dynamic thresholds: same pass-rate percentages as workflow doc,
    # applied to the actual max marks in this test version.
    # Workflow: A2 75% (≥5/6), B1 65% (≥6/9), B2 63% (≥7/11)
    import math
    a2_thresh = math.ceil(0.75 * a2_total)
    b1_thresh = math.ceil(0.65 * b1_total)
    b2_thresh = math.ceil(0.63 * b2_total)

    # A1 → skip_pass (auto pass, always)
    a2_pass = a2_candidate >= a2_thresh
    b1_pass = b1_candidate >= b1_thresh
    b2_pass = b2_candidate >= b2_thresh

    if not a2_pass:
        # Case 1 — BelowA2
        display = "BelowA2"
        total_marks = a2_candidate
    elif not b1_pass:
        # Case 2 — A2
        display = "A2"
        total_marks = a2_candidate + b1_candidate
    elif not b2_pass:
        # Case 3 — B1
        display = "B1"
        total_marks = a2_candidate + b1_candidate + b2_candidate
    elif b2_candidate <= 8:
        # Case 4 — B2 (7 or 8 out of 11)
        display = "B2"
        total_marks = a2_candidate + b1_candidate + b2_candidate
    else:
        # Case 5 — B2+ (9, 10, or 11 out of 11)
        display = "B2+"
        total_marks = a2_candidate + b1_candidate + b2_candidate

    band = READING_BANDS[display]
    denominator = band["denominator"]
    performance_pct = round(total_marks / denominator * 100, 1)
    scale_score = band["band_start"] + round(performance_pct * band["band_range"] / 100)

    return {
        "cefr_display": display,
        "scale_score": scale_score,
        "performance_pct": performance_pct,
        "total_marks": total_marks,
        "denominator": denominator,
        "proficiency_label": PROFICIENCY_LABELS.get(display, ""),
        "capability_statement": READING_CAPABILITY.get(display, ""),
        "skill_definition": READING_SKILL_DEFINITION,
    }
