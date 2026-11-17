"""Estado compartilhado entre páginas: as worksheets da sessão e qual está ativa (como no Minitab)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

PLANILHAS = "planilhas"
ATIVA = "planilha_ativa"
SELETOR = "seletor_worksheet"


def planilhas() -> dict[str, pd.DataFrame]:
    if PLANILHAS not in st.session_state:
        st.session_state[PLANILHAS] = {}
    return st.session_state[PLANILHAS]


def nome_unico(base: str) -> str:
    base = (base or "Worksheet").strip() or "Worksheet"
    existentes = planilhas()
    if base not in existentes:
        return base
    k = 2
    while f"{base} ({k})" in existentes:
        k += 1
    return f"{base} ({k})"


def nova_planilha(nome: str, df: pd.DataFrame) -> str:
    final = nome_unico(nome)
    planilhas()[final] = df
    st.session_state[ATIVA] = final
    return final


def salvar(nome: str, df: pd.DataFrame) -> None:
    planilhas()[nome] = df


def ativa() -> tuple[str, pd.DataFrame] | None:
    """Worksheet ativa como ``(nome, tabela)``; None se a sessão não tem nenhuma."""
    dados = planilhas()
    if not dados:
        return None
    nome = st.session_state.get(ATIVA)
    if nome not in dados:
        nome = next(iter(dados))
        st.session_state[ATIVA] = nome
    return nome, dados[nome]


def seletor_lateral() -> None:
    """Seletor da worksheet ativa na barra lateral (visível em todas as páginas)."""
    dados = planilhas()
    if not dados:
        st.sidebar.caption("Nenhuma worksheet ainda. Importe ou cole dados na página **Dados**.")
        return
    nomes = list(dados)
    atual = ativa()[0]  # type: ignore[index]
    escolha = st.sidebar.selectbox("Worksheet ativa", nomes, index=nomes.index(atual), key=SELETOR)
    st.session_state[ATIVA] = escolha


ALPHA = "alpha_global"
ALPHAS = (0.05, 0.01)


def alpha() -> float:
    """Nível de significância escolhido na barra lateral (padrão 0,05)."""
    valor = st.session_state.get(ALPHA, ALPHAS[0])
    return float(valor) if valor in ALPHAS else ALPHAS[0]


def seletor_alpha() -> None:
    st.sidebar.radio(
        "Nível de significância (α)",
        ALPHAS,
        format_func=lambda a: f"{a:.2f}".replace(".", ",") + (" (95% de confiança)" if a == 0.05 else " (99%)"),
        key=ALPHA,
    )
