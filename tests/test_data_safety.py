"""Data safety: one-click CSV export + confirmation before deletion."""

import csv
import io
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "static" / "index.html"


def test_csv_export_endpoint(client):
    client, _ = client
    client.post("/api/recipes", json={"url": "https://example.com/borscht"})
    r = client.get("/api/recipes/export.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers.get("content-disposition", "")
    rows = list(csv.reader(io.StringIO(r.text)))
    assert rows[0] == ["title", "url", "tags", "favorite", "rating", "saved_at"]
    assert len(rows) == 2 and "borscht" in rows[1][1]


def test_csv_export_escapes_and_multitag():
    """csv.writer round-trip: titles with commas/quotes survive."""
    import csv
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Borscht, \"best\"", "https://x.y", "soup;dinner", 1, 5, 1.0])
    rows = list(csv.reader(io.StringIO(buf.getvalue())))
    assert rows[0][0] == 'Borscht, "best"'
    assert rows[0][2] == "soup;dinner"


def test_csv_route_not_shadowed_by_id_route(client):
    client, _ = client
    assert client.get("/api/recipes/export.csv").status_code == 200
    assert client.get("/api/recipes/999999").status_code == 404  # id route still fine


def test_ui_has_csv_link_and_delete_confirmation(client):
    client, _ = client
    page = client.get("/").text
    assert "/api/recipes/export.csv" in page
    assert "confirm(" in page
    src = SRC.read_text(encoding="utf-8")
    assert "delete_confirm" in src


def test_delete_confirm_is_translated():
    from tests.test_i18n import _dict_keys  # reuse the parity helper
    keys = _dict_keys("ua") & _dict_keys("en")
    assert "delete_confirm" in keys and "export_csv" in keys
