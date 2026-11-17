"""Página Dois grupos independentes: médias (t, Welch ou Mann-Whitney) e variâncias (F e Levene)."""

import streamlit as st

from statlab import graficos
from statlab.core.dados import ErroDeDados, amostra
from statlab.core.formatacao import num, p_valor
from statlab.core.testes_t import analisar_dois_grupos
from statlab.core.variancias import teste_f
from statlab.ui import componentes, estado

st.header("Dois grupos independentes")
st.caption(
    "Grupos com indivíduos diferentes. O teste é escolhido pelos pré-requisitos: t (variância combinada), "
    "t de Welch (variâncias diferentes) ou Mann-Whitney (sem normalidade e n < 30)."
)

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()
nome, df = ativa
componentes.exigir_numericas(df, nome)
alpha = estado.alpha()
aba_medias, aba_var = st.tabs(["Comparar médias", "Comparar variâncias"])

with aba_medias:
    grupos = componentes.selecionar_grupos(df, "g2", minimo=2, maximo=2)
    if grupos is not None:
        (nome_a, va), (nome_b, vb) = grupos.items()
        alt = componentes.escolher_alternativa("g2_alt", f"{nome_a} > {nome_b}", f"{nome_a} < {nome_b}")
        variavel = componentes.nome_variavel("g2_nome", componentes.nome_padrao_grupos("g2"))
        try:
            res = analisar_dois_grupos(va, vb, alpha=alpha, alternativa=alt, nome_a=nome_a, nome_b=nome_b)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            componentes.mostrar(res, variavel)
            fig = graficos.boxplot(grupos, titulo=f"{nome_a} × {nome_b}")
            st.plotly_chart(fig)
            componentes.botao_relatorio(
                "g2", componentes.item(res, f"Dois grupos: {nome_a} × {nome_b}", variavel, [fig])
            )

with aba_var:
    st.caption(
        "H₀: σ²₁ = σ²₂. O teste F é sensível à falta de normalidade; se os dados não forem normais, "
        "use o Levene (centrado na mediana), mostrado junto."
    )
    grupos_v = componentes.selecionar_grupos(df, "v2", minimo=2, maximo=2)
    if grupos_v is not None:
        (nome_a, va), (nome_b, vb) = grupos_v.items()
        try:
            a, _ = amostra(va, nome_a)
            b, _ = amostra(vb, nome_b)
            var = teste_f(a, b, alpha=alpha)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            componentes.resultado(var)
            st.write(f"Levene (mediana): p {p_valor(var.p_levene)}")
            st.write(f"Variâncias: {nome_a} = {num(float(a.var(ddof=1)))}; {nome_b} = {num(float(b.var(ddof=1)))}")
            componentes.conclusao(var, f"{nome_a} e {nome_b}")
            componentes.calculo(var)
            componentes.botao_relatorio(
                "v2", componentes.item(var, f"Variâncias: {nome_a} × {nome_b}", f"{nome_a} e {nome_b}")
            )
