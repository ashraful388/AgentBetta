from __future__ import annotations
import json
from pathlib import Path
from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.providers.fake import FakeProvider


def main() -> None:
    tasks = json.loads(Path(__file__).with_name("tasks").joinpath("smoke.json").read_text())
    runtime = AgentBetta(provider=FakeProvider(), runtime_config=RuntimeConfig(research_mode=True))
    out=[]
    for item in tasks:
        result=runtime.run(item["task"], workspace=item.get("workspace"))
        out.append({"id": item["id"], "success": result.success, "verified": result.verified,
                    "attempts": result.attempts, "final_configuration": result.final_configuration.to_dict()})
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
