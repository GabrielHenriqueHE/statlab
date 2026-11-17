"""Helpers dos testes de interface (AppTest do Streamlit)."""

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from statlab.ui import estado

UI = Path(__file__).resolve().parents[1] / "src" / "statlab" / "ui"
PAGINAS = UI / "paginas"
TIMEOUT = 60


def app(pagina: str, planilhas: dict[str, pd.DataFrame] | None = None) -> AppTest:
    """Roda uma página com as worksheets dadas (a primeira fica ativa)."""
    at = AppTest.from_file(str(PAGINAS / pagina), default_timeout=TIMEOUT)
    at.session_state[estado.PLANILHAS] = planilhas or {}
    if planilhas:
        at.session_state[estado.ATIVA] = next(iter(planilhas))
    return at.run()


def sem_erros(at: AppTest, esperando_mensagem: bool = False) -> None:
    """Nenhuma exceção não tratada. Sem ``esperando_mensagem``, também nenhum ``st.error``."""
    assert [e.value for e in at.exception] == []
    if not esperando_mensagem:
        assert [e.value for e in at.error] == []


def metrica(at: AppTest, rotulo: str) -> str:
    for m in at.metric:
        if m.label == rotulo:
            return m.value
    raise AssertionError(f"métrica {rotulo!r} não encontrada; há: {[m.label for m in at.metric]}")


def worksheet(**colunas: list[float]) -> pd.DataFrame:
    """Colunas de tamanhos diferentes viram uma worksheet com faltantes no fim (como no Minitab)."""
    return pd.DataFrame({k: pd.Series(v, dtype=float) for k, v in colunas.items()})
