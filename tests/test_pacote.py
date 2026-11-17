"""Pacote: versão, subpacotes e o entrypoint que abre o app."""

import subprocess

import pytest

import statlab
from statlab import core, graficos, relatorio, ui


def test_versao_definida() -> None:
    assert statlab.__version__ == "0.1.0"


def test_subpacotes_importam() -> None:
    assert core is not None
    assert ui is not None
    assert relatorio is not None
    assert graficos is not None


def test_app_existe_no_pacote() -> None:
    assert statlab.APP.is_file()


def test_main_abre_o_app_com_streamlit(monkeypatch: pytest.MonkeyPatch) -> None:
    chamadas: list[list[str]] = []

    def falso_call(args: list[str]) -> int:
        chamadas.append(args)
        return 0

    monkeypatch.setattr(subprocess, "call", falso_call)
    with pytest.raises(SystemExit) as saida:
        statlab.main()
    assert saida.value.code == 0
    assert chamadas[0][1:4] == ["-m", "streamlit", "run"]
    assert str(statlab.APP) in chamadas[0]
