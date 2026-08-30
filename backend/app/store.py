"""
In-memory patient queue + audit trail.

Includes a virtual clock (advance_time) so the demo can show deterioration
and re-assessment behavior without waiting in real time — click "Advance 15
min" in the UI and watch patients get re-scored and possibly escalated.

Regulatory note (assumed jurisdiction: HIPAA, US): patient records here are
synthetic. In a real deployment, this store would need encryption at rest,
role-based access control, and a retention policy; the audit log format
below (who / what / when / why) is designed to satisfy a HIPAA-style
"clinician override must be recorded" requirement, not to be a complete
compliance implementation.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional
import itertools

from .triage_engine import score_patient, TriageScore

_id_counter = itertools.count(1)
_audit_counter = itertools.count(1)

SAFE_WAIT_THRESHOLDS = {  # minutes a patient may safely wait at each ESI level
    1: 0,
    2: 15,
    3: 45,
    4: 90,
    5: 120,
}


@dataclass
class Patient:
    id: int
    name: str
    age: float
    chief_complaint: str
    vitals: dict
    has_history: bool
    arrival_time: datetime
    score: TriageScore
    last_assessed: datetime
    status: str = "waiting"          # waiting | in_review | seen
    trend: str = "stable"            # stable | worsening | improving
    vitals_history: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["arrival_time"] = self.arrival_time.isoformat()
        d["last_assessed"] = self.last_assessed.isoformat()
        d["score"] = asdict(self.score)
        d["wait_minutes"] = None  # filled in by caller with virtual clock
        return d


@dataclass
class AuditEntry:
    id: int
    patient_id: int
    patient_name: str
    action: str              # "auto_score" | "override" | "re_assessment" | "escalation"
    previous_level: Optional[int]
    new_level: Optional[int]
    reason: str
    actor: str                # "system" | nurse name
    timestamp: datetime

    def to_dict(self):
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


class TriageStore:
    def __init__(self):
        self.patients: dict[int, Patient] = {}
        self.audit_log: list[AuditEntry] = []
        self.virtual_now = datetime(2026, 1, 1, 9, 0, 0)
        self.normal_capacity = 8  # "safe" number of waiting patients at once

    # ------------------------------------------------------------------
    def _load_ratio(self) -> float:
        waiting = sum(1 for p in self.patients.values() if p.status == "waiting")
        return waiting / self.normal_capacity if self.normal_capacity else 0.0

    def add_patient(self, name, age, chief_complaint, vitals, has_history, force_fallback=False) -> Patient:
        score = score_patient(
            age=age,
            chief_complaint=chief_complaint,
            vitals=vitals,
            has_history=has_history,
            system_load_ratio=self._load_ratio(),
            force_fallback=force_fallback,
        )
        pid = next(_id_counter)
        status = "in_review" if (score.confidence_band == "low" and not score.fallback_mode) else "waiting"
        patient = Patient(
            id=pid,
            name=name,
            age=age,
            chief_complaint=chief_complaint,
            vitals=vitals,
            has_history=has_history,
            arrival_time=self.virtual_now,
            score=score,
            last_assessed=self.virtual_now,
            status=status,
            vitals_history=[{"time": self.virtual_now.isoformat(), "vitals": vitals}],
        )
        self.patients[pid] = patient
        self._log(
            patient_id=pid, patient_name=name, action="auto_score",
            previous_level=None, new_level=score.esi_level,
            reason="Initial intake scoring" + (" (fallback mode — surge/degraded data)" if score.fallback_mode else ""),
            actor="system",
        )
        return patient

    def _log(self, patient_id, patient_name, action, previous_level, new_level, reason, actor):
        entry = AuditEntry(
            id=next(_audit_counter), patient_id=patient_id, patient_name=patient_name,
            action=action, previous_level=previous_level, new_level=new_level,
            reason=reason, actor=actor, timestamp=self.virtual_now,
        )
        self.audit_log.append(entry)
        return entry

    def override(self, patient_id: int, new_level: int, nurse_name: str, reason: str):
        patient = self.patients[patient_id]
        old_level = patient.score.esi_level
        patient.score.esi_level = new_level
        patient.score.confidence = 1.0
        patient.score.confidence_band = "high"
        patient.score.contributing_factors = [f"Manually overridden by {nurse_name}: {reason}"]
        patient.status = "waiting"
        self._log(
            patient_id=patient_id, patient_name=patient.name, action="override",
            previous_level=old_level, new_level=new_level, reason=reason, actor=nurse_name,
        )
        return patient

    def update_vitals(self, patient_id: int, new_vitals: dict):
        """Simulate a recheck: re-score with updated vitals and detect trend."""
        patient = self.patients[patient_id]
        old_level = patient.score.esi_level
        merged_vitals = {**patient.vitals, **{k: v for k, v in new_vitals.items() if v is not None}}
        new_score = score_patient(
            age=patient.age, chief_complaint=patient.chief_complaint, vitals=merged_vitals,
            has_history=patient.has_history, system_load_ratio=self._load_ratio(),
        )
        patient.vitals = merged_vitals
        patient.vitals_history.append({"time": self.virtual_now.isoformat(), "vitals": merged_vitals})
        patient.last_assessed = self.virtual_now

        if new_score.esi_level < old_level:
            patient.trend = "worsening"
        elif new_score.esi_level > old_level:
            patient.trend = "improving"
        else:
            patient.trend = "stable"

        patient.score = new_score
        action = "escalation" if new_score.esi_level < old_level else "re_assessment"
        self._log(
            patient_id=patient_id, patient_name=patient.name, action=action,
            previous_level=old_level, new_level=new_score.esi_level,
            reason="Vitals recheck" + (" — trend worsening, resequenced" if action == "escalation" else ""),
            actor="system",
        )
        return patient

    def advance_time(self, minutes: int):
        """Advance the virtual clock and run the continuous-watch pass:
        any waiting patient whose wait exceeds the safe threshold for their
        level gets flagged/escalated for re-assessment."""
        self.virtual_now += timedelta(minutes=minutes)
        flagged = []
        for patient in self.patients.values():
            if patient.status != "waiting":
                continue
            wait = (self.virtual_now - patient.arrival_time).total_seconds() / 60
            threshold = SAFE_WAIT_THRESHOLDS.get(patient.score.esi_level, 120)
            if wait > threshold and patient.last_assessed < self.virtual_now - timedelta(minutes=threshold):
                # Overdue for a safety recheck — escalate one level as a
                # conservative default until a nurse actually re-assesses.
                old_level = patient.score.esi_level
                if old_level > 1:
                    patient.score.esi_level -= 1
                    patient.score.contributing_factors.append(
                        f"Wait time ({int(wait)} min) exceeded safe threshold for prior level — auto-escalated pending recheck"
                    )
                    patient.trend = "worsening"
                    self._log(
                        patient_id=patient.id, patient_name=patient.name, action="escalation",
                        previous_level=old_level, new_level=patient.score.esi_level,
                        reason=f"Wait time exceeded safe threshold ({threshold} min) for level {old_level}",
                        actor="system",
                    )
                    flagged.append(patient.id)
                patient.last_assessed = self.virtual_now
        return flagged

    def simulate_surge(self, count: int, sample_generator):
        """Add `count` additional patients at once (e.g. 3x normal volume)
        to demonstrate fallback-mode behavior under load."""
        added = []
        for _ in range(count):
            data = sample_generator()
            load_ratio = self._load_ratio()
            p = self.add_patient(
                name=data["name"], age=data["age"], chief_complaint=data["chief_complaint"],
                vitals=data["vitals"], has_history=data["has_history"],
                force_fallback=load_ratio >= 3.0,
            )
            added.append(p.id)
        return added

    def queue_snapshot(self):
        result = []
        for p in self.patients.values():
            d = p.to_dict()
            d["wait_minutes"] = round((self.virtual_now - p.arrival_time).total_seconds() / 60)
            result.append(d)
        result.sort(key=lambda x: (x["score"]["esi_level"], -x["wait_minutes"]))
        return result

    def audit_snapshot(self):
        return [e.to_dict() for e in sorted(self.audit_log, key=lambda e: e.id, reverse=True)]


store = TriageStore()
