"""Políticas sintéticas de soporte."""

from __future__ import annotations

import json
from pathlib import Path


class PolicyBook:
    def __init__(self, path: Path) -> None:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self.meta: dict = raw["policy_set"]
        self.policies: dict[str, dict] = raw["policies"]

    @property
    def topics(self) -> list[str]:
        return list(self.policies)

    def get(self, topic: str) -> dict | None:
        policy = self.policies.get(topic)
        if policy is None:
            return None
        return {"topic": topic, **policy, "synthetic": True}

    def to_markdown(self) -> str:
        lines = [f"# {self.meta['name']} (v{self.meta['version']})", "", f"> {self.meta['notice']}", ""]
        for topic, policy in self.policies.items():
            lines.append(f"## {policy['title']} (`{topic}`)")
            lines.extend(f"- {rule}" for rule in policy["rules"])
            lines.append("")
        return "\n".join(lines)
