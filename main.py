"""
main.py
-------
CLI entry-point for the Agentic AI Career Assistant.
All logic is delegated to the AgentOrchestrator.
"""

import logging
from database import get_saved_jobs, save_job, SUPPORTED_CITIES
from company import fetch_company_research_links
from orchestrator import AgentOrchestrator
import config  # loads .env automatically

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def prompt(text: str, required: bool = True) -> str:
    """Helper that reprompts until a non-empty answer is given."""
    while True:
        val = input(text).strip().strip('"').strip("'")
        if val:
            return val
        if not required:
            return ""
        print("This field is required. Please try again.")


def main():
    print("=" * 55)
    print("    🤖  Agentic AI Career Assistant  🤖")
    print("=" * 55)

    # ── Show saved jobs ──────────────────────────────────────────
    saved = get_saved_jobs()
    if saved:
        print(f"\n[INFO] {len(saved)} saved job(s) in memory.")
        if input("View saved jobs? (y/n): ").strip().lower() == "y":
            print("\n--- Saved Jobs ---")
            for i, j in enumerate(saved, 1):
                sal = f" (₹{j['salary_lpa']} LPA)" if j["salary_lpa"] else ""
                print(f"[{i}] {j['job_title']} @ {j['company_name']} — "
                      f"{j['location']}{sal} [{j['application_status']}]")
            print("-" * 18)

    # ── 1. User Input ─────────────────────────────────────────────
    print(f"\n--- Step 1: Search Preferences ---")
    print(f"  Supported cities: {', '.join(SUPPORTED_CITIES)}")
    role = prompt("Job role (e.g. Data Engineer): ")

    from agents.location_agent import LocationIntelligenceAgent
    stored_city = LocationIntelligenceAgent().get_preferred_city()
    city_prompt = f"Preferred city"
    if stored_city:
        city_prompt += f" [default: {stored_city}]"
    city_prompt += ": "
    location = input(city_prompt).strip() or stored_city or ""
    while not location:
        location = input("City is required: ").strip()

    salary_raw = prompt("Minimum salary (LPA or raw e.g. 1200000) [Enter to skip]: ",
                        required=False)
    min_salary = None
    if salary_raw:
        try:
            min_salary = float(salary_raw.replace(",", ""))
        except ValueError:
            logging.warning("Could not parse salary — ignoring.")

    # Work preferences
    print("\n  Work mode:  1. Remote / WFH  2. Hybrid  3. Onsite")
    mode_map = {"1": "Remote", "2": "Hybrid", "3": "Onsite"}
    work_mode = mode_map.get(input("  Choice [default 1]: ").strip(), "Remote")

    notice_raw = input("  Notice period in days [default 30]: ").strip()
    try:
        notice_days = int(notice_raw) if notice_raw else 30
    except ValueError:
        notice_days = 30

    flex_raw = input("  Flexibility (Strict/Flexible) [default Strict]: ").strip()
    flexibility = "Flexible" if flex_raw.lower() == "flexible" else "Strict"

    # ── 2. Resume ─────────────────────────────────────────────────
    print("\n--- Step 2: Resume ---")
    resume_path = prompt("Path to PDF resume [Enter to skip]: ", required=False) or None

    # ── 3. Build context & run orchestrator ───────────────────────
    print("\n--- Running Agentic Pipeline ---")
    orchestrator = AgentOrchestrator()
    context = orchestrator.build_context(
        search_role=role,
        search_location=location,
        expected_salary=min_salary,
        work_mode=work_mode,
        notice_days=notice_days,
        flexibility=flexibility,
        resume_path=resume_path,
    )
    final = orchestrator.run_pipeline(context)

    # ── 4. Display results ────────────────────────────────────────
    if not final.enriched_jobs:
        print("\nNo jobs found. Try a different role or city.")
        return

    print("\n\n" + "=" * 55)
    print(final.career_advice)
    print("=" * 55)

    print(f"\n--- Source Quality ---")
    for src, stats in final.source_metadata.items():
        print(f"  [{src}] Yield: {stats['total_jobs_yielded']} | "
              f"Success Rate: {stats['success_rate_percent']}%")

    if final.skills:
        print(f"\n  Detected skills: {', '.join(final.skills)}")

    top_matches = final.enriched_jobs[:5]
    print(f"\n--- Top {len(top_matches)} Recommended Jobs ---")
    for idx, job in enumerate(top_matches, 1):
        print(f"\n[{idx}] {job['title']}")
        print(f"    Company  : {job['company']}")
        print(f"    Location : {job['location']}")
        print(f"    Salary   : {job.get('normalized_salary', 'Not Disclosed')} "
              f"({job.get('salary_comparison', 'N/A')})")
        print(f"    Source   : {job.get('source', 'N/A')}")
        print(f"    Rec Score: {job.get('recommendation_score', 0)} "
              f"(Match: {job.get('match_score', 0)} + Culture: {job.get('culture_score', 0)})")
        print(f"    Culture  : WLB={job.get('culture_wlb')} | "
              f"Growth={job.get('culture_growth')} | "
              f"Salary={job.get('culture_salary')} | "
              f"Remote={job.get('culture_remote')}")
        if job.get("culture_summary"):
            print(f"    Insight  : {job['culture_summary']}")

        # Company research links
        company = job.get("company", "")
        if company and company.lower() not in ("unknown", "n/a", ""):
            links = fetch_company_research_links(company)
            if links:
                print(f"    Links    :")
                for lnk in links:
                    print(f"      - {lnk}")

    # ── 5. Save a job ─────────────────────────────────────────────
    print("\n--- Save a Job ---")
    choice = input("Enter job number to save (or Enter to skip): ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(top_matches):
            j = top_matches[idx]
            save_job(
                job_title=j["title"],
                company_name=j["company"],
                location=j["location"],
                salary_lpa=j.get("salary_lpa"),
                source_platform=j.get("source", "Unknown"),
                application_status="Saved",
            )
            print(f"✅  '{j['title']}' saved successfully!")
        else:
            print("Invalid selection.")

    print("\n" + "=" * 55)
    print("    ✅  Pipeline Complete!  Good luck!  ")
    print("=" * 55)


if __name__ == "__main__":
    main()
