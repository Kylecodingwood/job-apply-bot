"""
Job Discovery for job-apply-bot
Searches Indeed & LinkedIn for matching jobs, prints a ranked list.
"""

import json
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

# ── Load profile ─────────────────────────────────────────────────────────────

PROFILE_PATH = Path(__file__).parent / "profile.json"

def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        print("❌  profile.json not found. Run ./setup.sh first.")
        exit(1)
    return json.loads(PROFILE_PATH.read_text())


# ── Search config ─────────────────────────────────────────────────────────────

SEARCHES = [
    # Graduate programmes
    {"query": "Software Engineering Graduate Programme", "location": "Dublin, Ireland"},
    {"query": "Software Developer Graduate", "location": "Dublin, Ireland"},
    {"query": "IT Graduate Programme", "location": "Ireland"},
    # Internships
    {"query": "Software Engineering Intern", "location": "Dublin, Ireland"},
    {"query": "Backend Developer Intern", "location": "Dublin, Ireland"},
    {"query": "Software Developer Intern", "location": "Ireland"},
    # Broader
    {"query": "Java Developer Graduate", "location": "Ireland"},
    {"query": "Python Developer Intern", "location": "Dublin, Ireland"},
]

SITES   = ["indeed", "linkedin"]
HOURS   = 168   # last 7 days
RESULTS = 20    # per search per site


# ── Scoring ──────────────────────────────────────────────────────────────────

KEYWORDS = [
    "java", "python", "spring", "spring boot", "backend", "software engineer",
    "rest", "api", "sql", "postgresql", "mysql", "docker", "linux", "git",
    "graduate", "intern", "entry level", "junior", "ireland", "dublin",
]

def score(title: str, description: str) -> int:
    """Simple keyword match score against profile skills."""
    text = f"{title} {description}".lower()
    return sum(1 for kw in KEYWORDS if kw in text)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    from jobspy import scrape_jobs
    import pandas as pd

    profile = load_profile()
    name = profile.get("personal", {}).get("first_name", "")
    print(f"\n🔍  Searching jobs for {name}...\n")

    all_results = []
    seen_urls = set()

    for s in SEARCHES:
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
                title = str(row.get("title", "")) or ""
                company = str(row.get("company", "")) or ""
                location = str(row.get("location", "")) or ""
                desc = str(row.get("description", "")) or ""
                apply_url = str(row.get("job_url_direct", "")) or url
                site = str(row.get("site", ""))

                # Skip clearly non-Ireland results
                loc_lower = location.lower()
                if location and "ireland" not in loc_lower and "dublin" not in loc_lower and "remote" not in loc_lower:
                    continue

                all_results.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": apply_url if apply_url != "nan" else url,
                    "site": site,
                    "score": score(title, desc),
                    "desc_preview": desc[:120].replace("\n", " ") if desc else "",
                })

        except Exception as e:
            print(f"   ⚠️  Failed: {e}")

    if not all_results:
        print("\n❌  No results found. Try again later or check your internet connection.")
        return

    # Sort by score descending
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Print results
    print(f"\n✅  Found {len(all_results)} unique jobs:\n")
    print(f"{'#':<4} {'Score':<6} {'Title':<45} {'Company':<25} {'Location':<20} {'Site'}")
    print("─" * 120)

    for i, job in enumerate(all_results, 1):
        title = job["title"][:43] + ".." if len(job["title"]) > 45 else job["title"]
        company = job["company"][:23] + ".." if len(job["company"]) > 25 else job["company"]
        location = job["location"][:18] + ".." if len(job["location"]) > 20 else job["location"]
        print(f"{i:<4} {job['score']:<6} {title:<45} {company:<25} {location:<20} {job['site']}")

    # Save to jobs.json for reference
    out = Path(__file__).parent / "jobs.json"
    out.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\n💾  Full list saved to jobs.json")
    print(f"\n👉  To apply: copy the URL from jobs.json and paste it to Claude.\n")


if __name__ == "__main__":
    main()
