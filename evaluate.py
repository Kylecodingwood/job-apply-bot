"""
Job Evaluator for job-apply-bot
Reads jobs.json, filters ineligible jobs, scores the rest, outputs a ranked list.
"""

import json
import re
from pathlib import Path

JOBS_PATH = Path(__file__).parent / "jobs.json"
OUT_PATH  = Path(__file__).parent / "evaluated_jobs.json"

# Graduation constraint — grad programmes must start ON OR AFTER this
GRAD_MIN_YEAR  = 2028
GRAD_MIN_MONTH = 1   # January

# ── Fit scoring ────────────────────────────────────────────────────────────────

FIT_POSITIVE = {
    "java": 2, "spring boot": 2,
    "spring": 1, "python": 1, "backend": 1,
    "rest api": 1, "rest": 1, "api": 1,
    "postgresql": 1, "mysql": 1, "docker": 1,
    "software engineer": 1, "software developer": 1,
    "dublin": 1, "remote": 1,
}

FIT_NEGATIVE = {
    "senior": -2, "lead developer": -2, "engineering manager": -2,
    "5 years": -2, "5+ years": -2, "7 years": -2, "10 years": -2,
    "minimum 3 years": -1, "3+ years": -1,
}

# Job titles that are clearly off-topic for a software/backend engineer
OFF_TOPIC_TITLE_KEYWORDS = [
    "civil engineer", "geotechnical", "structural engineer", "electrical engineer",
    "mechanical engineer", "quantity surveyor", "site engineer", "field engineer",
    "finance graduate", "finance data", "financial analyst", "accounting", "auditor",
    "tax", "actuar",
    "hotel", "hospitality", "tourism",
    "legal", "solicitor", "barrister", "paralegal",
    "nurse", "nursing", "clinical", "critical care", "pharmacy", "pharmacist",
    "medical", "healthcare", "physiotherap", "occupational therap", "speech therap",
    "ergonomic",
    "marketing", "sales graduate", "business development representative",
    "hr ", "human resources", "organisational development", "recruitment",
    "procurement", "supply chain",
    "rail ", "transport planner", "urban planner",
    "chemistry", "biology", "biochem", "lab technician",
    "maintenance graduate", "operations engineer intern (field)",
]

# ── Eligibility patterns ───────────────────────────────────────────────────────

UK_LOCATIONS = [
    "united kingdom", "england", "scotland", "wales",
    "london", "manchester", "birmingham", "bristol",
    "edinburgh", "glasgow", " uk", "(uk)", ", uk",
]

NO_SPONSORSHIP_PHRASES = [
    "no sponsorship", "cannot sponsor", "will not sponsor",
    "not able to sponsor", "sponsorship is not available",
    "must be eligible to work", "must have the right to work",
    "must already have the right", "eu citizen", "irish citizen",
    "uk citizen", "british citizen", "must hold an eu",
]

MONTHS = {
    "january": 1,  "jan": 1,
    "february": 2, "feb": 2,
    "march": 3,    "mar": 3,
    "april": 4,    "apr": 4,
    "may": 5,
    "june": 6,     "jun": 6,
    "july": 7,     "jul": 7,
    "august": 8,   "aug": 8,
    "september": 9,"sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11,"nov": 11,
    "december": 12,"dec": 12,
}

START_CONTEXT_WORDS = [
    "start", "commence", "begin", "join", "intake",
    "cohort", "joining date", "programme start",
]


# ── Helper functions ───────────────────────────────────────────────────────────

def is_off_topic(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in OFF_TOPIC_TITLE_KEYWORDS)


def is_uk(location: str, description: str) -> bool:
    loc = location.lower()
    if any(kw in loc for kw in ["ireland", "dublin", "remote"]):
        return False
    return any(uk in loc for uk in UK_LOCATIONS)


def detect_role_type(title: str, description: str) -> str:
    text = f"{title} {description[:600]}".lower()
    intern_kws = ["intern", "internship", "placement", "work placement", "co-op", "work experience"]
    grad_kws   = ["graduate programme", "graduate program", "grad programme",
                  "graduate scheme", "graduate role", "new grad",
                  "entry level", "entry-level", "recently graduated", "final year"]
    for kw in intern_kws:
        if kw in text:
            return "INTERN"
    for kw in grad_kws:
        if kw in text:
            return "GRAD"
    # fallback: title only
    t = title.lower()
    if any(k in t for k in ["intern", "internship", "placement"]):
        return "INTERN"
    if any(k in t for k in ["graduate", "grad"]):
        return "GRAD"
    return "UNKNOWN"


