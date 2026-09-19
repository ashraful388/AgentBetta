from __future__ import annotations
import re
from pathlib import Path
from .models import Task, TaskFeatures


_FILE_EXTENSION = re.compile(
    r"\.(txt|md|markdown|csv|tsv|json|ya?ml|xml|html?|pdf|docx?|xlsx?|pptx?|py|js|ts|"
    r"log|ini|cfg|toml|rtf|odt)\b",
    re.IGNORECASE,
)
_PATH_LIKE = re.compile(r"((?<![A-Za-z0-9])[A-Za-z]:[\\/]|\\\\|~[\\/]|\.\.?[\\/]|/[\w.-]+/)")
_URL = re.compile(r"https?://\S+", re.IGNORECASE)
# Browsing/real-time-web vocabulary. Word-boundary matched so that e.g.
# "opposite" does not trigger "site" and "monochrome" does not trigger "chrome".
_BROWSER_WORDS = re.compile(
    r"\b(browse|browser|web|webpage|website|site|navigate|chrome|chromium|firefox|"
    r"safari|internet|online|google|lookup|url|http|https|latest)\b",
    re.IGNORECASE,
)
# Local-computer vocabulary. Word-boundary matched so "pc" does not match
# "spec" and "drive" is not required to be an exact token elsewhere.
_PC_WORDS = re.compile(
    r"\b(pc|computer|drive|disk|filesystem|file system|my files|local files|"
    r"hard drive|desktop|documents|downloads|directory|machine)\b",
    re.IGNORECASE,
)


def characterize(task: Task) -> TaskFeatures:
    text = task.objective.lower()
    file_words = ("file", "folder", "pdf", "document", "csv", "workspace", "repository", "repo")
    write_words = ("write", "edit", "modify", "patch", "create file", "save", "fix the code")
    code_words = ("code", "python", "test", "bug", "repository", "repo", "function", "class")
    calc_words = ("calculate", "compute", "sum", "multiply", "average", "percentage", "equation")
    net_words = ("web", "internet", "online", "latest", "search the web", "url", "http")
    shell_words = ("powershell", "shell", "command line", "terminal", "cmd ", "script")
    process_words = ("run program", "launch", "open the app", "executable", "process", "start program")
    delete_words = ("delete", "remove file", "remove the file", "erase", "clean up files")
    memory_words = ("remember", "recall", "memory", "preference", "i prefer", "my name is", "as we discussed", "previously")
    complex_words = ("compare", "analyze", "synthesize", "prove", "debug", "evaluate", "critique")
    reasoning = min(2, sum(1 for w in complex_words if w in text))
    path_probe = _URL.sub(" ", task.objective)
    est = len(task.objective)
    for inp in task.inputs:
        try:
            p=Path(inp)
            if p.exists() and p.is_file():
                est += min(p.stat().st_size, 200_000)
        except OSError:
            pass
    return TaskFeatures(
        needs_files=(
            bool(task.inputs)
            or any(w in text for w in file_words)
            or bool(_FILE_EXTENSION.search(text))
            or bool(_PATH_LIKE.search(path_probe))
            or bool(_PC_WORDS.search(text))
        ),
        needs_write=any(w in text for w in write_words),
        needs_code=any(w in text for w in code_words),
        needs_calculation=any(w in text for w in calc_words) or bool(re.search(r"\d+\s*[*+/\-]\s*\d+", text)),
        needs_network=any(w in text for w in net_words) or bool(_BROWSER_WORDS.search(text)),
        needs_shell=any(w in text for w in shell_words),
        needs_process=any(w in text for w in process_words),
        needs_delete=any(w in text for w in delete_words),
        needs_memory=any(w in text for w in memory_words),
        reasoning_level=reasoning,
        requested_structured_output=any(w in text for w in ("json", "yaml", "table", "structured")),
        estimated_input_chars=est,
    )
