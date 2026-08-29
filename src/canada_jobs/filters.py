import re
from datetime import date, datetime, timedelta
from typing import Iterable

from .model import Job


STUDENT_RE = re.compile(r"\b(intern(ship)?|co[ -]?op|student|new grad(uate)?)\b", re.I)
TECH_RE = re.compile(
    r"\b(software|developer|engineering|data|machine learning|ai|cloud|devops|"
    r"security|cyber|qa|quality assurance|sre|site reliability|product|technical|research|"
    r"ux|ui|design|analytics|business intelligence|it)\b",
    re.I,
)
CANADA_RE = re.compile(
    r"\b(canada|remote.*canada|alberta|british columbia|manitoba|new brunswick|"
    r"newfoundland|nova scotia|ontario|prince edward island|quebec|saskatchewan|"
    r"toronto|vancouver|montreal|montréal|ottawa|waterloo|kitchener|calgary|"
    r"edmonton|victoria|halifax|winnipeg|burnaby|mississauga|markham)\b",
    re.I,
)


MAX_POST_AGE_DAYS = 180


def _parse_date(value: str):
    if not value or value == "Not specified":
        return None
    cleaned = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", value, flags=re.I)
    cleaned = re.sub(r"\s+at\s+.*$", "", cleaned, flags=re.I).strip()
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%B %d %Y", "%d %B %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            pass
    return None


def eligible(title: str, location: str) -> bool:
    return bool(STUDENT_RE.search(title) and TECH_RE.search(title) and CANADA_RE.search(location))


def currently_recruiting(job: Job, today=None) -> bool:
    today = today or date.today()
    posted = _parse_date(job.posted_date)
    deadline = _parse_date(job.deadline)
    if deadline and deadline < today:
        return False
    if posted and posted < today - timedelta(days=MAX_POST_AGE_DAYS):
        return False
    return True


def filter_jobs(jobs: Iterable[Job], today=None):
    return [job for job in jobs
            if eligible(job.title, job.location) and currently_recruiting(job, today)]
