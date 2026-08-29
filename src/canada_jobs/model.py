from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Job:
    id: str
    company: str
    title: str
    location: str
    url: str
    source: str
    first_seen: str
    last_seen: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

