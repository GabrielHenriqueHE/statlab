"""Página Regressão múltipla: coeficientes, sumário do modelo, ANOVA, predição e resíduos (como no Minitab)."""

import pandas as pd
import streamlit as st

from statlab import graficos
from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.regressao_multipla import analisar_regressao_multipla, prever_multipla
from statlab.ui import componentes, estado

st.header("Regressão múltipla")
st.caption(
    "Uma resposta (Y) explicada por um ou mais preditores (X). Para um único X, prefira a página "
    "Correlação e regressão, que segue a apostila."
)

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()
nome, df = ativa
numericas = componentes.exigir_numericas(df, nome, minimo=2)
alpha = estado.alpha()
resposta = st.selectbox("Resposta (Y)", numericas, index=len(numericas) - 1, key="rm_y")
candidatos = [c for c in numericas if c != resposta]
preditores = st.multiselect("Preditores (X)", candidatos, default=candidatos, key="rm_x")
if not preditores:
    st.info("Escolha pelo menos um preditor.")
    st.stop()

try:
    reg = analisar_regressao_multipla(df, resposta, preditores, alpha=alpha)
except ErroDeDados as exc:
    st.error(str(exc))
    st.stop()

componentes.prerequisitos(reg)
componentes.resultado(reg)
st.markdown(f"**Equação:** {reg.equacao}")

st.markdown("**Coeficientes**")
st.dataframe(
    pd.DataFrame(
        {
            "Termo": [c.termo for c in reg.coeficientes],
            "Coef": [num(c.coef, 4) for c in reg.coeficientes],
            "EP de Coef": [num(c.ep, 4) for c in reg.coeficientes],
            "Valor-T": [num(c.t, 2) for c in reg.coeficientes],
            "Valor-P": [p_valor(c.p).removeprefix("= ") for c in reg.coeficientes],
            "VIF": ["" if c.vif is None else num(c.vif, 2) for c in reg.coeficientes],
        }
    ),
    hide_index=True,
)
m1, m2, m3, m4 = st.columns(4)
m1.metric("S", num(reg.s, 4))
m2.metric("R²", f"{num(reg.r2 * 100, 2)}%")
m3.metric("R²(aj)", f"{num(reg.r2_aj * 100, 2)}%")
m4.metric("R²(pred)", f"{num(reg.r2_pred * 100, 2)}%")
st.markdown("**Análise de variância**")
st.dataframe(
    pd.DataFrame(
        {
            "Fonte": ["Regressão", "Erro", "Total"],
            "GL": [str(reg.gl_regressao), str(reg.gl_residuo), str(reg.gl_regressao + reg.gl_residuo)],
            "SQ": [num(reg.sq_regressao, 3), num(reg.sq_residuo, 3), num(reg.sq_total, 3)],
            "QM": [num(reg.sq_regressao / reg.gl_regressao, 4), num(reg.sq_residuo / reg.gl_residuo, 4), ""],
            "F": [num(reg.estatistica, 2), "", ""],
            "Valor-P": [p_valor(reg.p).removeprefix("= "), "", ""],
        }
    ),
    hide_index=True,
)
componentes.avisos(reg)
componentes.calculo(reg)

st.subheader("Predição")
colunas = st.columns(min(4, len(preditores)))
valores = {}
for i, c in enumerate(preditores):
    lo, hi = reg.faixas[c]
    valores[c] = colunas[i % len(colunas)].number_input(c, value=float((lo + hi) / 2), key=f"rm_prev_{c}")
prev = prever_multipla(reg, valores)
p1, p2, p3, p4 = st.columns(4)
p1.metric("Ajuste (ŷ)", num(prev.ajuste, 4))
p2.metric("EP do ajuste", num(prev.ep_ajuste, 4))
p3.metric("IC 95% (média)", f"({num(prev.ic[0])}; {num(prev.ic[1])})")
p4.metric("IP 95% (nova obs.)", f"({num(prev.ip[0])}; {num(prev.ip[1])})")
if prev.aviso:
    st.warning(prev.aviso)

st.plotly_chart(graficos.residuos_quatro(reg.residuos, reg.ajustados))
