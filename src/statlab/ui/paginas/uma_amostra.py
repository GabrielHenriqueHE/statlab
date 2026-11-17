"""Página Uma amostra: média (t ou Wilcoxon), média com σ conhecido (Z) e uma proporção."""

import streamlit as st

from statlab.core.dados import ErroDeDados
from statlab.core.uma_amostra import analisar_uma_amostra, analisar_uma_proporcao, analisar_z
from statlab.ui import componentes, estado

st.header("Uma amostra")
st.caption("Compara a média (ou a proporção) de uma amostra com um valor de referência. Fora da apostila revisada.")

alpha = estado.alpha()
ativa = estado.ativa()
aba_t, aba_z, aba_p = st.tabs(["Média (t ou Wilcoxon)", "Média com σ conhecido (Z)", "Proporção"])

with aba_t:
    if ativa is None:
        st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    else:
        nome, df = ativa
        numericas = componentes.exigir_numericas(df, nome)
        var = st.selectbox("Variável", numericas, key="t1_var")
        mu0 = st.number_input("Valor de referência (μ₀)", value=0.0, key="t1_mu0", format="%.4f")
        alt = componentes.escolher_alternativa("t1_alt", "média > μ₀", "média < μ₀")
        try:
            res = analisar_uma_amostra(df[var].to_numpy(dtype=float), mu0, alpha=alpha, alternativa=alt, nome=var)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            componentes.mostrar(res)

with aba_z:
    if ativa is None:
        st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    else:
        nome, df = ativa
        numericas = componentes.exigir_numericas(df, nome)
        var_z = st.selectbox("Variável", numericas, key="z1_var")
        c1, c2 = st.columns(2)
        mu0_z = c1.number_input("Valor de referência (μ₀)", value=0.0, key="z1_mu0", format="%.4f")
        sigma = c2.number_input("Desvio padrão populacional conhecido (σ)", value=1.0, min_value=0.0, key="z1_sigma")
        alt_z = componentes.escolher_alternativa("z1_alt", "média > μ₀", "média < μ₀")
        try:
            res_z = analisar_z(
                df[var_z].to_numpy(dtype=float), mu0_z, sigma, alpha=alpha, alternativa=alt_z, nome=var_z
            )
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            componentes.mostrar(res_z)

with aba_p:
    c1, c2, c3 = st.columns(3)
    x = c1.number_input("Ocorrências (x)", min_value=0, value=10, step=1, key="p1_x")
    n = c2.number_input("Total (n)", min_value=1, value=20, step=1, key="p1_n")
    p0 = c3.number_input("Proporção de referência (p₀)", min_value=0.0, max_value=1.0, value=0.5, key="p1_p0")
    alt_p = componentes.escolher_alternativa("p1_alt", "p > p₀", "p < p₀")
    try:
        res_p = analisar_uma_proporcao(int(x), int(n), float(p0), alpha=alpha, alternativa=alt_p)
    except ErroDeDados as exc:
        st.error(str(exc))
    else:
        componentes.mostrar(res_p)
