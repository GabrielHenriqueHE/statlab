"""Página Relatório: as análises adicionadas nesta sessão, exportáveis em Markdown e HTML."""

import streamlit as st

from statlab.relatorio import para_html, para_markdown
from statlab.ui import estado

st.header("Relatório")
itens = estado.relatorio()
if not itens:
    st.info(
        "O relatório está vazio. Nas páginas de testes, use o botão **Adicionar ao relatório** depois de "
        "analisar os dados."
    )
    st.stop()

titulo = st.text_input("Título do relatório", value="Relatório — statlab", key="rel_titulo")
c1, c2, c3 = st.columns(3)
c1.download_button(
    "Baixar HTML (com gráficos)",
    data=para_html(itens, titulo).encode("utf-8"),
    file_name="relatorio_statlab.html",
    mime="text/html",
    key="rel_html",
)
c2.download_button(
    "Baixar Markdown",
    data=para_markdown(itens, titulo).encode("utf-8"),
    file_name="relatorio_statlab.md",
    mime="text/markdown",
    key="rel_md",
)
if c3.button("Limpar relatório", key="rel_limpar"):
    itens.clear()
    st.rerun()

for i, item in enumerate(list(itens)):
    with st.expander(f"{i + 1}. {item.titulo}", expanded=i == len(itens) - 1):
        st.markdown(f"**Teste:** {item.teste}")
        st.markdown(f"> {item.conclusao}")
        for ic, nome, det in item.verificacoes:
            st.markdown(f"{ic} **{nome}** — {det}")
        for linha in item.resultado:
            st.text(linha)
        for aviso in item.avisos:
            st.warning(aviso)
        for fig in item.figuras:
            st.plotly_chart(fig, key=f"rel_fig_{i}_{id(fig)}")
        if st.button("Remover", key=f"rel_remover_{i}"):
            itens.pop(i)
            st.rerun()
