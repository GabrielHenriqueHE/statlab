"""Página Uma amostra: média (t ou Wilcoxon), média com σ conhecido (Z), mediana (sinal) e uma proporção."""

import streamlit as st

from statlab.core.dados import ErroDeDados
from statlab.core.uma_amostra import analisar_sinal, analisar_uma_amostra, analisar_uma_proporcao, analisar_z
from statlab.ui import componentes, estado

st.header("Uma amostra")
st.caption("Compara a média (ou a proporção) de uma amostra com um valor de referência. Fora da apostila revisada.")

alpha = estado.alpha()
ativa = estado.ativa()
aba_t, aba_z, aba_s, aba_p = st.tabs(
    ["Média (t ou Wilcoxon)", "Média com σ conhecido (Z)", "Mediana (teste de sinal)", "Proporção"]
)

with aba_t:
    if ativa is None:
        st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    else:
        nome, df = ativa
        numericas = componentes.exigir_numericas(df, nome)
        var = st.selectbox("Variável", numericas, key="t1_var")
        mu0 = st.number_input("Valor de referência (μ₀)", value=0.0, key="t1_mu0", format="%.4f")
        alt = componentes.escolher_alternativa("t1_alt", "média > μ₀", "média < μ₀")
        variavel = componentes.nome_variavel("t1_nome", var)
        try:
            res = analisar_uma_amostra(df[var].to_numpy(dtype=float), mu0, alpha=alpha, alternativa=alt, nome=var)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            componentes.mostrar(res, variavel)
            componentes.botao_relatorio("t1", componentes.item(res, f"Uma amostra: {var}", variavel))

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
        variavel_z = componentes.nome_variavel("z1_nome", var_z)
        try:
            res_z = analisar_z(
                df[var_z].to_numpy(dtype=float), mu0_z, sigma, alpha=alpha, alternativa=alt_z, nome=var_z
            )
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            componentes.mostrar(res_z, variavel_z)
            componentes.botao_relatorio("z1", componentes.item(res_z, f"Teste Z: {var_z}", variavel_z))

with aba_s:
    st.caption(
        "Conta quantos valores ficam acima e abaixo da mediana de referência (binomial exata). Não exige "
        "normalidade. Para dados pareados, aplique-o à coluna das diferenças (antes − depois) com m₀ = 0."
    )
    if ativa is None:
        st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    else:
        nome, df = ativa
        numericas = componentes.exigir_numericas(df, nome)
        var_s = st.selectbox("Variável", numericas, key="s1_var")
        m0 = st.number_input("Mediana de referência (m₀)", value=0.0, key="s1_m0", format="%.4f")
        alt_s = componentes.escolher_alternativa("s1_alt", "mediana > m₀", "mediana < m₀")
        variavel_s = componentes.nome_variavel("s1_nome", var_s)
        try:
            res_s = analisar_sinal(df[var_s].to_numpy(dtype=float), m0, alpha=alpha, alternativa=alt_s, nome=var_s)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            componentes.mostrar(res_s, variavel_s)
            componentes.botao_relatorio("s1", componentes.item(res_s, f"Teste de sinal: {var_s}", variavel_s))

with aba_p:
    c1, c2, c3 = st.columns(3)
    x = c1.number_input("Ocorrências (x)", min_value=0, value=10, step=1, key="p1_x")
    n = c2.number_input("Total (n)", min_value=1, value=20, step=1, key="p1_n")
    p0 = c3.number_input("Proporção de referência (p₀)", min_value=0.0, max_value=1.0, value=0.5, key="p1_p0")
    alt_p = componentes.escolher_alternativa("p1_alt", "p > p₀", "p < p₀")
    variavel_p = componentes.nome_variavel("p1_nome", "ocorrência")
    try:
        res_p = analisar_uma_proporcao(int(x), int(n), float(p0), alpha=alpha, alternativa=alt_p)
    except ErroDeDados as exc:
        st.error(str(exc))
    else:
        componentes.mostrar(res_p, variavel_p)
        componentes.botao_relatorio("p1", componentes.item(res_p, "Uma proporção", variavel_p))
