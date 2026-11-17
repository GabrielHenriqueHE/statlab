"""Página Normalidade: Shapiro-Wilk (padrão da disciplina) e Anderson-Darling (padrão do Minitab)."""

import numpy as np
import pandas as pd
import streamlit as st

from statlab import graficos
from statlab.core.dados import ErroDeDados
from statlab.core.descritiva import detectar_outliers, texto_outliers
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import anderson_darling, shapiro_wilk
from statlab.ui import componentes, estado

st.header("Teste de normalidade")
st.caption(
    "H₀: os dados vêm de uma população normal. p > α → pode-se assumir normalidade. Com n ≥ 30, o teste t e a "
    "ANOVA dispensam a normalidade (TCL); a correlação de Pearson, não."
)

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()
nome, df = ativa
numericas = componentes.exigir_numericas(df, nome)
alpha = estado.alpha()
variaveis = st.multiselect("Variáveis", numericas, default=numericas[:1], key="norm_vars")
if not variaveis:
    st.info("Escolha pelo menos uma variável.")
    st.stop()

linhas, outliers_txt = [], []
for var in variaveis:
    v = df[var].to_numpy(dtype=float)
    v = v[~np.isnan(v)]
    try:
        sw = shapiro_wilk(v, alpha=alpha, nome=var)
        ad = anderson_darling(v, alpha=alpha, nome=var)
    except ErroDeDados as exc:
        st.warning(f"{var}: {exc}")
        continue
    if sw.normal:
        conclusao = "✅ pode-se assumir normalidade"
    elif sw.pelo_tcl:
        conclusao = "⚠️ não normal, mas n ≥ 30 (TCL vale para t e ANOVA)"
    else:
        conclusao = "❌ não normal e n < 30"
    linhas.append(
        {
            "Variável": var,
            "n": str(len(v)),
            "Shapiro-Wilk W": num(sw.estatistica, 3),
            "p (Shapiro-Wilk)": p_valor(sw.p).removeprefix("= "),
            "Anderson-Darling A²": num(ad.estatistica, 3),
            "p (Anderson-Darling)": p_valor(ad.p).removeprefix("= "),
            "Conclusão (Shapiro-Wilk)": conclusao,
        }
    )
    if sw.normal != ad.normal:
        st.warning(
            f"{var}: Shapiro-Wilk e Anderson-Darling discordam (perto de α). Informe sempre qual teste usou; "
            "a disciplina usa o Shapiro-Wilk."
        )
    outliers_txt.append(texto_outliers(var, v, detectar_outliers(v)))

if linhas:
    st.dataframe(pd.DataFrame(linhas), hide_index=True)
    with st.expander("Outliers (diagrama de caixa)"):
        for t in outliers_txt:
            st.text(t)
    alvo = st.selectbox("Gráfico de probabilidade normal de", variaveis, key="norm_graf")
    try:
        st.plotly_chart(graficos.probabilidade_normal(df[alvo].to_numpy(dtype=float)))
    except ErroDeDados as exc:
        st.error(str(exc))
