"""Data structures for the update checker."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReleaseAsset:
    name: str
    url: str
    size: int = 0


@dataclass
class UpdateInfo:
    version: str
    tag: str
    notes: str = ""
    page_url: str = ""
    published_at: str = ""
    prerelease: bool = False
    assets: list[ReleaseAsset] = field(default_factory=list)

    def asset(self, predicate) -> ReleaseAsset | None:
        for candidate in self.assets:
            if predicate(candidate.name):
                return candidate
        return None

    def checksums_asset(self) -> ReleaseAsset | None:
        return self.asset(lambda name: name.lower().endswith("sha256sums.txt"))
