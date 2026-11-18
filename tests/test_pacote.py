"""Pacote: versão, subpacotes, pureza do núcleo e o entrypoint que abre o app."""

from pathlib import Path

import pytest

import statlab
from statlab import core, graficos, relatorio, ui

RAIZ = Path(statlab.__file__).parent
PUROS = ["core", "relatorio", "graficos"]


def test_versao_definida() -> None:
    assert statlab.__version__ == "0.1.0"


def test_subpacotes_importam() -> None:
    assert core is not None
    assert ui is not None
    assert relatorio is not None
    assert graficos is not None


@pytest.mark.parametrize("pacote", PUROS)
def test_nucleo_relatorio_e_graficos_nao_importam_a_ui(pacote: str) -> None:
    """Pureza: só a camada ``ui`` conhece o motor gráfico (hoje PySide6)."""
    for arquivo in (RAIZ / pacote).rglob("*.py"):
        fonte = arquivo.read_text()
        for proibido in ("PySide6", "statlab.ui", "streamlit"):
            assert proibido not in fonte, f"{arquivo.relative_to(RAIZ)} importa {proibido}"


def test_main_abre_a_janela_qt(monkeypatch: pytest.MonkeyPatch) -> None:
    from statlab.ui import app as app_qt

    chamadas: list[bool] = []
    monkeypatch.setattr(app_qt, "main", lambda: chamadas.append(True))
    statlab.main()
    assert chamadas == [True]


def test_app_qt_tem_janela_e_entrada() -> None:
    from statlab.ui import app as app_qt

    assert callable(app_qt.main)
    assert hasattr(app_qt, "JanelaPrincipal")
