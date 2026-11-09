"""
Job Discovery for job-apply-bot
Searches Indeed & LinkedIn for matching jobs, prints a ranked list.

Usage:
  uv run python discover.py                      # normal keyword search
  uv run python discover.py --tier               # search companies from company_list.md
  uv run python discover.py --tier S+            # search a specific tier only
"""

import json
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

PROFILE_PATH      = Path(__file__).parent / "profile.json"
APPLIED_PATH      = Path(__file__).parent / "applied_companies.json"
COMPANY_LIST_PATH = Path(__file__).parent / "company_list.md"

# ── Load profile ──────────────────────────────────────────────────────────────

def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        print("❌  profile.json not found.")
        exit(1)
    return json.loads(PROFILE_PATH.read_text())


# ── Parse company_list.md → {tier: [company, ...]} ───────────────────────────

def parse_company_list() -> dict[str, list[str]]:
    """Return ordered dict of tier -> [company names]."""
    if not COMPANY_LIST_PATH.exists():
        return {}
    text = COMPANY_LIST_PATH.read_text()
    tiers = {}
    current_tier = None
    for line in text.splitlines():
        # Heading lines like "## S+ 大厂 / Big Tech"
        h = re.match(r"^##\s+(.+)", line)
        if h:
            current_tier = h.group(1).strip()
            tiers[current_tier] = []
            continue
        # Company lines: "Google · Microsoft · Amazon"  or table rows
        if current_tier and line.strip() and not line.startswith("|") and not line.startswith(">") and not line.startswith("#"):
            # Extract names separated by · or ,
            names = re.split(r"[·,]", line)
            for n in names:
                n = n.strip().strip("*_()")
                # Remove trailing notes like "(评论补充：...)"
                n = re.sub(r"\(.*?\)", "", n).strip()
                if n and len(n) > 1:
                    tiers[current_tier].append(n)
    return tiers


def get_applied_companies() -> set[str]:
    """Return lowercase company names already in applied_companies.json."""
    if not APPLIED_PATH.exists():
        return set()
    applied = json.loads(APPLIED_PATH.read_text())
    return {a["company"].lower() for a in applied}


def print_unapplied_companies(tiers: dict, applied: set[str]):
    """D-mode: print companies from the list not yet applied to."""
    print("\n📋  company_list.md — 还没投过的公司：\n")
    for tier, companies in tiers.items():
        unapplied = [c for c in companies if c.lower() not in applied]
        if not unapplied:
            continue
        # Compact display: max 8 per line
        chunks = [unapplied[i:i+8] for i in range(0, len(unapplied), 8)]
        print(f"  [{tier}]")
        for chunk in chunks:
            print("    " + "  ·  ".join(chunk))
    print()


# ── Search config ─────────────────────────────────────────────────────────────

SEARCHES = [
    # Graduate programmes
    {"query": "Software Engineering Graduate Programme", "location": "Dublin, Ireland"},
    {"query": "Software Developer Graduate",             "location": "Dublin, Ireland"},
    {"query": "IT Graduate Programme",                   "location": "Ireland"},
    {"query": "Technology Graduate Programme",           "location": "Ireland"},
    {"query": "Graduate Software Engineer",              "location": "Ireland"},
    # Internships — general
    {"query": "Software Engineering Intern",    "location": "Dublin, Ireland"},
    {"query": "Backend Developer Intern",       "location": "Dublin, Ireland"},
    {"query": "Software Developer Intern",      "location": "Ireland"},
    {"query": "Software Intern Summer 2027",    "location": "Ireland"},
    {"query": "IT Intern",                      "location": "Dublin, Ireland"},
    # Internships — specialised
    {"query": "Cloud Engineer Intern",          "location": "Ireland"},
    {"query": "DevOps Intern",                  "location": "Ireland"},
    {"query": "Full Stack Developer Intern",    "location": "Ireland"},
    {"query": "Data Engineer Intern",           "location": "Ireland"},
    # Junior roles
    {"query": "Junior Software Developer",      "location": "Ireland"},
    {"query": "Junior Java Developer",          "location": "Ireland"},
    {"query": "Junior Backend Developer",       "location": "Dublin, Ireland"},
    # Broader
    {"query": "Java Developer Graduate",   "location": "Ireland"},
    {"query": "Python Developer Intern",   "location": "Dublin, Ireland"},
]

SITES   = ["indeed", "linkedin"]
HOURS   = 336   # last 14 days
RESULTS = 25    # per search per site


# ── Scoring ───────────────────────────────────────────────────────────────────

KEYWORDS = [
    "java", "python", "spring", "spring boot", "backend", "software engineer",
    "rest", "api", "sql", "postgresql", "mysql", "docker", "linux", "git",
    "graduate", "intern", "entry level", "junior", "ireland", "dublin",
]

