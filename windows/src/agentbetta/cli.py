from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from agentbetta import AgentBetta, PermissionSet, RuntimeConfig, Task, __version__
from agentbetta.core.models import AdaptationMode
from agentbetta.providers import FakeProvider, OllamaProvider, OpenAICompatibleProvider


def _provider(args):
    if args.provider == "fake":
        return FakeProvider()
    if args.provider == "ollama":
        return OllamaProvider(
            model=args.model or "qwen3:1.7b",
            base_url=args.base_url or "http://127.0.0.1:11434",
        )
    if args.provider == "openai-compatible":
        if not args.model or not args.base_url:
            raise SystemExit("--model and --base-url are required for openai-compatible")
        return OpenAICompatibleProvider(model=args.model, base_url=args.base_url)
    raise SystemExit(f"Unknown provider: {args.provider}")


def _permissions(args) -> PermissionSet:
    allowed = {"file_read"}
    eligible = {"file_read"}
    if args.allow_write:
        allowed.add("file_write")
        eligible.add("file_write")
    elif args.write_eligible:
        eligible.add("file_write")
    return PermissionSet(frozenset(allowed), frozenset(eligible))


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--provider", choices=["fake", "ollama", "openai-compatible"], default="fake")
    p.add_argument("--model")
    p.add_argument("--base-url")
    p.add_argument("--workspace")
    p.add_argument("--allow-write", action="store_true")
    p.add_argument(
        "--write-eligible",
        action="store_true",
        help="Allow adaptive activation of file_write if a task requires it",
    )
    p.add_argument("--mode", choices=[x.value for x in AdaptationMode], default="adaptive")
    p.add_argument("--research", action="store_true")
    p.add_argument("--privacy", action="store_true")
    p.add_argument("--memory", action="store_true",
                   help="Enable global long-term memory for this run")
    p.add_argument("--memory-path", help="Override the long-term memory file path")
    p.add_argument("--json", action="store_true", dest="as_json")


def _load_task(path: str, permissions: PermissionSet, mode: str) -> Task:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as e:
            raise SystemExit("YAML tasks require: pip install 'agentbetta[yaml]'") from e
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)
    return Task(
        objective=data.get("task") or data.get("objective") or "",
        inputs=list(data.get("inputs") or []),
        workspace=data.get("workspace"),
        permissions=permissions,
        mode=AdaptationMode(data.get("mode", mode)),
        metadata=dict(data.get("metadata") or {}),
    )


def _emit(result, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                {
                    "run_id": result.run_id,
                    "success": result.success,
                    "verified": result.verified,
                    "attempts": result.attempts,
                    "output": result.output,
                    "configuration": result.final_configuration.to_dict(),
                    "adaptations": [a.to_dict() for a in result.adaptations],
                    "contraction_candidates": [c.to_dict() for c in result.contraction_candidates],
                    "record_path": result.record_path,
                },
                indent=2,
            )
        )
    else:
        print(result.output)
        print(
            f"\n[AgentBetta] verified={result.verified} attempts={result.attempts} "
            f"run={result.run_id}"
        )
        for a in result.adaptations:
            print(f"  adaptation: {', '.join(a.changed_dimensions)} — {a.reason}")
        if result.record_path:
            print(f"  record: {result.record_path}")


def _build_direct_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agentbetta",
        description="AgentBetta adaptive AI nano-agent research runtime",
    )
    _add_common(p)
    p.add_argument("--version", action="version", version=f"AgentBetta {__version__}")
    p.add_argument("task", nargs="?")
    return p


def _build_run_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agentbetta run",
        description="Run a JSON or YAML AgentBetta task specification",
    )
    _add_common(p)
    p.add_argument("task_file")
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "run":
        args = _build_run_parser().parse_args(argv[1:])
        perms = _permissions(args)
        task = _load_task(args.task_file, perms, args.mode)
    else:
        parser = _build_direct_parser()
        args = parser.parse_args(argv)
        if not args.task:
            parser.error("provide a task or use: agentbetta run task.json")
        perms = _permissions(args)
        task = Task(
            args.task,
            workspace=args.workspace,
            permissions=perms,
            mode=AdaptationMode(args.mode),
        )

    runtime = AgentBetta(
        _provider(args),
        runtime_config=RuntimeConfig(
            research_mode=args.research,
            privacy_mode=args.privacy,
            memory_items=3 if getattr(args, "memory", False) else None,
        ),
        memory=_build_memory(args),
    )
    result = runtime.run(task)
    _emit(result, args.as_json)
    return 0 if result.success else 2


def _build_memory(args):
    if not getattr(args, "memory", False) and not getattr(args, "memory_path", None):
        return None
    from agentbetta.memory import MemoryManager, MemoryStore, default_memory_path
    from agentbetta.platform import paths as platform_paths

    path = args.memory_path or str(default_memory_path(platform_paths.local_app_data_root()))
    return MemoryManager(MemoryStore(path), auto_capture=True)


if __name__ == "__main__":
    raise SystemExit(main())
