"""Print-friendly /print view: dedicated print CSS, escaping, conversions."""

from app import db


def test_print_page_has_print_stylesheet(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    page = client.get(f"/print/{rid}").text
    assert "@media print" in page
    assert ".toolbar { display: none; }" in page
    assert "break-inside: avoid" in page


def test_print_toolbar_hidden_on_paper(client):
    """The on-screen Print button lives in .toolbar and dies in @media print."""
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/cake"}).json()["id"]
    page = client.get(f"/print/{rid}").text
    assert 'class="toolbar"' in page and "window.print()" in page


def test_print_escapes_html_in_title_and_ingredients(client, tmp_path, monkeypatch):
    client, _ = client
    monkeypatch.setenv("RECIPE_DB", str(tmp_path / "xss.db"))
    conn = db.connect()
    rid = db.save_recipe(conn, "https://evil.example/x", {
        "title": "Bad <script>alert(1)</script> Recipe",
        "ingredients": ["1 cup <b>flour</b>"],
        "steps": ["Mix &amp; bake"],
    })
    page = client.get(f"/print/{rid}").text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page
    assert "<b>flour</b>" not in page
    assert "Mix &amp;amp; bake" in page


def test_print_keeps_conversions(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()["id"]
    page = client.get(f"/print/{rid}").text
    assert "≈" in page
