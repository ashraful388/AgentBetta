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

    def checksums_assets(self) -> list[ReleaseAsset]:
        return [
            candidate
            for candidate in self.assets
            if candidate.name.lower().startswith("sha256sums")
            and candidate.name.lower().endswith(".txt")
        ]

    def checksums_asset(self) -> ReleaseAsset | None:
        assets = self.checksums_assets()
        return assets[0] if assets else None
