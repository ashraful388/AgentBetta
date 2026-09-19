$ErrorActionPreference = "Stop"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,yaml,documents]"
pytest
agentbetta --provider fake "Explain AgentBetta in one paragraph"
Write-Host "AgentBetta local baseline bootstrap complete."
