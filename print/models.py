from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PrintableMessage:
    id: int
    author_name: str
    author_avatar_url: str | None
    timestamp: str | datetime
    content: str
    image_urls: list[str] = field(default_factory=list)
    mention_map: dict[str, str] = field(default_factory=dict)
    poll: dict[str, Any] | None = None
    forward: dict[str, Any] | None = None
    is_target: bool = False


@dataclass
class PrintResult:
    success: bool
    job_id: str | None = None
    stdout: str = ""
    stderr: str = ""
    error: str | None = None
