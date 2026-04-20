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

# Human-readable proficiency labels (displayed under the CEFR badge)
PROFICIENCY_LABELS = {
    "Pre A1":  "Beginner",
    "BelowA2": "Beginner",
    "A1":      "Beginner",
    "A2":      "Elementary",
    "B1":      "Intermediate",
    "B2":      "Upper-intermediate",
    "B2+":     "Upper-intermediate+",
    "C1":      "Advanced",
    "C2":      "Mastery",
}

# Candidate capability statements for Reading per CEFR outcome
READING_CAPABILITY = {
    "BelowA2": (
        "Candidate has not yet demonstrated sufficient comprehension to understand simple written "
        "material on familiar topics consistently. At this level, there is not enough demonstrated "
        "ability to distinguish between different stages of beginner proficiency."
    ),
    "A2": (
        "Candidate understands simple texts on familiar topics when the language is straightforward. "
        "Longer or less predictable material will cause difficulty."
    ),
    "B1": (
        "Candidate understands factual texts on familiar topics, following how ideas connect and what "
        "the writer intends. Unfamiliar or complex material may present difficulty."
    ),
    "B2": (
        "Candidate understands complex texts on everyday and workplace topics, grasping not only what "
        "is stated but what is meant. Highly abstract or densely argued material may cause some loss "
        "of meaning."
    ),
    "B2+": (
        "Candidate understands complex texts on everyday and workplace topics with confidence, "
        "handling a range of writing styles with minimal loss of meaning. At this level, there is "
        "not enough demonstrated ability to distinguish between upper-intermediate and advanced "
        "proficiency."
    ),
}

READING_SKILL_DEFINITION = (
    "Reading reflects the ability to understand written English in everyday and workplace situations. "
    "The score reflects how well a candidate can make sense of what they read — both what is directly "
    "stated and what is implied — assessed through progressively challenging questions across multiple "
    "proficiency levels."
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
        "Candidate has not yet demonstrated sufficient comprehension to follow simple spoken exchanges "
        "on familiar topics consistently, even when speech is slow and clear. At this level, there is "
        "not enough demonstrated ability to distinguish between different stages of beginner proficiency."
    ),
    "A2": (
        "Candidate understands simple spoken exchanges on familiar topics when speech is slow and clear. "
        "Faster or less predictable speech will cause difficulty."
    ),
    "B1": (
        "Candidate follows clear, standard speech on familiar topics well enough to understand what "
        "was discussed and what needs to happen next. Rapid or accented speech may cause some loss."
    ),
    "B2": (
        "Candidate follows extended speech on concrete and abstract topics, understanding the "
        "information as well as the speaker's attitude and intent. Very fast or unstructured speech "
        "may occasionally cause difficulty."
    ),
    "B2+": (
        "Candidate follows extended speech on concrete and abstract topics with confidence, handling "
        "a range of spoken formats with minimal loss of information. At this level, there is not "
        "enough demonstrated ability to distinguish between upper-intermediate and advanced proficiency."
    ),
}

LISTENING_SKILL_DEFINITION = (
    "Listening reflects the ability to follow and understand spoken English in everyday and workplace "
    "situations. The score reflects how well a candidate can pick up on key information and details, "
    "assessed through progressively challenging questions across multiple proficiency levels."
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
        "The text contains basic expressions (often lacking any awareness of grammatical "
        "conventions). The topic of the text is almost unintelligible."
    ),
    "A1": (
        "The text contains very simple expressions and uses some basic structures in one-clause "
        "sentences with some omission or reduction of elements. It often deviates from the topic "
        "through circumlocutions."
    ),
    "A2": (
        "The text contains sufficient vocabulary to briefly elaborate on the topic. It uses simple "
        "structures with a few errors, but it is generally clear in terms of the message being conveyed."
    ),
    "B1": (
        "The topic is expressed using a good range of vocabulary with some circumlocutions. "
        "However, there are fewer diversions and there are no errors with regard to simple structures."
    ),
    "B2": (
        "The text uses a good range of vocabulary &amp; the formulation varies to avoid repetition. "
        "The topic is described using mostly simple language structures and some complex grammatical "
        "forms without diversions."
    ),
    "C1": (
        "The text contains a broad range of complex grammatical structures appropriately and with "
        "considerable flexibility. The vocabulary used is appropriate and varied and the topic is "
        "well-elaborated on sequentially with various cohesive devices."
    ),
    "C2": (
        "The text is a comprehensive description of the topic using a wide range of vocabulary "
        "&amp; grammatical structures precisely to emphasize, differentiate, and eliminate ambiguity. "
        "The text exhibits the users' ease with the language."
    ),
}

WRITING_SKILL_DEFINITION = (
    "Writing reflects the ability to understand a given prompt and produce a written response that "
    "is clear, organised, and fit for purpose. The score is based on the ability to develop ideas "
    "coherently, use vocabulary and grammar accurately, and maintain orthographic control across formats."
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
