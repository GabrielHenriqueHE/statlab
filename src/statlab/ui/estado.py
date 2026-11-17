"""Estado da sessão: as worksheets abertas (como no Minitab) e a janela de sessão."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from statlab.relatorio import ItemRelatorio

PLANILHAS = "planilhas"
ATIVA = "planilha_ativa"
SELETOR = "seletor_worksheet"
SESSAO = "sessao_itens"
COMANDO = "comando_aberto"


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
    """Seletor da worksheet ativa na barra lateral."""
    dados = planilhas()
    if not dados:
        st.sidebar.caption("Nenhuma worksheet ainda. Use **Dados › Importar** ou **Dados › Colar**.")
        return
    nomes = list(dados)
    atual = ativa()[0]  # type: ignore[index]
    escolha = st.sidebar.selectbox("Worksheet ativa", nomes, index=nomes.index(atual), key=SELETOR)
    st.session_state[ATIVA] = escolha


# --------------------------------------------------------------------------- janela de sessão


def sessao() -> list[ItemRelatorio]:
    """Saídas acumuladas dos comandos, na ordem em que foram executados."""
    if SESSAO not in st.session_state:
        st.session_state[SESSAO] = []
    return st.session_state[SESSAO]


def registrar(*itens: ItemRelatorio) -> None:
    """Acrescenta blocos à janela de sessão."""
    sessao().extend(itens)


def limpar_sessao() -> None:
    st.session_state[SESSAO] = []


def remover_da_sessao(indice: int) -> None:
    itens = sessao()
    if 0 <= indice < len(itens):
        del itens[indice]


# --------------------------------------------------------------------------- diálogo aberto


def abrir_comando(chave: str) -> None:
    """Marca qual comando está com o diálogo aberto.

    O estado é explícito porque o diálogo precisa ser redesenhado a cada rerun: sem isso, mexer em
    qualquer opção dentro dele o fecharia.
    """
    st.session_state[COMANDO] = chave


def fechar_comando() -> None:
    st.session_state[COMANDO] = None


def comando_aberto() -> str | None:
    return st.session_state.get(COMANDO)
