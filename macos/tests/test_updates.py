"""Update-checker tests (no network)."""

from agentbetta.updates import checker
from agentbetta.updates.installer import parse_sha256sums, verify_checksum
from agentbetta.updates.models import ReleaseAsset, UpdateInfo
from agentbetta.updates.version import compare_versions, is_newer


def test_version_ordering():
    assert is_newer("0.2.0-alpha.2", "0.2.0-alpha.1")
    assert is_newer("0.2.0", "0.2.0-alpha.1")
    assert is_newer("0.3.0", "0.2.9")
    assert is_newer("0.2.1", "0.2.0a1")
    assert is_newer("v0.2.0-alpha.2", "0.2.0-alpha.1")


def test_version_not_newer():
    assert not is_newer("0.2.0-alpha.1", "0.2.0-alpha.1")
    assert not is_newer("0.2.0-alpha.1", "0.2.0")
    assert not is_newer("0.1.9", "0.2.0")
    assert compare_versions("1.0.0", "1.0.0") == 0


def test_select_asset_windows_prefers_setup():
    info = UpdateInfo(
        version="1",
        tag="v1",
        assets=[
            ReleaseAsset("AgentBetta-1-Windows-x64-Portable.zip", "u1"),
            ReleaseAsset("AgentBetta-1-Windows-x64-Setup.exe", "u2"),
        ],
    )
    chosen = checker.select_asset(info, "windows")
    assert chosen is not None and chosen.name.endswith("Setup.exe")


def test_select_asset_macos_prefers_dmg():
    info = UpdateInfo(
        version="1",
        tag="v1",
        assets=[
            ReleaseAsset("AgentBetta-1-macOS.zip", "u1"),
            ReleaseAsset("AgentBetta-1-macOS.dmg", "u2"),
        ],
    )
    chosen = checker.select_asset(info, "macos")
    assert chosen is not None and chosen.name.endswith(".dmg")


def test_select_asset_macos_matches_architecture(monkeypatch):
    monkeypatch.setattr(checker._platform, "machine", lambda: "arm64")
    info = UpdateInfo(
        version="1",
        tag="v1",
        assets=[
            ReleaseAsset("AgentBetta-1-macOS-x86_64.dmg", "x"),
            ReleaseAsset("AgentBetta-1-macOS-arm64.dmg", "a"),
        ],
    )
    chosen = checker.select_asset(info, "macos")
    assert chosen is not None and chosen.name.endswith("arm64.dmg")


def test_check_for_update(monkeypatch):
    monkeypatch.setattr(
        checker, "fetch_latest_release",
        lambda repo, channel="stable": UpdateInfo(version="0.3.0", tag="v0.3.0"),
    )
    assert checker.check_for_update("0.2.0a1", "x/y").version == "0.3.0"

    monkeypatch.setattr(
        checker, "fetch_latest_release",
        lambda repo, channel="stable": UpdateInfo(version="0.1.0", tag="v0.1.0"),
    )
    assert checker.check_for_update("0.2.0a1", "x/y") is None


def test_sha256sums_parse_and_verify(tmp_path):
    payload = tmp_path / "file.bin"
    payload.write_bytes(b"agentbetta")
    import hashlib

    digest = hashlib.sha256(b"agentbetta").hexdigest()
    checksums = parse_sha256sums(f"{digest}  file.bin\nother  x.txt")
    assert checksums["file.bin"] == digest
    assert verify_checksum(payload, digest) is True
    assert verify_checksum(payload, "0" * 64) is False
    assert verify_checksum(payload, None) is True
