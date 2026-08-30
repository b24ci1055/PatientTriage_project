"""
18 simulated patient records for the Round 2 prototype demo.

Deliberately includes (per the brief's minimum expectations):
  - Ambiguous presentation:  Ravi Menon (#4) — vague chest discomfort, one partial vital
  - Pediatric case:          Aanya Kapoor (#2), Ishaan Verma (#11)
  - Geriatric case:          Fatima Sheikh (#3), Joseph Mathew (#14)
  - Zero-history first-timer: Priya Nair (#7)

All data is synthetic and for demo purposes only.
"""

import random

PATIENTS = [
    dict(name="Ravi Menon", age=54, chief_complaint="Vague chest discomfort",
         vitals={"heart_rate": 98, "resp_rate": None, "spo2": None, "temp_c": None, "systolic_bp": None},
         has_history=False),  # ambiguous + thin data on purpose
    dict(name="Aanya Kapoor", age=4, chief_complaint="High fever and fussiness",
         vitals={"heart_rate": 150, "resp_rate": 32, "spo2": 96, "temp_c": 39.6, "systolic_bp": 88},
         has_history=True),  # pediatric, high fever — note different threshold than adult
    dict(name="Fatima Sheikh", age=78, chief_complaint="Generalized weakness",
         vitals={"heart_rate": 58, "resp_rate": 14, "spo2": 91, "temp_c": 37.6, "systolic_bp": 98},
         has_history=True),  # geriatric — blunted fever response, still concerning
    dict(name="Arjun Rao", age=35, chief_complaint="Twisted ankle playing football",
         vitals={"heart_rate": 82, "resp_rate": 16, "spo2": 99, "temp_c": 36.8, "systolic_bp": 120},
         has_history=True),  # clear low-acuity case
    dict(name="Meera Iyer", age=29, chief_complaint="Severe allergic reaction, facial swelling",
         vitals={"heart_rate": 118, "resp_rate": 26, "spo2": 90, "temp_c": 37.1, "systolic_bp": 88},
         has_history=True),  # red flag, clear high acuity
    dict(name="Vikram Singh", age=61, chief_complaint="Shortness of breath",
         vitals={"heart_rate": 105, "resp_rate": 24, "spo2": 89, "temp_c": 37.3, "systolic_bp": 142},
         has_history=True),
    dict(name="Priya Nair", age=31, chief_complaint="Abdominal pain, first visit to this hospital",
         vitals={"heart_rate": 96, "resp_rate": 18, "spo2": 97, "temp_c": 37.8, "systolic_bp": 110},
         has_history=False),  # zero-history first-timer
    dict(name="Karan Malhotra", age=45, chief_complaint="Mild headache",
         vitals={"heart_rate": 74, "resp_rate": 14, "spo2": 99, "temp_c": 36.9, "systolic_bp": 122},
         has_history=True),
    dict(name="Sneha Deshpande", age=8, chief_complaint="Fell off bicycle, arm pain",
         vitals={"heart_rate": 105, "resp_rate": 20, "spo2": 98, "temp_c": 37.0, "systolic_bp": 100},
         has_history=True),  # pediatric, moderate
    dict(name="Anil Kumar", age=68, chief_complaint="Slurred speech and facial droop",
         vitals={"heart_rate": 92, "resp_rate": 18, "spo2": 95, "temp_c": 37.0, "systolic_bp": 168},
         has_history=True),  # red flag stroke symptoms
    dict(name="Ishaan Verma", age=2, chief_complaint="Difficulty breathing, wheezing",
         vitals={"heart_rate": 158, "resp_rate": 42, "spo2": 90, "temp_c": 38.2, "systolic_bp": 84},
         has_history=False),  # pediatric + red flag + zero history: high acuity
    dict(name="Divya Pillai", age=52, chief_complaint="Nausea after eating",
         vitals={"heart_rate": 88, "resp_rate": 16, "spo2": 98, "temp_c": 37.2, "systolic_bp": 128},
         has_history=True),
    dict(name="Rohan Gupta", age=24, chief_complaint="Minor cut on hand, needs stitches",
         vitals={"heart_rate": 76, "resp_rate": 14, "spo2": 99, "temp_c": 36.7, "systolic_bp": 118},
         has_history=True),
    dict(name="Joseph Mathew", age=82, chief_complaint="Confusion, not acting like himself",
         vitals={"heart_rate": 102, "resp_rate": 22, "spo2": 90, "temp_c": 38.4, "systolic_bp": 96},
         has_history=True),  # geriatric, ambiguous but concerning combination
    dict(name="Neha Chatterjee", age=39, chief_complaint="Migraine, recurring",
         vitals={"heart_rate": 80, "resp_rate": 16, "spo2": 99, "temp_c": 36.9, "systolic_bp": 124},
         has_history=True),
    dict(name="Sameer Ali", age=57, chief_complaint="Severe bleeding from leg laceration",
         vitals={"heart_rate": 122, "resp_rate": 24, "spo2": 94, "temp_c": 36.5, "systolic_bp": 92},
         has_history=False),  # red flag, zero history
    dict(name="Lakshmi Venkatesh", age=71, chief_complaint="Unresponsive briefly, now awake",
         vitals={"heart_rate": 48, "resp_rate": 12, "spo2": 92, "temp_c": 36.2, "systolic_bp": 88},
         has_history=True),  # geriatric, red flag
    dict(name="Tanya Bhatt", age=19, chief_complaint="Sore throat, mild cough",
         vitals={"heart_rate": 78, "resp_rate": 15, "spo2": 99, "temp_c": 37.4, "systolic_bp": 112},
         has_history=True),
    dict(name="Farah Osman", age=43, chief_complaint="Persistent vomiting and dehydration",
         vitals={"heart_rate": 135, "resp_rate": 18, "spo2": 97, "temp_c": 37.5, "systolic_bp": 108},
         has_history=True),  # single critical vital -> clean ESI-3 case
    dict(name="Deepak Joshi", age=46, chief_complaint="Feeling generally unwell",
         vitals={"heart_rate": None, "resp_rate": None, "spo2": None, "temp_c": None, "systolic_bp": None},
         has_history=False),  # no vitals, no history, vague complaint -> low confidence, straight to nurse
]


def random_surge_patient():
    """Generate a lightweight synthetic patient for surge simulation."""
    complaints = ["Fever", "Cough", "Minor injury", "Dizziness", "Vomiting", "Rash", "Back pain"]
    age = random.choice([6, 15, 28, 40, 55, 70, 80])
    return dict(
        name=f"Surge Patient {random.randint(1000, 9999)}",
        age=age,
        chief_complaint=random.choice(complaints),
        vitals={
            "heart_rate": random.randint(60, 130),
            "resp_rate": random.randint(12, 28),
            "spo2": random.randint(88, 99),
            "temp_c": round(random.uniform(36.5, 39.0), 1),
            "systolic_bp": random.randint(90, 150),
        },
        has_history=random.choice([True, False]),
    )
