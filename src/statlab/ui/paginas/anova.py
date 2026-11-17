"""Página Três ou mais grupos: ANOVA de 1 fator + Tukey, ou Kruskal-Wallis + Mann-Whitney/Bonferroni."""

import pandas as pd
import streamlit as st

from statlab import graficos
from statlab.core.anova import analisar_grupos
from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.ui import componentes, estado

st.header("Três ou mais grupos (ANOVA)")
st.caption(
    "ANOVA se cada grupo for normal (ou n ≥ 30) e a maior variância for até 9 vezes a menor; senão, "
    "Kruskal-Wallis. Se houver diferença, as comparações mostram quais grupos diferem."
)

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()
nome, df = ativa
componentes.exigir_numericas(df, nome)
alpha = estado.alpha()
grupos = componentes.selecionar_grupos(df, "an", minimo=2)
if grupos is None:
    st.stop()

try:
    res = analisar_grupos(grupos, alpha=alpha)
except ErroDeDados as exc:
    st.error(str(exc))
    st.stop()

componentes.prerequisitos(res)
componentes.resultado(res)

if res.modelo.startswith("ANOVA"):
    st.markdown("**Análise de variância**")
    tabela_anova = pd.DataFrame(
        {
            "Fonte": ["Entre grupos", "Dentro (erro)", "Total"],
            "gl": [str(res.gl_entre), str(res.gl_dentro), str(res.gl_entre + res.gl_dentro)],
            "SQ": [num(res.sq_entre), num(res.sq_dentro), num(res.sq_total)],
            "QM": [num(res.qm_entre), num(res.qm_dentro), ""],
            "F": [num(res.estatistica, 3), "", ""],
            "p": [p_valor(res.p).removeprefix("= "), "", ""],
        }
    )
    st.dataframe(tabela_anova, hide_index=True)
    st.write(f"R² = {num(res.r2 * 100, 1)}%")
else:
    st.markdown("**Medianas**")
    st.dataframe(
        pd.DataFrame({"Grupo": list(res.medianas), "Mediana": [num(m) for m in res.medianas.values()]}),
        hide_index=True,
    )
if res.conferencia:
    st.caption(res.conferencia)

if res.comparacoes:
    st.subheader(f"Comparações 2 a 2 ({res.metodo_comparacoes})")
    linhas = []
    for c in res.comparacoes:
        linha = {"Par": f"{c.grupo_a} − {c.grupo_b}"}
        if c.diferenca is not None:
            linha["Diferença"] = num(c.diferenca)
        linha["p"] = p_valor(c.p).removeprefix("= ")
        if c.ic is not None:
            linha["IC 95%"] = f"({num(c.ic[0])}; {num(c.ic[1])})"
        linha["Diferem?"] = "sim" if c.significativo(res.alpha) else "não"
        linhas.append(linha)
    st.dataframe(pd.DataFrame(linhas), hide_index=True)
    if res.metodo_comparacoes == "Tukey HSD":
        st.plotly_chart(graficos.tukey_intervalos(res.comparacoes))
elif res.significativo is False:
    st.caption("Sem diferença significativa: comparações 2 a 2 não são necessárias.")

componentes.avisos(res)
componentes.calculo(res)

col1, col2 = st.columns(2)
col1.plotly_chart(graficos.intervalos(grupos))
col2.plotly_chart(graficos.boxplot(grupos))
