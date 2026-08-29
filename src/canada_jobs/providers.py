import hashlib
import json
from datetime import date
from html import unescape
from typing import Dict, Iterable, List
from urllib.request import Request, urlopen

from .model import Job


USER_AGENT = "canada-tech-internships/0.1 (+https://github.com/)"


def _get_json(url: str):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def _id(provider: str, company: str, native_id: str, url: str) -> str:
    raw = f"{provider}|{company}|{native_id}|{url}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def fetch_greenhouse(source: Dict[str, str], today: str) -> List[Job]:
    data = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{source['slug']}/jobs")
    jobs = []
    for item in data.get("jobs", []):
        location = unescape(item.get("location", {}).get("name", ""))
        url = item.get("absolute_url", "")
        jobs.append(Job(_id("greenhouse", source["company"], str(item.get("id", "")), url),
                        source["company"], unescape(item.get("title", "")), location, url,
                        "greenhouse", today, today))
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
                        "lever", today, today))
    return jobs


def fetch_ashby(source: Dict[str, str], today: str) -> List[Job]:
    data = _get_json(f"https://api.ashbyhq.com/posting-api/job-board/{source['slug']}")
    jobs = []
    for item in data.get("jobs", []):
        locations = [item.get("location", "")]
        locations.extend(loc.get("location", "") for loc in item.get("secondaryLocations", []))
        location = "; ".join(value for value in locations if value)
        url = item.get("jobUrl", "")
        jobs.append(Job(_id("ashby", source["company"], str(item.get("id", "")), url),
                        source["company"], unescape(item.get("title", "")), unescape(location), url,
                        "ashby", today, today))
    return jobs


def fetch_source(source: Dict[str, str], today: str = "") -> Iterable[Job]:
    today = today or date.today().isoformat()
    providers = {"greenhouse": fetch_greenhouse, "lever": fetch_lever, "ashby": fetch_ashby}
    if source["provider"] not in providers:
        raise ValueError(f"Unsupported provider: {source['provider']}")
    return providers[source["provider"]](source, today)
