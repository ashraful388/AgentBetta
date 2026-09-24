"""Update-checker tests (no network)."""

from io import BytesIO

import pytest

from agentbetta.updates import checker, installer
from agentbetta.updates.installer import (
    InstallError,
    download_checksums,
    parse_sha256sums,
    verify_checksum,
)
from agentbetta.updates.models import ReleaseAsset, UpdateInfo
from agentbetta.updates.version import compare_versions, is_newer, is_prerelease


def test_default_update_repo():
    assert checker.DEFAULT_UPDATE_REPO == "ashraful388/AgentBetta"


def test_version_ordering():
    assert is_newer("0.2.0-alpha.2", "0.2.0-alpha.1")
    assert is_newer("0.2.0", "0.2.0-alpha.1")
    assert is_newer("0.3.0", "0.2.9")
    assert is_newer("0.2.1", "0.2.0a1")
    assert is_newer("v0.2.0-alpha.2", "0.2.0-alpha.1")
    assert is_prerelease("0.2.0-alpha.2")
    assert is_prerelease("0.2.0rc1")
    assert not is_prerelease("0.2.0")
    assert not is_prerelease("1.0.0+build.7")


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


def test_select_asset_macos_rejects_incompatible_architecture(monkeypatch):
    monkeypatch.setattr(checker._platform, "machine", lambda: "arm64")
    info = UpdateInfo(
        version="1",
        tag="v1",
        assets=[ReleaseAsset("AgentBetta-1-macOS-x86_64.dmg", "x")],
    )
    assert checker.select_asset(info, "macos") is None


def test_select_asset_macos_prefers_universal_asset(monkeypatch):
    monkeypatch.setattr(checker._platform, "machine", lambda: "arm64")
    info = UpdateInfo(
        version="1",
        tag="v1",
        assets=[
            ReleaseAsset("AgentBetta-1-macOS-x86_64.dmg", "x"),
            ReleaseAsset("AgentBetta-1-macOS-universal.dmg", "u"),
        ],
    )
    chosen = checker.select_asset(info, "macos")
    assert chosen is not None and chosen.name.endswith("universal.dmg")


def test_stable_channel_rejects_prerelease_tags(monkeypatch):
    monkeypatch.setattr(
        checker,
        "_get",
        lambda url: {"tag_name": "v0.3.0-alpha.1", "prerelease": False, "assets": []},
    )
    with pytest.raises(checker.UpdateError, match="pre-release"):
        checker.fetch_latest_release("owner/repo")


def test_prerelease_channel_follows_pagination(monkeypatch):
    first_page = [
        {"tag_name": f"v0.1.{index}", "assets": []}
        for index in range(100)
    ]
    second_page = [{"tag_name": "v0.2.0", "assets": []}]
    requested = []

    def fake_get(url):
        requested.append(url)
        return second_page if "page=2" in url else first_page

    monkeypatch.setattr(checker, "_get", fake_get)
    latest = checker.fetch_latest_release("owner/repo", channel="prerelease")
    assert latest.version == "0.2.0"
    assert len(requested) == 2


def test_prerelease_channel_uses_semantic_version_order(monkeypatch):
    releases = [
        {"tag_name": "v0.2.0-alpha.2", "assets": []},
        {"tag_name": "v0.2.0-alpha.10", "assets": []},
        {"tag_name": "v99.0.0", "draft": True, "assets": []},
    ]
    requested = []

    def fake_get(url):
        requested.append(url)
        return releases

    monkeypatch.setattr(checker, "_get", fake_get)
    latest = checker.fetch_latest_release("owner/repo", channel="prerelease")
    assert latest.version == "0.2.0-alpha.10"
    assert "per_page=100" in requested[0]


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


def test_download_checksums_requires_release_asset():
    info = UpdateInfo(version="1", tag="v1")
    with pytest.raises(InstallError, match="SHA-256"):
        download_checksums(info)


def test_download_checksums_merges_platform_manifests(monkeypatch):
    windows_digest = "1" * 64
    macos_digest = "2" * 64
    info = UpdateInfo(
        version="1",
        tag="v1",
        assets=[
            ReleaseAsset("SHA256SUMS-Windows.txt", "https://example.invalid/windows.txt"),
            ReleaseAsset("SHA256SUMS-macOS-arm64.txt", "https://example.invalid/macos.txt"),
        ],
    )
    payloads = {
        "https://example.invalid/windows.txt": f"{windows_digest}  AgentBetta.exe\n",
        "https://example.invalid/macos.txt": f"{macos_digest}  AgentBetta.dmg\n",
    }

    def fake_urlopen(request, timeout):
        return BytesIO(payloads[request.full_url].encode())

    monkeypatch.setattr(installer.urllib.request, "urlopen", fake_urlopen)
    checksums = download_checksums(info)
    assert checksums == {
        "agentbetta.exe": windows_digest,
        "agentbetta.dmg": macos_digest,
    }
