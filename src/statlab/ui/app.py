"""Entrada do app statlab (Streamlit). Rode com ``uv run statlab``.

Layout no modelo do Minitab: barra de menus em cima, worksheet à esquerda e janela de sessão à
direita. Cada comando do menu abre um diálogo com as suas opções e manda a saída para a sessão.
"""

import pandas as pd
import streamlit as st

from statlab.ui import estado, menu, sessao

st.set_page_config(page_title="statlab", layout="wide")

st.markdown("### statlab")
menu.barra()

estado.seletor_lateral()
st.sidebar.caption(
    "O statlab executa o comando que você escolher, com as opções que você marcar. "
    "Ele não troca o teste, não exclui dados e não escreve a conclusão."
)

esquerda, direita = st.columns([1.1, 1])

with esquerda:
    ativa = estado.ativa()
    if ativa is None:
        st.subheader("Worksheet")
        st.info("Nenhuma worksheet aberta. Use **Dados › Abrir arquivo** ou **Dados › Colar dados**.")
    else:
        nome, df = ativa
        st.subheader(f"Worksheet: {nome}")
        editado = st.data_editor(df, num_rows="dynamic", width="stretch", height=520, key=f"ws_{nome}")
        if not editado.equals(df):
            estado.salvar(nome, pd.DataFrame(editado))
        st.caption(f"{len(df)} linha(s) × {df.shape[1]} coluna(s). Edite as células diretamente.")

with direita:
    sessao.painel()
