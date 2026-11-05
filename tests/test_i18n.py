"""i18n: UA/EN dictionaries, browser-language auto-detect, persisted choice."""

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "static"


def _dict_keys(name: str) -> set:
    src = (STATIC / "i18n.js").read_text(encoding="utf-8")
    block = re.search(rf"{name}: \{{(.*?)\n  \}}", src, re.S).group(1)
    return set(re.findall(r"^    (\w+):", block, re.M))


def test_both_dictionaries_present():
    ua, en = _dict_keys("ua"), _dict_keys("en")
    assert {"ua", "en"} <= set(re.findall(r"^  (\w+): \{",
        (STATIC / "i18n.js").read_text(encoding="utf-8"), re.M))
    assert ua and en


def test_key_parity_ua_en():
    assert _dict_keys("ua") == _dict_keys("en"), "dictionaries must cover the same keys"


def test_no_russian_locale():
    src = (STATIC / "i18n.js").read_text(encoding="utf-8")
    for marker in ("русск", "Вставьте ссылку", "Мой сборник", "по-русски"):
        assert marker not in src  # political decision: UA/EN only, never Russian


def test_i18n_js_served(client):
    client, _ = client
    r = client.get("/i18n.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    assert "localStorage.setItem('rd-lang'" in r.text     # choice persists
    assert "navigator.language" in r.text                 # browser-language auto-detect


def test_index_has_lang_toggle_and_data_i18n(client):
    client, _ = client
    page = client.get("/").text
    assert 'src="/i18n.js"' in page
    assert page.count('class="langbtn') == 2              # UA + EN buttons
    assert 'data-i18n="book"' in page                     # static elements tagged
    assert "applyI18n()" in page


def test_i18n_js_in_offline_shell():
    sw = (STATIC / "sw.js").read_text(encoding="utf-8")
    assert "'/i18n.js'" in sw
