"""INSTALL.md + launchers: start.bat, install.bat, systemd user unit."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_install_md_covers_windows_linux_updates():
    doc = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
    assert "start.bat" in doc
    assert "shell:startup" in doc                     # Windows autostart via Startup folder
    assert "systemd" in doc and "recipe-distiller.service" in doc
    assert "Оновлення" in doc                          # update section
    assert "Install" in doc or "встанов" in doc.lower()


def test_start_bat_launches_uvicorn():
    bat = (ROOT / "start.bat").read_text(encoding="utf-8", errors="replace")
    assert "app.main:app" in bat
    assert "uvicorn" in bat
    assert "http://localhost:8000" in bat


def test_install_bat_installs_requirements():
    bat = (ROOT / "install.bat").read_text(encoding="utf-8", errors="replace")
    assert "requirements.txt" in bat


def test_systemd_user_unit():
    unit = (ROOT / "deploy" / "recipe-distiller.service").read_text(encoding="utf-8")
    assert "[Service]" in unit and "uvicorn app.main:app" in unit
    assert "WantedBy=default.target" in unit           # user unit, not system


def test_extension_folder_referenced_from_install():
    doc = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
    assert "extension/" in doc and "Load unpacked" in doc
