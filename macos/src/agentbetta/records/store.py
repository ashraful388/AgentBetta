from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from agentbetta.core.models import RunRecord

class RunRecorder:
    def __init__(self, directory: str): self.directory=Path(directory)
    def save(self, record: RunRecord) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        path=self.directory/f"{record.run_id}.json"
        path.write_text(json.dumps(asdict(record), indent=2, sort_keys=True), encoding="utf-8")
        return path

class FrontierStore:
    def __init__(self, path: str): self.path=Path(path)
    def append(self, row: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True)+"\n")
