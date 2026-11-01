"""Chargement du fichier ``.env`` : priorité au shell, fichier facultatif."""
from __future__ import annotations

import os

from config.settings import load_env_file


def test_env_file_fills_missing_variables(tmp_path, monkeypatch):
    """Les variables absentes du shell sont ajoutées depuis le fichier."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# commentaire\nSECRET_KEY_VERSION=3\nKORA_DEMO_TAG = \"deux mots\"\n\nligne_invalide\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SECRET_KEY_VERSION", raising=False)
    monkeypatch.delenv("KORA_DEMO_TAG", raising=False)

    loaded = load_env_file(env_file)

    assert loaded == 2
    assert os.environ["SECRET_KEY_VERSION"] == "3"
    assert os.environ["KORA_DEMO_TAG"] == "deux mots"


def test_env_file_never_overrides_shell(tmp_path, monkeypatch):
    """Une variable déjà définie garde sa valeur (CI, Docker, terminal)."""
    env_file = tmp_path / ".env"
    env_file.write_text("DJANGO_DEBUG=1\n", encoding="utf-8")
    monkeypatch.setenv("DJANGO_DEBUG", "0")

    loaded = load_env_file(env_file)

    assert loaded == 0
    assert os.environ["DJANGO_DEBUG"] == "0"


def test_missing_env_file_is_silent(tmp_path):
    """Un fichier absent n'est pas une erreur : le projet démarre sans configuration."""
    assert load_env_file(tmp_path / "absent.env") == 0


def test_env_file_ignores_comments_and_blank_lines(tmp_path, monkeypatch):
    """Commentaires, lignes vides et lignes sans ``=`` sont ignorés."""
    env_file = tmp_path / ".env"
    env_file.write_text("# rien\n\nKORA_ONLY_KEY=ok\nsans_egal\n", encoding="utf-8")
    monkeypatch.delenv("KORA_ONLY_KEY", raising=False)

    assert load_env_file(env_file) == 1
    assert os.environ["KORA_ONLY_KEY"] == "ok"
