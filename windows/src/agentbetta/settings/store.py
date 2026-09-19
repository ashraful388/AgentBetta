"""Secret-free application settings store.

Writes are atomic (temp file + ``os.replace``) so a crash cannot corrupt the
settings file. The store refuses to persist secret-like values.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from agentbetta.settings.models import AppSettings, assert_no_secret_values


class SettingsStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            # utf-8-sig tolerates a BOM (e.g. a file edited in Notepad).
            raw = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            # A corrupt settings file must never prevent the app from starting.
            # Preserve it for inspection and fall back to defaults.
            try:
                self.path.replace(self.path.with_name(self.path.name + ".corrupt"))
            except OSError:
                pass
            return AppSettings()
        return AppSettings.from_dict(raw)

    def save(self, settings: AppSettings) -> Path:
        data = settings.to_dict()
        assert_no_secret_values(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=self.path.name + ".", suffix=".tmp", dir=str(self.path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        return self.path
