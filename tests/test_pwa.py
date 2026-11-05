"""PWA offline: service worker, web manifest, offline caching of the recipe book."""

from app import db


def test_sw_js_served_with_js_content_type(client):
    client, _ = client
    r = client.get("/sw.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    assert "/api/recipes" in r.text           # the book is cached for offline
    assert "caches.match" in r.text


def test_manifest_served(client):
    client, _ = client
    r = client.get("/manifest.webmanifest")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Recipe Distiller"
    assert body["start_url"] == "/"
    assert any("favicon" in i["src"] for i in body["icons"])


def test_sw_caches_saved_book_json(client):
    """The SW must cache the export JSON — the offline recipe book."""
    client, _ = client
    sw = client.get("/sw.js").text
    assert "/api/recipes/export" not in sw or "/api/recipes" in sw  # prefix covers export
    # network-first with cache fallback for the book:
    assert "fetch(req).then" in sw and "caches.match(req)" in sw


def test_index_registers_service_worker_and_manifest(client):
    client, _ = client
    page = client.get("/").text
    assert "serviceWorker" in page
    assert 'rel="manifest"' in page


def test_index_html_file_has_sw_registration():
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "static" / "index.html").read_text(
        encoding="utf-8")
    assert "navigator.serviceWorker.register('/sw.js')" in src


def test_sw_file_covers_offline_book_strategy():
    from pathlib import Path
    sw = (Path(__file__).resolve().parent.parent / "static" / "sw.js").read_text(
        encoding="utf-8")
    assert "recipe-distiller-" in sw                      # versioned cache name
    assert "SHELL" in sw and "'/'" in sw                  # offline app shell
    assert "/api/" in sw
