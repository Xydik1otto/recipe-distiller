"""Ingredient checklist: checkboxes in the UI card, state kept in localStorage."""

from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "static"
INDEX = (STATIC / "index.html").read_text(encoding="utf-8")


def test_card_renders_checkboxes_for_ingredients():
    assert 'type="checkbox" data-ing=' in INDEX


def test_checklist_state_uses_localstorage():
    assert "localStorage.getItem" in INDEX and "localStorage.setItem" in INDEX
    assert "rd-check:" in INDEX          # namespaced key per recipe url


def test_checked_items_strikethrough_and_reset_button():
    assert "input:checked ~ .txt" in INDEX
    assert 'class="uncheck"' in INDEX


def test_conversion_span_inside_checklist_label():
    assert 'class="conv" data-conv=' in INDEX
