"""Tests des fichiers Docker : pytest ne lance pas Docker, mais il vérifie ce qui casse un conteneur sans bruit."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def instructions(name: str) -> list[str]:
    """Les lignes utiles d'un fichier, sans commentaires ni lignes vides."""
    return [line.split("#")[0].strip() for line in read(name).splitlines() if line.split("#")[0].strip()]


def test_image_requirements_are_pinned_like_the_model():
    reqs = instructions("requirements-docker.txt")
    assert "scikit-learn==1.8.0" in reqs          # la version qui a écrit le modèle (TP4)
    assert all("==" in r for r in reqs)
    assert not any(r.startswith(("mlflow", "dvc", "pytest")) for r in reqs)


def test_dockerfile_installs_libraries_before_copying_the_code():
    lines = instructions("Dockerfile")
    assert lines[0].startswith("FROM python:3.11")
    pip = next(i for i, line in enumerate(lines) if "pip install" in line)
    code = next(i for i, line in enumerate(lines) if line.startswith("COPY maintai"))
    assert pip < code                             # le cache garde l'étape lente


def test_api_listens_on_all_interfaces():
    cmd = next(line for line in instructions("Dockerfile") if line.startswith("CMD"))
    assert "0.0.0.0" in cmd and "8000" in cmd     # 127.0.0.1 serait injoignable depuis le PC


def test_secrets_data_and_models_stay_out_of_the_image():
    ignored = instructions(".dockerignore")
    for item in (".venv/", "data/", "models/", ".env", "mlflow.db"):
        assert item in ignored, f"{item} entrerait dans l'image"


def test_compose_mounts_the_model_and_names_the_api():
    compose = read("compose.yaml")
    assert "./models:/app/models" in compose      # le modèle vient du PC, pas de l'image
    assert "env_file: .env" in compose            # la clé API, sans l'écrire dans le fichier
    assert "http://api:8000" in compose           # l'interface appelle le service par son nom


def test_ui_reads_the_api_url_from_the_environment(settings_env, monkeypatch):
    monkeypatch.setenv("MAINTAI_API_URL", "http://api:8000")
    at = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=30).run()
    assert at.sidebar.text_input[0].value == "http://api:8000"
