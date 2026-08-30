"""
Core triage scoring engine for PatientTriage.ai.

Design principles (from the Round 1 concept + Round 2 requirements):
  1. Score + explicit confidence band, never a bare number.
  2. Age-banded vital thresholds (pediatric / adult / geriatric) — a single
     adult-calibrated model is treated as a safety risk, not a shortcut.
  3. Bias toward escalation under uncertainty: ties and borderline cases
     round to the MORE urgent ESI level, never the less urgent one.
  4. Fallback mode: under a surge or when confidence machinery itself can't
     be trusted, fall back to a simple deterministic ESI rule table instead
     of guessing.
  5. Continuous watch: waiting patients are re-assessed based on elapsed
     wait time vs. a safe threshold for their level, or on updated vitals.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AgeBand(str, Enum):
    PEDIATRIC = "pediatric"   # < 12
    ADULT = "adult"           # 12-65
    GERIATRIC = "geriatric"   # > 65


def age_band(age: float) -> AgeBand:
    if age < 12:
        return AgeBand.PEDIATRIC
    if age > 65:
        return AgeBand.GERIATRIC
    return AgeBand.ADULT


# ---------------------------------------------------------------------------
# Age-banded vital thresholds.
# Each entry: (band) -> dict of vital -> (low_critical, low_warn, high_warn, high_critical)
# A value outside the *_warn band contributes urgency; outside *_critical contributes more.
# These are illustrative, simplified reference ranges — not clinical advice.
# ---------------------------------------------------------------------------
VITAL_THRESHOLDS = {
    AgeBand.PEDIATRIC: {
        "heart_rate":      (70, 90, 140, 160),   # bpm
        "resp_rate":       (15, 18, 30, 40),     # breaths/min
        "spo2":            (85, 92, 100, 100),   # % (low is bad; high bound unused)
        "temp_c":          (35.0, 36.0, 38.0, 39.5),
        "systolic_bp":     (70, 80, 120, 140),
    },
    AgeBand.ADULT: {
        "heart_rate":      (45, 55, 100, 130),
        "resp_rate":       (8, 12, 20, 28),
        "spo2":            (88, 94, 100, 100),
        "temp_c":          (35.0, 36.1, 38.0, 39.5),
        "systolic_bp":     (80, 90, 140, 180),
    },
    AgeBand.GERIATRIC: {
        "heart_rate":      (45, 55, 95, 120),
        "resp_rate":       (10, 12, 22, 30),
        "spo2":            (85, 90, 100, 100),
        "temp_c":          (35.0, 35.8, 37.8, 39.0),  # blunted febrile response
        "systolic_bp":     (90, 100, 150, 190),
    },
}

RED_FLAG_COMPLAINTS = {
    "chest pain", "chest discomfort", "difficulty breathing", "shortness of breath",
    "stroke symptoms", "facial droop", "slurred speech", "severe bleeding",
    "unresponsive", "seizure", "severe allergic reaction",
}

# Standard ESI-style vital + expected-resources -> level lookup, used as the
# FALLBACK when confidence machinery is bypassed (surge / degraded mode).
# This is intentionally simple and deterministic.
def fallback_esi_level(vitals: dict, chief_complaint: str, band: AgeBand) -> int:
    cc = (chief_complaint or "").lower()
    if any(flag in cc for flag in RED_FLAG_COMPLAINTS):
        return 2
    abnormal = _count_abnormal_vitals(vitals, band)
    if abnormal >= 2:
        return 2
    if abnormal == 1:
        return 3
    return 4


def _count_abnormal_vitals(vitals: dict, band: AgeBand) -> int:
    thresholds = VITAL_THRESHOLDS[band]
    count = 0
    for vital, value in vitals.items():
        if value is None or vital not in thresholds:
            continue
        low_crit, low_warn, high_warn, high_crit = thresholds[vital]
        if value < low_crit or value > high_crit:
            count += 2
        elif value < low_warn or value > high_warn:
            count += 1
    return count


@dataclass
class TriageScore:
    esi_level: int                  # 1 (most urgent) - 5 (least urgent)
    confidence: float                # 0.0 - 1.0
    confidence_band: str              # "low" | "medium" | "high"
    contributing_factors: list[str] = field(default_factory=list)
    fallback_mode: bool = False
    recommended_recheck_minutes: int = 60


def _confidence_band(score: float) -> str:
    if score < 0.55:
        return "low"
    if score < 0.75:
        return "medium"
    return "high"


def _recheck_interval(level: int) -> int:
    # Minutes between recommended vitals rechecks while waiting, scaled to risk.
    return {1: 5, 2: 10, 3: 15, 4: 30, 5: 45}.get(level, 45)


def score_patient(
    age: float,
    chief_complaint: str,
    vitals: dict,
    has_history: bool,
    system_load_ratio: float = 1.0,
    force_fallback: bool = False,
) -> TriageScore:
    """
    Compute an ESI-aligned severity score with an explicit confidence band.

    system_load_ratio: current queue size / normal safe capacity. Above the
    SURGE_THRESHOLD, the engine drops into fallback mode rather than trusting
    a confidence-weighted read on a system it can no longer be sure is being
    fed reliable, timely data.
    """
    band = age_band(age)
    SURGE_THRESHOLD = 3.0

    fallback = force_fallback or system_load_ratio >= SURGE_THRESHOLD
    if fallback:
        level = fallback_esi_level(vitals, chief_complaint, band)
        return TriageScore(
            esi_level=level,
            confidence=1.0,
            confidence_band="high",
            contributing_factors=[
                "Fallback mode active (surge or degraded data pipeline) — using standard ESI rule table, not the confidence-weighted model."
            ],
            fallback_mode=True,
            recommended_recheck_minutes=_recheck_interval(level),
        )

    factors: list[str] = []
    present_vitals = {k: v for k, v in vitals.items() if v is not None}
    total_expected = len(VITAL_THRESHOLDS[band])
    completeness = len(present_vitals) / total_expected if total_expected else 0.0

    abnormal_score = 0
    borderline_hits = 0
    thresholds = VITAL_THRESHOLDS[band]
    for vital, value in present_vitals.items():
        if vital not in thresholds:
            continue
        low_crit, low_warn, high_warn, high_crit = thresholds[vital]
        if value < low_crit or value > high_crit:
            abnormal_score += 2
            factors.append(f"{vital.replace('_', ' ')} critically abnormal for {band.value} range")
        elif value < low_warn or value > high_warn:
            abnormal_score += 1
            borderline_hits += 1
            factors.append(f"{vital.replace('_', ' ')} borderline for {band.value} range")

    cc = (chief_complaint or "").lower()
    red_flag = any(flag in cc for flag in RED_FLAG_COMPLAINTS)
    if red_flag:
        abnormal_score += 3
        factors.append(f"Chief complaint contains a red-flag symptom pattern ('{chief_complaint}')")

    # --- ESI level mapping (bias toward escalation on ties) ---
    if abnormal_score >= 5:
        level = 1
    elif abnormal_score >= 3:
        level = 2
    elif abnormal_score >= 2:
        level = 3
    elif abnormal_score >= 1:
        level = 4
    else:
        level = 5

    # --- Confidence calculation ---
    # Lower confidence when: data is incomplete, case is borderline, or
    # patient has no prior history to sanity-check against.
    confidence = 1.0
    confidence -= (1 - completeness) * 0.45
    if borderline_hits > 0:
        confidence -= 0.10 * min(borderline_hits, 2)
        factors.append("Score sits near a threshold boundary — confidence reduced")
    if not has_history:
        confidence -= 0.10
        factors.append("No prior health record on file for this patient")
    confidence = max(0.05, min(1.0, confidence))

    # Escalation bias under uncertainty: if confidence is low AND the level
    # would otherwise be a borderline 3/4/5, nudge one level more urgent
    # rather than leaving a low-confidence patient at low priority.
    if confidence < 0.5 and level >= 3:
        level -= 1
        factors.append("Escalated one level due to low confidence (bias toward escalation under uncertainty)")

    if not present_vitals:
        factors.append("No vitals captured yet — scored on chief complaint only")

    return TriageScore(
        esi_level=level,
        confidence=round(confidence, 2),
        confidence_band=_confidence_band(confidence),
        contributing_factors=factors,
        fallback_mode=False,
        recommended_recheck_minutes=_recheck_interval(level),
    )
