"""MV3 browser extension: manifest, service worker, options page, ?url= auto-extract."""

import json
from pathlib import Path

EXT = Path(__file__).resolve().parent.parent / "extension"


def test_manifest_is_valid_mv3():
    m = json.loads((EXT / "manifest.json").read_text(encoding="utf-8"))
    assert m["manifest_version"] == 3
    assert m["name"] == "Recipe Distiller"
    assert "background" in m and "service_worker" in m["background"]
    assert "action" in m
    # least privilege: no host permissions, no content scripts
    assert "host_permissions" not in m
    assert not m.get("content_scripts")


def test_service_worker_opens_distiller_with_url():
    sw = (EXT / "background.js").read_text(encoding="utf-8")
    assert "chrome.action.onClicked" in sw
    assert "encodeURIComponent(tab.url)" in sw       # page URL passed safely
    assert "/?url=" in sw                            # distiller deep link
    assert "chrome.storage.sync" in sw               # configurable server address


def test_options_page_persists_server_address():
    opts = (EXT / "options.js").read_text(encoding="utf-8")
    assert "chrome.storage.sync.set" in opts
    assert "chrome.storage.sync.get" in opts
    html = (EXT / "options.html").read_text(encoding="utf-8")
    assert 'id="distiller"' in html


def test_index_auto_extracts_from_url_param(client):
    client, _ = client
    page = client.get("/").text
    assert "URLSearchParams(location.search)" in page   # reads ?url=
    assert "distill(" in page                            # shared extraction path


def test_extension_readme_has_install_steps():
    doc = (EXT / "README.md").read_text(encoding="utf-8")
    assert "Load unpacked" in doc and "chrome://extensions" in doc
    assert "MANIFEST V3" in doc.upper()
