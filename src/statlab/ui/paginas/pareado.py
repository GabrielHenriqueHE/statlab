"""Página Antes × depois: dados pareados (t pareado ou Wilcoxon), sobre as diferenças d = antes − depois."""

import numpy as np
import streamlit as st

from statlab import graficos
from statlab.core.dados import ErroDeDados
from statlab.core.testes_t import analisar_antes_depois
from statlab.ui import componentes, estado

st.header("Antes × depois (dados pareados)")
st.caption(
    "Os mesmos indivíduos medidos duas vezes, na mesma linha. A normalidade exigida é a das diferenças "
    "(ou n ≥ 30); senão, usa-se o Wilcoxon."
)

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()
nome, df = ativa
numericas = componentes.exigir_numericas(df, nome, minimo=2)
alpha = estado.alpha()
c1, c2 = st.columns(2)
antes = c1.selectbox("Antes", numericas, key="par_antes")
depois = c2.selectbox("Depois", numericas, index=1, key="par_depois")
if antes == depois:
    st.info("Escolha colunas diferentes para antes e depois.")
    st.stop()
alt = componentes.escolher_alternativa("par_alt", "antes > depois (diminuiu)", "antes < depois (aumentou)")
variavel = componentes.nome_variavel("par_nome", "o valor")
try:
    res = analisar_antes_depois(df[antes].tolist(), df[depois].tolist(), alpha=alpha, alternativa=alt)
except ErroDeDados as exc:
    st.error(str(exc))
else:
    componentes.mostrar(res, variavel)
    d = df[antes].to_numpy(dtype=float) - df[depois].to_numpy(dtype=float)
    fig = graficos.boxplot({"d = antes − depois": d[~np.isnan(d)]}, titulo="Diferenças (antes − depois)")
    st.plotly_chart(fig)
    componentes.botao_relatorio("par", componentes.item(res, f"Antes × depois: {antes} × {depois}", variavel, [fig]))
