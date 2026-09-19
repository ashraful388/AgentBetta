"""Typed permission vocabulary.

The adaptive controller may only activate permissions that are externally
``eligible``. ``hard_denied`` permissions can never be activated by adaptation,
regardless of eligibility.
"""

from __future__ import annotations

from agentbetta.core.models import PermissionSet
from agentbetta.platform import processes as _platform_processes

FILE_READ = "file_read"
FILE_WRITE = "file_write"
FILE_DELETE = "file_delete"
PROCESS_LAUNCH = "process_launch"
SHELL_EXEC = "shell_exec"
NETWORK_HTTP = "network_http"
NETWORK_SHARE = "network_share"
BROWSER_READ = "browser_read"
BROWSER_INTERACT = "browser_interact"
BROWSER_DOWNLOAD = "browser_download"
DESKTOP_READ = "desktop_read"
DESKTOP_CONTROL = "desktop_control"
MEMORY_READ = "memory_read"
MEMORY_WRITE = "memory_write"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        FILE_READ,
        FILE_WRITE,
        FILE_DELETE,
        PROCESS_LAUNCH,
        SHELL_EXEC,
        NETWORK_HTTP,
        NETWORK_SHARE,
        BROWSER_READ,
        BROWSER_INTERACT,
        BROWSER_DOWNLOAD,
        DESKTOP_READ,
        DESKTOP_CONTROL,
        MEMORY_READ,
        MEMORY_WRITE,
    }
)

# Tools that become available for each permission.
TOOLS_FOR_PERMISSION: dict[str, tuple[str, ...]] = {
    FILE_READ: (
        "list_drives",
        "list_directory_global",
        "file_stat",
        "read_text_file_global",
        "search_files",
        "grep_files",
        "file_hash",
    ),
    FILE_WRITE: (
        "create_directory",
        "write_text_file_global",
        "append_text_file",
        "copy_path",
        "move_path",
    ),
    FILE_DELETE: ("delete_path",),
    SHELL_EXEC: (_platform_processes.shell_tool_name(),),
    PROCESS_LAUNCH: ("run_executable", "list_processes", "terminate_process", "open_path", "reveal_path"),
    NETWORK_HTTP: ("http_fetch",),
    BROWSER_READ: ("browser_open", "browser_search", "browser_extract_text", "browser_screenshot"),
    BROWSER_INTERACT: ("browser_click", "browser_fill", "browser_select"),
    BROWSER_DOWNLOAD: ("browser_download",),
    DESKTOP_READ: ("desktop_list_windows", "desktop_screenshot"),
    DESKTOP_CONTROL: ("desktop_focus_window", "desktop_click_control", "desktop_type_text"),
    MEMORY_READ: ("recall",),
    MEMORY_WRITE: ("remember",),
}
