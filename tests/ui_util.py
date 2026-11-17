"""Helpers dos testes de interface (AppTest do Streamlit)."""

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from statlab.ui import estado

UI = Path(__file__).resolve().parents[1] / "src" / "statlab" / "ui"
APP = UI / "app.py"
TIMEOUT = 60


def app(planilhas: dict[str, pd.DataFrame] | None = None) -> AppTest:
    """Roda o app com as worksheets dadas (a primeira fica ativa)."""
    at = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    at.session_state[estado.PLANILHAS] = planilhas or {}
    if planilhas:
        at.session_state[estado.ATIVA] = next(iter(planilhas))
    return at.run()


def sem_erros(at: AppTest, esperando_mensagem: bool = False) -> None:
    """Nenhuma exceção não tratada. Sem ``esperando_mensagem``, também nenhum ``st.error``."""
    assert [str(e.value) for e in at.exception] == []
    if not esperando_mensagem:
        assert [e.value for e in at.error] == []


def abrir(at: AppTest, menu: str, grupo: str, nome: str) -> AppTest:
    """Clica num item de menu, abrindo o diálogo do comando."""
    return at.button(key=f"menu_{menu}_{grupo}_{nome}").click().run()


def executar(at: AppTest, rotulo: str = "Executar") -> AppTest:
    """Clica no botão que roda o comando do diálogo aberto."""
    for botao in at.button:
        if botao.label == rotulo:
            return botao.click().run()
    raise AssertionError(f"botão {rotulo!r} não encontrado; há: {[b.label for b in at.button]}")


def saida(at: AppTest) -> list:
    """Os blocos acumulados na janela de sessão."""
    return at.session_state[estado.SESSAO]


def linhas_da_saida(at: AppTest, indice: int = -1) -> str:
    item = saida(at)[indice]
    return "\n".join([*item.resultado, *item.avisos, *item.passos])


def worksheet(**colunas: list[float]) -> pd.DataFrame:
    """Colunas de tamanhos diferentes viram uma worksheet com faltantes no fim (como no Minitab)."""
    return pd.DataFrame({k: pd.Series(v, dtype=float) for k, v in colunas.items()})
