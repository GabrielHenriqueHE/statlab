"""Página Qui-quadrado: independência (tabela de contingência) e aderência (qualidade do ajuste)."""

import pandas as pd
import streamlit as st

from statlab.core import qui_quadrado
from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num
from statlab.ui import componentes, estado

st.header("Qui-quadrado")
alpha = estado.alpha()
ativa = estado.ativa()
aba_ind, aba_ad = st.tabs(["Independência (tabela de contingência)", "Aderência (qualidade do ajuste)"])

DA_WORKSHEET = "Duas colunas da worksheet"
DIGITADA = "Digitar a tabela"


def _tabela_formatada(matriz, linhas, colunas, casas: int) -> pd.DataFrame:
    return pd.DataFrame([[num(v, casas) for v in linha] for linha in matriz], index=linhas, columns=colunas)


with aba_ind:
    st.caption("H₀: as variáveis são independentes. Cada célula é a contagem de uma combinação de categorias.")
    modo = st.radio("Origem", [DIGITADA, DA_WORKSHEET], key="qi_modo", horizontal=True)
    tabela = None
    if modo == DA_WORKSHEET:
        if ativa is None:
            st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
        else:
            _, df = ativa
            colunas = list(df.columns)
            c1, c2 = st.columns(2)
            col_l = c1.selectbox("Linhas", colunas, key="qi_lin")
            col_c = c2.selectbox("Colunas", colunas, index=min(1, len(colunas) - 1), key="qi_col")
            try:
                tabela = qui_quadrado.tabela_contingencia(df, col_l, col_c)
            except ErroDeDados as exc:
                st.error(str(exc))
    else:
        inicial = pd.DataFrame({"Coluna 1": [10, 20], "Coluna 2": [30, 40]}, index=["Linha 1", "Linha 2"])
        editada = st.data_editor(inicial, num_rows="dynamic", key="qi_editor")
        tabela = editada.apply(pd.to_numeric, errors="coerce")
    if tabela is not None:
        try:
            res = qui_quadrado.independencia(tabela, alpha=alpha)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            c1, c2 = st.columns(2)
            c1.markdown("**Observados**")
            c1.dataframe(_tabela_formatada(res.observados, res.linhas, res.colunas, 0))
            c2.markdown("**Esperados (se independentes)**")
            c2.dataframe(_tabela_formatada(res.esperados, res.linhas, res.colunas, 2))
            componentes.mostrar(res)
            componentes.botao_relatorio("qi", componentes.item(res, "Qui-quadrado de independência"))

with aba_ad:
    st.caption("H₀: as contagens seguem as proporções esperadas (iguais, se não informadas).")
    modo_a = st.radio("Origem", [DIGITADA, DA_WORKSHEET], key="qa_modo", horizontal=True)
    obs = cats = props = None
    if modo_a == DA_WORKSHEET:
        if ativa is None:
            st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
        else:
            _, df = ativa
            col = st.selectbox("Coluna categórica", list(df.columns), key="qa_col")
            contagem = df[col].dropna().astype(str).value_counts().sort_index()
            cats, obs = list(contagem.index), contagem.to_numpy()
    else:
        inicial = pd.DataFrame(
            {"Categoria": ["A", "B", "C"], "Observado": [18, 22, 20], "Proporção esperada": [1.0, 1.0, 1.0]}
        )
        editada = st.data_editor(inicial, num_rows="dynamic", key="qa_editor")
        editada = editada.dropna(subset=["Categoria"])
        cats = editada["Categoria"].astype(str).tolist()
        obs = pd.to_numeric(editada["Observado"], errors="coerce").to_numpy()
        props = pd.to_numeric(editada["Proporção esperada"], errors="coerce").to_numpy()
        st.caption("Proporções esperadas podem ser pesos (ex.: 1, 1, 2); são normalizadas para somar 1.")
    if obs is not None:
        try:
            res_a = qui_quadrado.aderencia(obs, categorias=cats, proporcoes=props, alpha=alpha)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            st.dataframe(
                pd.DataFrame(
                    {
                        "Categoria": res_a.colunas,
                        "Observado": [num(v, 0) for v in res_a.observados[0]],
                        "Esperado": [num(v, 2) for v in res_a.esperados[0]],
                    }
                ),
                hide_index=True,
            )
            componentes.mostrar(res_a, "as categorias")
            componentes.botao_relatorio("qa", componentes.item(res_a, "Qui-quadrado de aderência", "as categorias"))