def extract_start_dates(description: str) -> list[tuple[int, int]]:
    """Return (month, year) pairs found near start-date context words."""
    desc  = description.lower()
    dates = []
    pattern = (
        r"(january|february|march|april|may|june|july|august|september|"
        r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
        r"\s+(\d{4})"
    )
    for m in re.finditer(pattern, desc):
        month = MONTHS.get(m.group(1), 0)
        year  = int(m.group(2))
        if not (2025 <= year <= 2030):
            continue
        ctx_start = max(0, m.start() - 120)
        context   = desc[ctx_start : m.end() + 60]
        if any(kw in context for kw in START_CONTEXT_WORDS):
            dates.append((month, year))
    return dates


def grad_start_too_early(description: str) -> tuple[bool, str]:
    for month, year in extract_start_dates(description):
        if year < GRAD_MIN_YEAR or (year == GRAD_MIN_YEAR and month < GRAD_MIN_MONTH):
            month_name = next(
                (k.capitalize() for k, v in MONTHS.items() if v == month and len(k) > 3),
                str(month),
            )
            return True, f"Start {month_name} {year} — before graduation (Jan 2028)"
    return False, ""


def has_no_sponsorship(description: str) -> bool:
    desc = description.lower()
    return any(phrase in desc for phrase in NO_SPONSORSHIP_PHRASES)


def fit_score(title: str, description: str) -> int:
    text  = f"{title} {description}".lower()
    score = sum(pts for kw, pts in FIT_POSITIVE.items() if kw in text)
    score += sum(pts for kw, pts in FIT_NEGATIVE.items() if kw in text)
    return max(0, score)


# ── Core evaluation ────────────────────────────────────────────────────────────

def evaluate(job: dict) -> dict:
    title    = job.get("title", "")
    location = job.get("location", "")
    desc     = job.get("description", "") or job.get("desc_preview", "")

    out = {**job, "eligible": True, "skip_reason": "", "role_type": "UNKNOWN", "fit_score": 0}

    # 1. Off-topic field
    if is_off_topic(title):
        out["eligible"]    = False
        out["skip_reason"] = "Off-topic field (not software/tech)"
        return out

    # 2. UK location
    if is_uk(location, desc):
        out["eligible"]    = False
        out["skip_reason"] = "UK location (Stamp 1G not valid)"
        return out

    # 3. Role type
    out["role_type"] = detect_role_type(title, desc)

    # 4. Sponsorship restriction
    if has_no_sponsorship(desc):
        out["eligible"]    = False
        out["skip_reason"] = "No sponsorship / must already have right to work"
        return out

    # 5. Graduate start date check
    if out["role_type"] == "GRAD":
        too_early, reason = grad_start_too_early(desc)
        if too_early:
            out["eligible"]    = False
            out["skip_reason"] = reason
            return out

    # 6. Fit score
    out["fit_score"] = fit_score(title, desc)

    return out


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if not JOBS_PATH.exists():
        print("❌  jobs.json not found. Run discover.py first.")
        return

    jobs = json.loads(JOBS_PATH.read_text())
    print(f"\n📊  Evaluating {len(jobs)} jobs...\n")

    evaluated = [evaluate(j) for j in jobs]

    skipped  = [j for j in evaluated if not j["eligible"]]
    eligible = [j for j in evaluated if j["eligible"]]
    eligible.sort(key=lambda x: x["fit_score"], reverse=True)
    display  = [j for j in eligible if j["fit_score"] >= 1]

    # Print skipped summary
    print(f"❌  Skipped {len(skipped)} ineligible:")
    for j in skipped[:8]:
        print(f"   {j['title'][:38]:<38}  {j['skip_reason']}")
    if len(skipped) > 8:
        print(f"   ... and {len(skipped) - 8} more")

    # Print eligible table
    print(f"\n✅  {len(display)} jobs ready to apply (fit ≥ 2):\n")
    print(f"{'#':<4} {'Fit':<5} {'Type':<7} {'Title':<45} {'Company':<25} {'Location'}")
    print("─" * 115)
    for i, job in enumerate(display, 1):
        t = job["title"][:43]   + ".." if len(job["title"])    > 45 else job["title"]
        c = job["company"][:23] + ".." if len(job["company"])  > 25 else job["company"]
        l = job["location"][:18]+ ".." if len(job["location"]) > 20 else job["location"]
        print(f"{i:<4} {job['fit_score']:<5} {job['role_type']:<7} {t:<45} {c:<25} {l}")

    # Save full evaluation
    OUT_PATH.write_text(json.dumps(evaluated, indent=2, ensure_ascii=False))
    print(f"\n💾  Saved to evaluated_jobs.json")
    print(f"\n👉  Tell Claude the number and I'll open the form.\n")


if __name__ == "__main__":
    main()
