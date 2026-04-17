# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **data repository** for the iMocha English Proficiency Assessment (CEFR) reporting system. It contains raw assessment exports and workflow documentation — not application source code.

## Contents

- **`CEFR DATA(Sheet1).csv`** — Raw assessment data exported from the iMocha platform. 14 candidate records with 200+ columns covering test metadata, skill-level scores, and proctoring flags.
- **`CEFR Test → Score → Report Workflow v2.pdf`** — End-to-end pipeline documentation: how tests generate scores and how scores produce reports.
- **`Page 1_merged-3 4 1.pdf`** — Additional reference/sample report material.

## Data Schema

### Candidate & Test Metadata
`Employee_ID`, `Employee_Full_Name`, `Employee_Email_Address`, `Job_Role`, `Test_Id`, `Test_Name`, `Test_Status` (`Completed` / `Test Left` / `Terminated`), `Test_Score`, `Candidate_Score`, `Percentage`, `Performance_Category`, `Test_Duration(minutes)`, `Time_Taken(minutes)`, `Percentile`, `Completion_Time_Flag`

### Skill Sections and Their Columns

**Email Writing** — `Email_Writing_Grammar`, `_Readability`, `_Word-Count`, `_Vocabulary`, `_Orthographic_Control`, `_Thematic_Development`, `_Coherence`, `_Comprehension`, `Email_Writing_CEFR_Level`

**Reading** (three difficulty bands):
- `Reading_(A2)_*`, `Reading_(B1)_*`, `Reading_(B2-C1)_*`
- Per-band metrics: `Total_Score`, `Candidate_Score`, `Percentage`, `Questions`, `Answered`, `Correct`, `Wrong`

**Listening** (same three bands as Reading):
- `Listening_(A2)_*`, `Listening_(B1)_*`, `Listening_(B2-C1)_*`

**Speaking** (three workplace difficulty levels):
- `Speaking_Hard_(Workplace)_*`, `Speaking_Medium_(Workplace)_*`, `Speaking_Easy_(Personal)_*`
- Per-band metrics: `Oral_Fluency`, `Vocabulary`, `Grammar`, `Phonological_Control`, `Comprehension`, `CEFR_Level`

### Proctoring
`Proctoring_Flag`, `Window_Violation`, `Time_Violation`

## CEFR Level Mapping

Scores map to CEFR bands: A1 → A2 → B1 → B2 → C1 → C2. Each skill section independently assigns a CEFR level; the overall `Performance_Category` aggregates across sections.

## Workflow Summary (from PDF)

1. Candidates take the iMocha English Proficiency Assessment (multi-section: Email Writing, Reading, Listening, Speaking).
2. The platform scores each section and assigns per-section CEFR levels.
3. An aggregate score and `Performance_Category` are computed.
4. A candidate-facing report (PDF) is generated from the scored data.
5. Admin exports (this CSV) capture the full detail for HR/L&D analysis.
