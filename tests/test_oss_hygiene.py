"""Open-source hygiene: community files, privacy audit of the repo itself."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TRACKED = None  # filled lazily


def _tracked_files() -> list:
    global TRACKED
    if TRACKED is None:
        import subprocess
        out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        TRACKED = [Path(ROOT) / line for line in out.splitlines() if line.strip()]
    return TRACKED


def test_contributing_bilingual_and_no_russian_locale():
    doc = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "pytest" in doc
    assert "No Russian localization" in doc


def test_issue_templates_bilingual_no_russian():
    for name in ("bug_report.md", "feature_request.md"):
        tpl = (ROOT / ".github" / "ISSUE_TEMPLATE" / name).read_text(encoding="utf-8")
        assert "ukrain" in tpl.lower() or "украї" in tpl.lower()
        assert "English" in tpl
        for marker in ("по-русски", "Вставьте ссылку"):
            assert marker not in tpl


def test_security_md_exists():
    doc = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "vulnerabilit" in doc.lower() or "вразлив" in doc.lower()


def test_no_local_paths_or_secrets_in_tracked_files():
    """Privacy audit: no G:\\ paths, no Windows user dirs, no tokens in the repo."""
    import re
    suspects = re.compile(
        r"G:[/\\]|C:[/\\]Users|bigpi@|api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9]"
        r"|token\s*[:=]\s*['\"][A-Za-z0-9]|BEGIN (RSA|OPENSSH) PRIVATE KEY",
        re.IGNORECASE)
    for path in _tracked_files():
        if path.suffix in {".png", ".jpg", ".ico", ".db"} or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hits = [m.group(0) for m in suspects.finditer(text)]
        assert not hits, f"{path.name}: possible private-data leak {hits[:3]}"


def test_extension_has_no_hardcoded_urls_beyond_configurable_localhost():
    """Extension must not embed third-party endpoints; only the localhost default,
    always overridable through the options page."""
    import re
    sw = (ROOT / "extension" / "background.js").read_text(encoding="utf-8")
    opts = (ROOT / "extension" / "options.js").read_text(encoding="utf-8")
    for src in (sw, opts):
        urls = re.findall(r"https?://[^\"'\s]+", src)
        assert all(u.startswith("http://localhost") for u in urls), urls
    assert "chrome.storage.sync" in sw and "chrome.storage.sync" in opts  # configurable


def test_gitignore_covers_env_and_db():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", "*.db", "*.sqlite3", "*.env"):
        assert pattern in gi
    import subprocess
    for name in (".env", "recipes.db", "data.env"):
        r = subprocess.run(["git", "check-ignore", "-q", name], cwd=ROOT)
        assert r.returncode == 0, f"{name} is not git-ignored"


def test_readme_has_contributing_and_topics():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "CONTRIBUTING.md" in readme and "SECURITY.md" in readme
    for topic in ("recipes", "cooking", "browser-extension", "fastapi", "pwa", "self-hosted"):
        assert f"`{topic}`" in readme
