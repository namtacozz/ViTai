from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.request import urlopen


@dataclass(frozen=True)
class UpdateCheckConfig:
    enabled: bool
    owner: str
    repo: str


@dataclass(frozen=True)
class ReleaseInfo:
    tag_name: str
    html_url: str


def check_latest_release(config: UpdateCheckConfig, opener=urlopen) -> ReleaseInfo | None:
    if not config.enabled or not config.owner.strip() or not config.repo.strip():
        return None
    url = f"https://api.github.com/repos/{config.owner.strip()}/{config.repo.strip()}/releases/latest"
    with opener(url) as response:
        data = json.loads(response.read().decode("utf-8"))
    return ReleaseInfo(tag_name=str(data.get("tag_name", "")), html_url=str(data.get("html_url", "")))