def score(title: str, description: str) -> int:
    text = f"{title} {description}".lower()
    return sum(1 for kw in KEYWORDS if kw in text)


# ── Scrape helper ─────────────────────────────────────────────────────────────

def scrape(searches: list[dict], seen_urls: set) -> list[dict]:
    from jobspy import scrape_jobs
    results = []
    for s in searches:
        print(f"   Searching: \"{s['query']}\" in {s['location']}")
        try:
            df = scrape_jobs(
                site_name=SITES,
                search_term=s["query"],
                location=s["location"],
                results_wanted=RESULTS,
                hours_old=HOURS,
                description_format="markdown",
                country_indeed="ireland",
                verbose=0,
            )
            for _, row in df.iterrows():
                url = str(row.get("job_url", ""))
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                title    = str(row.get("title", ""))    or ""
                company  = str(row.get("company", ""))  or ""
                location = str(row.get("location", "")) or ""
                desc     = str(row.get("description", "")) or ""
                apply_url = str(row.get("job_url_direct", "")) or url
                site      = str(row.get("site", ""))
                date_posted = row.get("date_posted")
                date_str = (date_posted.strftime("%Y-%m-%d")
                            if hasattr(date_posted, "strftime")
                            else (str(date_posted) if date_posted and str(date_posted) != "NaT" else ""))

                loc_lower = location.lower()
                if location and "ireland" not in loc_lower and "dublin" not in loc_lower and "remote" not in loc_lower:
                    continue

                results.append({
                    "title":        title,
                    "company":      company,
                    "location":     location,
                    "url":          apply_url if apply_url != "nan" else url,
                    "site":         site,
                    "date_posted":  date_str,
                    "score":        score(title, desc),
                    "desc_preview": desc[:120].replace("\n", " ") if desc else "",
                    "description":  desc,
                })
        except Exception as e:
            print(f"   ⚠️  Failed: {e}")
    return results


def print_results(results: list[dict]):
    print(f"\n✅  Found {len(results)} unique jobs:\n")
    print(f"{'#':<4} {'Score':<6} {'Title':<45} {'Company':<25} {'Location':<20} {'Site'}")
    print("─" * 120)
    for i, job in enumerate(results, 1):
        t = job["title"][:43]   + ".." if len(job["title"])    > 45 else job["title"]
        c = job["company"][:23] + ".." if len(job["company"])  > 25 else job["company"]
        l = job["location"][:18]+ ".." if len(job["location"]) > 20 else job["location"]
        print(f"{i:<4} {job['score']:<6} {t:<45} {c:<25} {l:<20} {job['site']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    tier_mode   = "--tier" in args
    tier_filter = None
    if tier_mode:
        idx = args.index("--tier")
        if idx + 1 < len(args) and not args[idx + 1].startswith("--"):
            tier_filter = args[idx + 1]

    profile  = load_profile()
    name     = profile.get("personal", {}).get("first_name", "")
    tiers    = parse_company_list()
    applied  = get_applied_companies()

    # ── Tier mode (A): targeted company search ────────────────────────────────
    if tier_mode:
        label = f" [{tier_filter}]" if tier_filter else ""
        print(f"\n🏢  Tier search{label} from company_list.md...\n")

        tier_searches = []
        for tier_name, companies in tiers.items():
            if tier_filter and not tier_name.startswith(tier_filter):
                continue
            for company in companies:
                if company.lower() in applied:
                    continue  # already applied, skip
                tier_searches.append({
                    "query":    f"{company} software intern OR graduate",
                    "location": "Ireland",
                })

        if not tier_searches:
            print("No unapplied companies found for this tier.")
            return

        seen_urls: set = set()
        results = scrape(tier_searches, seen_urls)
        if not results:
            print("\n❌  No results found.")
            return

        results.sort(key=lambda x: x["score"], reverse=True)
        print_results(results)

        out = Path(__file__).parent / "jobs.json"
        out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\n💾  Saved to jobs.json")
        print(f"\n👉  Run evaluate.py next, then tell Claude the number.\n")
        return

    # ── Normal mode: keyword search + D-mode summary ─────────────────────────
    print(f"\n🔍  Searching jobs for {name}...\n")
    seen_urls: set = set()
    results = scrape(SEARCHES, seen_urls)

    if not results:
        print("\n❌  No results found. Try again later or check your internet connection.")
    else:
        results.sort(key=lambda x: x["score"], reverse=True)
        print_results(results)
        out = Path(__file__).parent / "jobs.json"
        out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\n💾  Full list saved to jobs.json")
        print(f"\n👉  To apply: run evaluate.py, then tell Claude the number.\n")

    # D-mode: always show unapplied companies from the list
    if tiers:
        print_unapplied_companies(tiers, applied)


if __name__ == "__main__":
    main()
