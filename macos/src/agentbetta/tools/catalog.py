"""Full tool catalog: workspace tools plus global computer-access tools."""

from __future__ import annotations

from typing import Any, Callable

from agentbetta.permissions import policy
from agentbetta.tools.registry import ToolRegistry, ToolSpec, default_registry


def _props(**kwargs: Any) -> dict[str, Any]:
    return {"type": "object", "properties": kwargs, "additionalProperties": False}


def _str(description: str = "") -> dict[str, str]:
    return {"type": "string", "description": description}


def _int(description: str = "") -> dict[str, int | str]:
    return {"type": "integer", "description": description}


def _bool(description: str = "") -> dict[str, bool | str]:
    return {"type": "boolean", "description": description}


def _arr(description: str = "") -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}, "description": description}


def _register(registry: ToolRegistry, name: str, permission: str | None, risk: str,
              function: Callable[..., Any], description: str, parameters: dict[str, Any]) -> None:
    registry.register(ToolSpec(name, permission, risk, function, description=description, parameters=parameters))


def full_registry() -> ToolRegistry:
    """Workspace tools plus all global computer-access tools.

    Whether a global tool can actually run is enforced by the permission layer,
    not by its presence here.
    """

    from agentbetta.platform import processes as platform_proc
    from agentbetta.tools import browser as browsert
    from agentbetta.tools import filesystem as fst
    from agentbetta.tools import memory as memoryt
    from agentbetta.tools import processes as proct
    from agentbetta.tools import shell as shellt
    from agentbetta.tools import web as webt

    registry = default_registry()

    # --- global filesystem: read -------------------------------------------------
    _register(registry, "list_drives", policy.FILE_READ, "low", fst.list_drives,
              "List local Windows drives and free space.", _props())
    _register(registry, "list_directory_global", policy.FILE_READ, "low", fst.list_directory_global,
              "List a directory by absolute path anywhere the user can access.",
              _props(path=_str("Absolute directory path."), max_entries=_int("Maximum entries.")))
    _register(registry, "file_stat", policy.FILE_READ, "low", fst.file_stat,
              "Return metadata for an absolute path.", _props(path=_str("Absolute path.")))
    _register(registry, "read_text_file_global", policy.FILE_READ, "low", fst.read_text_file_global,
              "Read a UTF-8 text file at an absolute path.",
              _props(path=_str("Absolute file path."), max_chars=_int("Maximum characters to return.")))
    _register(registry, "search_files", policy.FILE_READ, "low", fst.search_files,
              "Search for files by name pattern under a root directory.",
              _props(root=_str("Root directory."), pattern=_str("Glob pattern, e.g. *.txt"),
                     max_results=_int("Maximum results."), recursive=_bool("Search recursively.")))
    _register(registry, "grep_files", policy.FILE_READ, "low", fst.grep_files,
              "Search text inside files under a root directory.",
              _props(root=_str("Root directory."), query=_str("Text to find."), max_results=_int("Maximum hits.")))
    _register(registry, "file_hash", policy.FILE_READ, "low", fst.file_hash,
              "Compute a file hash.", _props(path=_str("Absolute file path."), algorithm=_str("sha256, md5, ...")))

    # --- global filesystem: write ------------------------------------------------
    _register(registry, "create_directory", policy.FILE_WRITE, "medium", fst.create_directory,
              "Create a directory (and parents) at an absolute path.", _props(path=_str("Absolute directory path.")))
    _register(registry, "write_text_file_global", policy.FILE_WRITE, "medium", fst.write_text_file_global,
              "Write a UTF-8 text file at an absolute path. Overwriting an existing file requires approval.",
              _props(path=_str("Absolute file path."), content=_str("File content."), overwrite=_bool("Allow overwrite.")))
    _register(registry, "append_text_file", policy.FILE_WRITE, "medium", fst.append_text_file,
              "Append text to a file at an absolute path.",
              _props(path=_str("Absolute file path."), content=_str("Text to append.")))
    _register(registry, "copy_path", policy.FILE_WRITE, "medium", fst.copy_path,
              "Copy a file or directory.",
              _props(source=_str("Source absolute path."), destination=_str("Destination absolute path.")))
    _register(registry, "move_path", policy.FILE_WRITE, "medium", fst.move_path,
              "Move or rename a file or directory.",
              _props(source=_str("Source absolute path."), destination=_str("Destination absolute path.")))

    # --- global filesystem: delete ----------------------------------------------
    _register(registry, "delete_path", policy.FILE_DELETE, "high", fst.delete_path,
              "Delete a file or directory. Requires explicit approval unless pre-approved for the run.",
              _props(path=_str("Absolute path."), recursive=_bool("Delete directories recursively.")))

    # --- shell -------------------------------------------------------------------
    _register(registry, platform_proc.shell_tool_name(), policy.SHELL_EXEC, "high", shellt.run_shell,
              "Run a shell command with timeout and output caps. No elevation.",
              _props(command=_str("Shell command."), timeout=_int("Timeout seconds."), cwd=_str("Working directory.")))

    # --- processes / open --------------------------------------------------------
    _register(registry, "run_executable", policy.PROCESS_LAUNCH, "high", proct.run_executable,
              "Run an executable with a structured argument array.",
              _props(executable=_str("Executable path or name."), args=_arr("Argument array."),
                     timeout=_int("Timeout seconds."), cwd=_str("Working directory.")))
    _register(registry, "list_processes", policy.PROCESS_LAUNCH, "low", proct.list_processes,
              "List running processes.", _props(max_rows=_int("Maximum rows.")))
    _register(registry, "terminate_process", policy.PROCESS_LAUNCH, "high", proct.terminate_process,
              "Terminate a process started by AgentBetta.", _props(pid=_int("Process id.")))
    _register(registry, "open_path", policy.PROCESS_LAUNCH, "medium", proct.open_path,
              "Open a file or folder with its default application.", _props(path=_str("Absolute path.")))
    _register(registry, "reveal_path", policy.PROCESS_LAUNCH, "low", proct.reveal_path,
              "Reveal a path in File Explorer.", _props(path=_str("Absolute path.")))
    _register(registry, "open_url", policy.PROCESS_LAUNCH, "medium", proct.open_url,
              "Open a URL in the default browser.", _props(url=_str("URL.")))

    # --- web retrieval -----------------------------------------------------------
    _register(registry, "http_fetch", policy.NETWORK_HTTP, "low", webt.http_fetch,
              "Fetch a public http(s) page and return its readable text.",
              _props(url=_str("http(s) URL."), max_chars=_int("Maximum characters to return.")))

    # --- browser -----------------------------------------------------------------
    _register(registry, "browser_open", policy.BROWSER_READ, "low", browsert.browser_open,
              "Open a URL in the dedicated AgentBetta browser.", _props(url=_str("http(s) URL.")))
    _register(registry, "browser_search", policy.BROWSER_READ, "low", browsert.browser_search,
              "Perform a web search in the dedicated browser and return page text.",
              _props(query=_str("Search query."), max_chars=_int("Maximum characters.")))
    _register(registry, "browser_extract_text", policy.BROWSER_READ, "low", browsert.browser_extract_text,
              "Extract visible text from the current page (optionally a CSS selector).",
              _props(selector=_str("Optional CSS selector."), max_chars=_int("Maximum characters.")))
    _register(registry, "browser_screenshot", policy.BROWSER_READ, "low", browsert.browser_screenshot,
              "Capture a screenshot to a file.", _props(path=_str("Optional output path.")))
    _register(registry, "browser_click", policy.BROWSER_INTERACT, "medium", browsert.browser_click,
              "Click an element on the current page by CSS selector.", _props(selector=_str("CSS selector.")))
    _register(registry, "browser_fill", policy.BROWSER_INTERACT, "medium", browsert.browser_fill,
              "Fill an input field by CSS selector.",
              _props(selector=_str("CSS selector."), value=_str("Value to type.")))
    _register(registry, "browser_select", policy.BROWSER_INTERACT, "medium", browsert.browser_select,
              "Select an option in a <select> element.",
              _props(selector=_str("CSS selector."), value=_str("Option value.")))
    _register(registry, "browser_download", policy.BROWSER_DOWNLOAD, "medium", browsert.browser_download,
              "Click a link that triggers a download and save it to the AgentBetta download directory.",
              _props(selector=_str("CSS selector of the download link.")))
    _register(registry, "browser_back", policy.BROWSER_READ, "low", browsert.browser_back,
              "Navigate back in the dedicated browser.", _props())
    _register(registry, "browser_close", policy.BROWSER_READ, "low", browsert.browser_close,
              "Close the dedicated AgentBetta browser session.", _props())

    # --- long-term memory --------------------------------------------------------
    _register(registry, "remember", policy.MEMORY_WRITE, "low", memoryt.remember,
              "Save a durable fact, preference or note to global long-term memory.",
              _props(text=_str("The memory text."), kind=_str("fact, preference, episode or summary."),
                     tags=_arr("Optional tags."), importance={"type": "number", "description": "0.0-1.0."}))
    _register(registry, "recall", policy.MEMORY_READ, "low", memoryt.recall,
              "Search global long-term memory for relevant facts and notes.",
              _props(query=_str("Search query."), k=_int("Maximum results.")))

    return registry


__all__ = ["full_registry"]
