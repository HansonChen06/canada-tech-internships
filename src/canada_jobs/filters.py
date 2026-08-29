import re
from typing import Iterable

from .model import Job


STUDENT_RE = re.compile(r"\b(intern(ship)?|co[ -]?op|student|new grad(uate)?)\b", re.I)
TECH_RE = re.compile(
    r"\b(software|developer|engineering|data|machine learning|ai|cloud|devops|"
    r"security|cyber|qa|quality assurance|sre|site reliability|product|technical|"
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


def eligible(title: str, location: str) -> bool:
    return bool(STUDENT_RE.search(title) and TECH_RE.search(title) and CANADA_RE.search(location))


def filter_jobs(jobs: Iterable[Job]):
    return [job for job in jobs if eligible(job.title, job.location)]

