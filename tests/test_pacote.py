"""Teste de fumaça da F0: o pacote importa, expõe versão e o entrypoint existe."""

import statlab
from statlab import core, relatorio, ui


def test_versao_definida() -> None:
    assert statlab.__version__ == "0.1.0"


def test_subpacotes_importam() -> None:
    assert core is not None
    assert ui is not None
    assert relatorio is not None


def test_main_imprime_status(capsys) -> None:
    statlab.main()
    saida = capsys.readouterr().out
    assert "statlab 0.1.0" in saida
