import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .model import Job


HEADER = """# Canada Tech Internships 🇨🇦

A community-maintained list of software, data, AI, product, design, IT, and
cybersecurity **internship / co-op** roles located in Canada.

> Automatically refreshed every day. Always confirm eligibility and deadlines
> on the employer's official posting before applying.
> Listings older than 180 days or past their stated deadline are automatically removed.

## Open roles

<!-- JOBS:START -->
"""


def markdown(jobs: List[Job], updated_at: str) -> str:
    lines = [HEADER.rstrip(), "", f"_Last updated: {updated_at} UTC · {len(jobs)} open roles_", ""]
    lines += ["| Company | Role | Location | Work mode | Type | Posted | Deadline | Apply |",
              "|---|---|---|---|---|---|---|---|"]
    if not jobs:
        lines.append("| — | No matching roles found today | — | — | — | — | — | — |")
    for job in sorted(jobs, key=lambda x: (x.company.lower(), x.title.lower())):
        values = [job.company, job.title, job.location or "Not specified",
                  job.workplace_type, job.employment_type, job.posted_date,
                  job.deadline]
        values = [value.replace("|", "\\|").replace("\n", " ") for value in values]
        lines.append(f"| {values[0]} | {values[1]} | {values[2]} | {values[3]} | {values[4]} | {values[5]} | {values[6]} | [Apply]({job.url}) |")
    lines += ["", "<!-- JOBS:END -->", "", "## Data", "",
              "Machine-readable exports: [`data/jobs.json`](data/jobs.json) and [`data/jobs.csv`](data/jobs.csv).",
              "", "## Contributing", "",
              "Add or correct an ATS source in `config/sources.json`, then open a pull request. See [`CONTRIBUTING.md`](CONTRIBUTING.md).",
              "", "## License", "", "MIT"]
    return "\n".join(lines) + "\n"


def write_outputs(root: Path, jobs: List[Job], updated_at: str) -> None:
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "jobs.json").write_text(json.dumps([j.to_dict() for j in jobs], indent=2, ensure_ascii=False) + "\n")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(Job.__dataclass_fields__))
    writer.writeheader()
    writer.writerows(j.to_dict() for j in jobs)
    (data_dir / "jobs.csv").write_text(buffer.getvalue())
    (root / "README.md").write_text(markdown(jobs, updated_at))


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
