"""A janela de sessão: a saída acumulada dos comandos, como no Minitab."""

from __future__ import annotations

import streamlit as st

from statlab.relatorio import ItemRelatorio, para_html, para_markdown
from statlab.ui import estado


def _bloco(item: ItemRelatorio, i: int) -> None:
    cabecalho = f"**{item.titulo}**"
    if item.teste and item.teste != item.titulo:
        cabecalho += f"  ·  {item.teste}"
    st.markdown(cabecalho)
    st.caption(item.criado_em.strftime("%H:%M:%S"))

    for nome, tabela in item.tabelas:
        st.markdown(f"*{nome}*")
        st.dataframe(tabela, hide_index=True, width="stretch")
    for linha in item.resultado:
        st.markdown(f"- {linha}")
    if item.verificacoes:
        st.markdown("*Diagnósticos*")
        for icone, nome, detalhe in item.verificacoes:
            st.markdown(f"{icone} **{nome}** — {detalhe}")
    for aviso in item.avisos:
        st.warning(aviso, icon="ℹ️")
    for j, fig in enumerate(item.figuras):
        st.plotly_chart(fig, width="stretch", key=f"sessao_fig_{i}_{j}")
    if item.passos:
        with st.expander("Cálculo"):
            for passo in item.passos:
                st.text(passo)
    st.button("Remover", key=f"sessao_rm_{i}", on_click=estado.remover_da_sessao, args=(i,))
    st.divider()


def painel() -> None:
    """Desenha a janela de sessão, com exportação e limpeza."""
    itens = estado.sessao()
    c1, c2 = st.columns([3, 1])
    c1.subheader("Sessão")
    if itens:
        c2.button("Limpar", key="sessao_limpar", on_click=estado.limpar_sessao, width="stretch")
    if not itens:
        st.caption("A saída dos comandos aparece aqui. Comece pelo menu **Dados**.")
        return

    with st.container(height=520, border=False):
        for i, item in enumerate(itens):
            _bloco(item, i)

    d1, d2 = st.columns(2)
    d1.download_button(
        "Exportar HTML",
        data=para_html(itens).encode("utf-8"),
        file_name="sessao_statlab.html",
        mime="text/html",
        width="stretch",
        key="sessao_html",
    )
    d2.download_button(
        "Exportar Markdown",
        data=para_markdown(itens).encode("utf-8"),
        file_name="sessao_statlab.md",
        mime="text/markdown",
        width="stretch",
        key="sessao_md",
    )
