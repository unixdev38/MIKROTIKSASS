"""Garde-fou : toute dépendance utilisée est déclarée.

Ce test existe à cause d'un oubli réel : ``djangorestframework-simplejwt`` était importé
par le code (JWT) mais absent de ``pyproject.toml``, ce qui cassait une installation
neuve. Il compare trois sources : les imports du code, ``pyproject.toml`` et les
fichiers ``requirements``.
"""
from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

#: Correspondance module importé → distribution PyPI.
MODULE_TO_DISTRIBUTION = {
    "django": "django",
    "rest_framework": "djangorestframework",
    "rest_framework_simplejwt": "djangorestframework-simplejwt",
    "celery": "celery",
    "cryptography": "cryptography",
    "pytest": "pytest",
    "redis": "redis",
}

#: Paquets locaux (jamais des distributions).
LOCAL_PACKAGES = {"apps", "core", "config", "tests", "design"}


def normalize(name: str) -> str:
    """Normalise un nom de distribution (insensible à la casse et aux séparateurs).

    Args:
        name: Nom brut (``Django``, ``djangorestframework_simplejwt``).

    Returns:
        Le nom normalisé, par exemple ``djangorestframework-simplejwt``.
    """
    return name.strip().lower().replace("_", "-").replace(".", "-")


def declared_in_pyproject() -> dict[str, set[str]]:
    """Lit les dépendances déclarées dans ``backend/pyproject.toml``.

    Returns:
        Un dictionnaire ``{"runtime": {...}, "dev": {...}}`` de noms normalisés.

    Raises:
        FileNotFoundError: Si ``pyproject.toml`` est absent.
    """
    data = tomllib.loads((BACKEND_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    runtime = {normalize(_distribution_part(entry)) for entry in project.get("dependencies", [])}
    dev = {
        normalize(_distribution_part(entry))
        for entry in project.get("optional-dependencies", {}).get("dev", [])
    }
    return {"runtime": runtime, "dev": dev}


def _distribution_part(requirement: str) -> str:
    """Extrait le nom d'une exigence PEP 508 (``"django>=5.2,<5.3"`` → ``"django"``).

    Args:
        requirement: Exigence complète.

    Returns:
        Le nom de la distribution seule.
    """
    for separator in ("[", ">", "<", "=", "!", "~", ";"):
        requirement = requirement.split(separator)[0]
    return requirement.strip()


def parse_requirements(path: Path) -> set[str]:
    """Liste les distributions d'un fichier ``requirements`` (hors options).

    Args:
        path: Fichier à lire.

    Returns:
        Les noms normalisés (les lignes ``-r`` et commentaires sont ignorés).
    """
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#") or entry.startswith("-"):
            continue
        names.add(normalize(_distribution_part(entry)))
    return names


def imported_third_party_modules() -> set[str]:
    """Recense les modules tiers importés par le code applicatif.

    Returns:
        Les noms de modules de premier niveau (hors bibliothèque standard et paquets locaux).
    """
    import sys

    stdlib = set(sys.stdlib_module_names)
    modules: set[str] = set()
    for path in list((BACKEND_DIR / "apps").rglob("*.py")) + list(
        (BACKEND_DIR / "core").rglob("*.py")
    ) + list((BACKEND_DIR / "config").rglob("*.py")):
        if "migrations" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                targets = [node.module]
            for target in targets:
                top = target.split(".")[0]
                if top not in stdlib and top not in LOCAL_PACKAGES:
                    modules.add(top)
    return modules


def test_every_import_is_mapped():
    """Tout module tiers importé doit figurer dans la table de correspondance."""
    unknown = imported_third_party_modules() - set(MODULE_TO_DISTRIBUTION)

    assert not unknown, f"Modules non répertoriés dans MODULE_TO_DISTRIBUTION : {sorted(unknown)}"


def test_every_import_is_declared():
    """Tout module tiers importé est déclaré dans pyproject.toml (runtime ou dev)."""
    declared = declared_in_pyproject()
    known = declared["runtime"] | declared["dev"]

    missing = {
        MODULE_TO_DISTRIBUTION[module]
        for module in imported_third_party_modules()
        if normalize(MODULE_TO_DISTRIBUTION[module]) not in known
    }

    assert not missing, f"Dépendances importées mais non déclarées : {sorted(missing)}"


def test_requirements_txt_covers_runtime_dependencies():
    """``requirements.txt`` contient exactement les dépendances d'exécution déclarées."""
    declared = declared_in_pyproject()["runtime"]
    pinned = parse_requirements(BACKEND_DIR / "requirements.txt")

    assert pinned == declared, (
        f"Écart entre requirements.txt et pyproject.toml : "
        f"manquants={sorted(declared - pinned)}, superflus={sorted(pinned - declared)}"
    )


def test_dev_requirements_include_runtime():
    """``requirements-dev.txt`` part de ``requirements.txt`` et ajoute les outils."""
    content = (BACKEND_DIR / "requirements-dev.txt").read_text(encoding="utf-8")
    pinned = parse_requirements(BACKEND_DIR / "requirements-dev.txt")

    assert "-r requirements.txt" in content
    assert {"pytest", "pytest-django", "ruff"} <= pinned


def test_requirements_are_pinned():
    """Chaque ligne utile est épinglée (``==``), pour des installations reproductibles."""
    for filename in ("requirements.txt", "requirements-dev.txt"):
        for line in (BACKEND_DIR / filename).read_text(encoding="utf-8").splitlines():
            entry = line.strip()
            if not entry or entry.startswith("#") or entry.startswith("-"):
                continue
            assert "==" in entry, f"Version non figée dans {filename} : {entry}"


def test_project_documents_requirements_files():
    """Les deux installateurs citent bien le fichier de dépendances."""
    makefile = (ROOT_DIR / "Makefile").read_text(encoding="utf-8")
    assert "requirements-dev.txt" in makefile

    dev_ps1 = (ROOT_DIR / "dev.ps1").read_text(encoding="utf-8")
    assert "requirements-dev.txt" in dev_ps1


@pytest.mark.parametrize("filename", ["requirements.txt", "requirements-dev.txt"])
def test_requirements_file_is_not_empty(filename: str):
    """Les fichiers de dépendances existent et contiennent au moins une ligne utile.

    Args:
        filename: Nom du fichier testé.
    """
    path = BACKEND_DIR / filename

    assert path.is_file()
    assert parse_requirements(path), f"{filename} ne déclare aucune dépendance"
