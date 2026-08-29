import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List

from .filters import filter_jobs
from .model import Job
from .providers import fetch_source
from .render import utc_timestamp, write_outputs


def load_previous(path: Path) -> Dict[str, Job]:
    if not path.exists():
        return {}
    return {item["id"]: Job(**item) for item in json.loads(path.read_text())}


def merge(current: List[Job], previous: Dict[str, Job], today: str,
          failed_companies=None) -> List[Job]:
    failed_companies = set(failed_companies or [])
    merged = []
    for job in current:
        old = previous.get(job.id)
        merged.append(Job(job.id, job.company, job.title, job.location, job.url,
                          job.source, old.first_seen if old else today, today,
                          job.posted_date, job.deadline, job.employment_type,
                          job.workplace_type))
    # A temporary ATS/network outage is not evidence that a posting closed.
    # Keep the last known rows for failed companies until a successful refresh.
    current_ids = {job.id for job in merged}
    merged.extend(job for job in previous.values()
                  if job.company in failed_companies and job.id not in current_ids)
    return merged


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Refresh Canadian tech internship listings")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--strict", action="store_true", help="Fail if any source fails")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    sources = json.loads((root / "config" / "sources.json").read_text())
    today = date.today().isoformat()
    found, failures = [], []
    for source in sources:
        try:
            jobs = list(fetch_source(source, today))
            found.extend(jobs)
            print(f"ok: {source['company']} ({len(jobs)} postings)")
        except Exception as exc:
            failures.append(source["company"])
            print(f"warning: {source['company']}: {exc}", file=sys.stderr)
    previous = load_previous(root / "data" / "jobs.json")
    jobs = merge(filter_jobs(found, date.fromisoformat(today)), previous, today, failures)
    write_outputs(root, jobs, utc_timestamp())
    print(f"wrote {len(jobs)} eligible roles; {len(failures)} source failures")
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
