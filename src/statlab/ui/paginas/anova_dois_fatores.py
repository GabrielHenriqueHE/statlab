"""Página ANOVA de dois fatores: tabela com SQ ajustadas, efeitos principais e interação (como no Minitab)."""

import pandas as pd
import streamlit as st

from statlab import graficos
from statlab.core.anova_dois_fatores import analisar_anova_dois_fatores
from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.ui import componentes, estado

st.header("ANOVA de dois fatores")
st.caption(
    "Uma resposta numérica e dois fatores (colunas com os níveis). Com interação, cada combinação de níveis "
    "precisa de réplicas. Os dados devem estar empilhados: uma linha por observação."
)

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()
nome, df = ativa
numericas = componentes.exigir_numericas(df, nome)
alpha = estado.alpha()
if len(df.columns) < 3:
    st.info("São necessárias três colunas: a resposta e os dois fatores.")
    st.stop()
resposta = st.selectbox("Resposta (numérica)", numericas, key="a2_y")
outras = [c for c in df.columns if c != resposta]
c1, c2 = st.columns(2)
fator_a = c1.selectbox("Fator A", outras, key="a2_a")
fator_b = c2.selectbox("Fator B", [c for c in outras if c != fator_a], key="a2_b")
com_interacao = st.checkbox("Incluir a interação A*B", value=True, key="a2_inter")

try:
    res = analisar_anova_dois_fatores(df, resposta, fator_a, fator_b, interacao=com_interacao, alpha=alpha)
except ErroDeDados as exc:
    st.error(str(exc))
    st.stop()

componentes.prerequisitos(res)
componentes.resultado(res)
st.markdown("**Análise de variância (SQ ajustadas)**")
st.dataframe(
    pd.DataFrame(
        {
            "Fonte": [lin.fonte for lin in res.tabela],
            "GL": [str(lin.gl) for lin in res.tabela],
            "SQ (Aj.)": [num(lin.sq, 3) for lin in res.tabela],
            "QM (Aj.)": ["" if lin.qm is None else num(lin.qm, 4) for lin in res.tabela],
            "Valor F": ["" if lin.f is None else num(lin.f, 2) for lin in res.tabela],
            "Valor-P": ["" if lin.p is None else p_valor(lin.p).removeprefix("= ") for lin in res.tabela],
            "Significativo?": [
                "" if lin.p is None else ("sim" if lin.significativa(res.alpha) else "não") for lin in res.tabela
            ],
        }
    ),
    hide_index=True,
)
m1, m2, m3 = st.columns(3)
m1.metric("S", num(res.s, 4))
m2.metric("R²", f"{num(res.r2 * 100, 2)}%")
m3.metric("R²(aj)", f"{num(res.r2_aj * 100, 2)}%")
componentes.avisos(res)
componentes.calculo(res)

col1, col2 = st.columns(2)
col1.plotly_chart(
    graficos.efeitos_principais(res.medias_a, res.medias_b, res.media_geral, nome_a=fator_a, nome_b=fator_b)
)
col2.plotly_chart(graficos.interacao(res.medias_celulas, res.niveis_a, res.niveis_b, nome_a=fator_a, nome_b=fator_b))
st.plotly_chart(graficos.residuos_quatro(res.residuos, res.ajustados))
