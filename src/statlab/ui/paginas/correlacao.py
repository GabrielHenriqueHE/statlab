"""Página Correlação e regressão: Pearson ou Spearman (pela normalidade), força, r² e reta de regressão."""

import numpy as np
import streamlit as st

from statlab import graficos
from statlab.core.correlacao import analisar_correlacao
from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num
from statlab.core.regressao import analisar_regressao, prever
from statlab.ui import componentes, estado

st.header("Correlação e regressão")
st.caption(
    "Pearson se x e y forem normais; senão, Spearman. A força só é classificada se a correlação for "
    "significativa, e a regressão só deve ser feita nesse caso."
)

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()
nome, df = ativa
numericas = componentes.exigir_numericas(df, nome, minimo=2)
alpha = estado.alpha()
c1, c2 = st.columns(2)
x = c1.selectbox("X (variável independente)", numericas, key="cor_x")
y = c2.selectbox("Y (variável dependente)", numericas, index=1, key="cor_y")
if x == y:
    st.info("Escolha colunas diferentes para X e Y.")
    st.stop()

try:
    cor = analisar_correlacao(df[x].tolist(), df[y].tolist(), alpha=alpha, nome_x=x, nome_y=y)
except ErroDeDados as exc:
    st.error(str(exc))
    st.stop()

componentes.prerequisitos(cor)
componentes.resultado(cor)
componentes.conclusao(cor)
m1, m2, m3, m4 = st.columns(4)
m1.metric("r (Pearson)", num(cor.r, 3))
m2.metric("rₛ (Spearman)", num(cor.r_s, 3))
m3.metric("r²", f"{num(cor.r2 * 100, 1)}%")
m4.metric("Força", cor.forca or "—")
st.caption(
    f"Valores críticos de |r| para n = {cor.n} (tabela A.6): {num(cor.r_critico_5, 3)} (5%) e "
    f"{num(cor.r_critico_1, 3)} (1%)."
)
componentes.avisos(cor)
componentes.calculo(cor)

st.subheader("Regressão linear simples")
forcar = st.checkbox(
    "Calcular a reta mesmo sem correlação significativa (não recomendado)", value=False, key="reg_forcar"
)
reg = analisar_regressao(df[x].tolist(), df[y].tolist(), alpha=alpha, forcar=forcar, nome_x=x, nome_y=y)
for aviso in reg.avisos:
    if aviso not in cor.avisos:
        st.warning(aviso)
if reg.permitida:
    st.markdown(f"**{reg.equacao}**")
    st.caption(
        f"a = {num(reg.a, 4)}: a cada unidade a mais de {x}, {y} {'aumenta' if reg.a > 0 else 'diminui'} "
        f"em média {num(abs(reg.a), 3)}. b = {num(reg.b, 3)}: valor estimado de {y} quando {x} = 0 "
        "(só faz sentido se 0 estiver na faixa observada)."
    )
    x0 = st.number_input(
        f"Prever {y} para {x} =", value=float(np.round(np.mean(cor.x_usado), 2)), key="reg_x0", format="%.4f"
    )
    yhat, aviso_ext = prever(reg, x0)
    st.metric(f"ŷ para {x} = {num(x0)}", num(yhat, 3))
    if aviso_ext:
        st.warning(aviso_ext)
    componentes.conclusao(reg)
else:
    st.info("A regressão não deve ser feita: a correlação não é significativa.")

fig = graficos.dispersao(
    cor.x_usado, cor.y_usado, linha_regressao=reg.permitida, nome_x=x, nome_y=y, titulo=f"{y} × {x}"
)
st.plotly_chart(fig)
itens = [componentes.item(cor, f"Correlação: {x} × {y}", figuras=[fig])]
if reg.permitida:
    itens.append(componentes.item(reg, f"Regressão: {y} em função de {x}"))
componentes.botao_relatorio("cor", *itens)
