"""Bookmarklet feature: /bookmarklet drag-button page + CORS for third-party use."""

BOOKMARKLET_JS = ("javascript:(async()=>{const b='http://127.0.0.1:8000';try{const r=await fetch"
                  "(b+'/api/recipes',{method:'POST',headers:{'Content-Type':'application/json'},"
                  "body:JSON.stringify({url:location.href})});const d=await r.json();if(d.id)"
                  "window.open(b+'/print/'+d.id);else alert('No recipe found: '+(d.detail||''));}"
                  "catch(e){alert('Recipe Distiller not running on '+b)}})()")


def test_bookmarklet_page_served(client):
    client, _ = client
    r = client.get("/bookmarklet")
    assert r.status_code == 200
    assert "Just the recipe" in r.text
    assert "javascript:" in r.text


def test_bookmarklet_js_matches_page_and_readme():
    from pathlib import Path
    page = (Path(__file__).parent.parent / "static" / "bookmarklet.html").read_text(encoding="utf-8")
    readme = (Path(__file__).parent.parent / "README.md").read_text(encoding="utf-8")
    assert BOOKMARKLET_JS in page, "drag-button href must carry the exact snippet"
    assert BOOKMARKLET_JS in readme, "README snippet must match the shipped bookmarklet"


def test_cors_allows_third_party_origin(client):
    client, _ = client
    r = client.options("/api/extract", headers={
        "Origin": "https://some-recipe-site.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"
