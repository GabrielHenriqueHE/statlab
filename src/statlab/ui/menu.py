"""Barra de menus do statlab (o Streamlit não tem menu nativo: cada menu é um popover)."""

from __future__ import annotations

import streamlit as st

from statlab.ui import estado
from statlab.ui.comandos import COMANDOS, MENUS


def chave(comando) -> str:
    return f"{comando.menu}_{comando.grupo}_{comando.nome}"


def barra() -> None:
    """Desenha a barra de menus e, se houver, o diálogo do comando aberto."""
    colunas = st.columns(len(MENUS))
    for coluna, nome_menu in zip(colunas, MENUS, strict=True):
        comandos = [c for c in COMANDOS if c.menu == nome_menu]
        with coluna.popover(nome_menu, width="stretch"):
            grupo_atual = None
            for c in comandos:
                if c.grupo != grupo_atual:
                    grupo_atual = c.grupo
                    if grupo_atual:
                        st.caption(grupo_atual)
                if st.button(c.nome, key=f"menu_{chave(c)}", width="stretch"):
                    estado.abrir_comando(chave(c))
                    st.rerun()

    aberto = estado.comando_aberto()
    if aberto:
        for c in COMANDOS:
            if chave(c) == aberto:
                c.abrir()
                break
