import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from html import unescape
from typing import Dict, Iterable, List
from urllib.request import Request, urlopen

from .model import Job


USER_AGENT = "canada-tech-internships/0.1 (+https://github.com/)"
STUDENT_TITLE_RE = re.compile(r"\b(intern(ship)?|co[ -]?op|student)\b", re.I)
TECH_TITLE_RE = re.compile(
    r"\b(software|developer|engineering|data|machine learning|ai|cloud|devops|"
    r"security|cyber|qa|quality assurance|technology|technical|analytics|it|"
    r"product|design|research|automation|platform)\b", re.I)


def _date(value) -> str:
    if not value:
        return "Not specified"
    return str(value)[:10]


def _deadline(text: str) -> str:
    """Extract only explicitly labelled application deadlines."""
    if not text:
        return "Not specified"
    patterns = [
        r"(?:application\s+deadline|deadline\s+to\s+apply|apply\s+by)\s*:?\s*"
        r"([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?)",
        r"(?:application\s+deadline|deadline\s+to\s+apply|apply\s+by)\s*:?\s*"
        r"(\d{4}-\d{2}-\d{2})",
        r"(?:application\s+deadline|deadline\s+to\s+apply|apply\s+by)\s*:?\s*"
        r"(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})",
    ]
    # Also support labels rendered on one line and the value on the next.
    patterns.insert(1, r"(?:application\s+deadline|deadline\s+to\s+apply|apply\s+by)\s*:?\s*"
                       r"([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})")
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1).strip()
    return "Not specified"


def _get_json(url: str):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def _get_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def _post_json(url: str, payload):
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json",
                                               "Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def _ashby_deadline(url: str) -> str:
    """Ashby's board API omits deadlines that are embedded in the official page."""
    try:
        page = _get_text(url)
        match = re.search(r'"applicationDeadline":"(\d{4}-\d{2}-\d{2})T', page)
        return match.group(1) if match else "Not specified"
    except Exception:
        return "Not specified"


def _id(provider: str, company: str, native_id: str, url: str) -> str:
    raw = f"{provider}|{company}|{native_id}|{url}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def fetch_greenhouse(source: Dict[str, str], today: str) -> List[Job]:
    data = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{source['slug']}/jobs?content=true")
    jobs = []
    for item in data.get("jobs", []):
        location = unescape(item.get("location", {}).get("name", ""))
        url = item.get("absolute_url", "")
        jobs.append(Job(_id("greenhouse", source["company"], str(item.get("id", "")), url),
                        source["company"], unescape(item.get("title", "")), location, url,
                        "greenhouse", today, today, _date(item.get("first_published")),
                        _date(item.get("application_deadline")), "Intern / Co-op",
                        "Not specified"))
    return jobs


def fetch_lever(source: Dict[str, str], today: str) -> List[Job]:
    data = _get_json(f"https://api.lever.co/v0/postings/{source['slug']}?mode=json")
    jobs = []
    for item in data:
        categories = item.get("categories", {})
        location = categories.get("location", "") or item.get("workplaceType", "")
        url = item.get("hostedUrl", "")
        jobs.append(Job(_id("lever", source["company"], str(item.get("id", "")), url),
                        source["company"], unescape(item.get("text", "")), unescape(location), url,
                        "lever", today, today, _date_from_millis(item.get("createdAt")),
                        _deadline(item.get("descriptionPlain", "")),
                        categories.get("commitment", "Not specified") or "Not specified",
                        item.get("workplaceType", "Not specified") or "Not specified"))
    return jobs


def fetch_ashby(source: Dict[str, str], today: str) -> List[Job]:
    data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{source['slug']}")
    jobs = []
    for item in data.get("jobs", []):
        locations = [item.get("location", "")]
        locations.extend(loc.get("location", "") for loc in item.get("secondaryLocations", []))
        location = "; ".join(value for value in locations if value)
        url = item.get("jobUrl", "")
        title = unescape(item.get("title", ""))
        deadline = (_ashby_deadline(url) if re.search(r"\b(intern|co[ -]?op|student)\b", title, re.I)
                    else "Not specified")
        jobs.append(Job(_id("ashby", source["company"], str(item.get("id", "")), url),
                        source["company"], title, unescape(location), url,
                        "ashby", today, today, _date(item.get("publishedAt")),
                        deadline if deadline != "Not specified" else _deadline(item.get("descriptionPlain", "")),
                        item.get("employmentType", "Not specified") or "Not specified",
                        item.get("workplaceType", "Not specified") or "Not specified"))
    return jobs


def _plain_html(value: str) -> str:
    return unescape(re.sub(r"<[^>]+>", " ", value or ""))


def fetch_workday(source: Dict[str, str], today: str) -> List[Job]:
    host = source["host"]
    tenant = source["tenant"]
    site = source["site"]
    base = f"https://{host}/wday/cxs/{tenant}/{site}"
    summaries = {}
    # Some Workday tenants rank exact recruiting-season phrases but return no
    # Canadian results for a generic "intern" query (notably Capital One).
    for query in ("intern", "co-op", "student", "Winter 2027", "Fall 2026", "Summer 2027"):
        offset = 0
        while offset < 200:
            data = _post_json(f"{base}/jobs", {"appliedFacets": {}, "limit": 20,
                                                "offset": offset, "searchText": query})
            batch = data.get("jobPostings", [])
            for item in batch:
                summaries[item.get("externalPath", "")] = item
            offset += len(batch)
            if not batch or offset >= data.get("total", 0):
                break
    jobs = []
    def build_job(entry):
        path, summary = entry
        title = unescape(summary.get("title", ""))
        detail = _get_json(base + path).get("jobPostingInfo", {})
        location = detail.get("location", "")
        extra = detail.get("additionalLocations", []) or []
        if extra:
            location = "; ".join([location] + [str(item) for item in extra])
        url = detail.get("externalUrl") or f"https://{host}/{site}{path}"
        description = _plain_html(detail.get("jobDescription", ""))
        deadline = _date(detail.get("endDate"))
        if deadline == "Not specified":
            deadline = _deadline(description)
        return Job(_id("workday", source["company"], detail.get("jobReqId", ""), url),
                   source["company"], title, location, url, "workday", today, today,
                   _date(detail.get("startDate")), deadline,
                   detail.get("timeType", "Not specified") or "Not specified",
                   "Not specified")

    candidates = [(path, item) for path, item in summaries.items()
                  if STUDENT_TITLE_RE.search(unescape(item.get("title", "")))
                  and TECH_TITLE_RE.search(unescape(item.get("title", "")))]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(build_job, entry) for entry in candidates]
        for future in as_completed(futures):
            jobs.append(future.result())
    return jobs


def _date_from_millis(value) -> str:
    if not value:
        return "Not specified"
    from datetime import datetime, timezone
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()


def fetch_source(source: Dict[str, str], today: str = "") -> Iterable[Job]:
    today = today or date.today().isoformat()
    providers = {"greenhouse": fetch_greenhouse, "lever": fetch_lever,
                 "ashby": fetch_ashby, "workday": fetch_workday}
    if source["provider"] not in providers:
        raise ValueError(f"Unsupported provider: {source['provider']}")
    return providers[source["provider"]](source, today)
