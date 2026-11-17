"""Página Estatísticas descritivas: relatório no formato do Minitab (N, N*, EP média, quartis, IC) e normalidade."""

import numpy as np
import pandas as pd
import streamlit as st

from statlab.core import tabela
from statlab.core.dados import ErroDeDados
from statlab.core.descritiva import resumo_estatistico
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import anderson_darling
from statlab.ui import estado

st.header("Estatísticas descritivas")

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()

nome, df = ativa
numericas = tabela.colunas_numericas(df)
if not numericas:
    st.warning(f"A worksheet **{nome}** não tem colunas numéricas.")
    st.stop()

variaveis = st.multiselect("Variáveis (numéricas)", numericas, default=numericas[:1], key="desc_vars")
outras = [c for c in df.columns if c not in variaveis]
agrupar = st.selectbox("Por variável de agrupamento (opcional)", ["(nenhuma)", *outras], key="desc_grupo")
confianca = st.number_input(
    "Nível de confiança do intervalo (%)", min_value=50.0, max_value=99.9, value=95.0, step=0.5, key="desc_conf"
)

if not variaveis:
    st.info("Escolha pelo menos uma variável.")
    st.stop()


def _grupos(var: str) -> dict[str, np.ndarray]:
    if agrupar == "(nenhuma)":
        return {"Todos": df[var].to_numpy(dtype=float)}
    return {str(nivel): serie.to_numpy(dtype=float) for nivel, serie in df.groupby(agrupar, sort=False)[var]}


linhas: list[dict[str, str]] = []
linhas_ad: list[dict[str, str]] = []
for var in variaveis:
    for grupo, valores in _grupos(var).items():
        try:
            r = resumo_estatistico(valores, confianca=confianca / 100)
        except ErroDeDados as exc:
            st.warning(f"{var} / {grupo}: {exc}")
            continue
        linhas.append(
            {
                "Variável": var,
                "Grupo": grupo,
                "N": str(r.n + r.n_faltantes),
                "N*": str(r.n_faltantes),
                "Média": num(r.media),
                "EP da média": num(r.ep_media, 3),
                "DP": num(r.dp),
                "Mínimo": num(r.minimo),
                "Q1": num(r.q1),
                "Mediana": num(r.mediana),
                "Q3": num(r.q3),
                "Máximo": num(r.maximo),
                "Assimetria": num(r.assimetria, 3),
                "Curtose": num(r.curtose, 3),
                f"IC {confianca:g}% da média": f"({num(r.ic_media[0])}; {num(r.ic_media[1])})",
            }
        )
        try:
            ad = anderson_darling(valores[~np.isnan(valores)])
        except ErroDeDados:
            continue
        linhas_ad.append(
            {
                "Variável": var,
                "Grupo": grupo,
                "A²": num(ad.estatistica, 3),
                "p": p_valor(ad.p).removeprefix("= "),
                "Conclusão": "normal (não se rejeita)" if ad.normal else "não normal (rejeita-se)",
            }
        )

if linhas:
    st.subheader("Estatísticas")
    st.caption(
        "N = total de observações; N* = faltantes. Assimetria e curtose ajustadas, como no Minitab. "
        "Faltantes são excluídos dos cálculos."
    )
    st.dataframe(pd.DataFrame(linhas), hide_index=True)
if linhas_ad:
    st.subheader("Teste de normalidade (Anderson-Darling, padrão do Minitab)")
    st.caption("p > α = 0,05 significa que não se rejeita a normalidade (pode-se assumir distribuição normal).")
    st.dataframe(pd.DataFrame(linhas_ad), hide_index=True)
