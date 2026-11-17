"""Página Variâncias: teste de uma variância (χ²) e igualdade de variâncias entre 2 ou mais grupos."""

import pandas as pd
import streamlit as st

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.uma_amostra import analisar_uma_variancia
from statlab.core.variancias import igualdade_variancias
from statlab.ui import componentes, estado

st.header("Variâncias")
st.caption(
    "Fora da apostila revisada, exceto o teste F de dois grupos (que também aparece na página Dois grupos). "
    "Equivalem aos testes de 1 variância e de variâncias iguais do Minitab."
)

alpha = estado.alpha()
ativa = estado.ativa()
aba_um, aba_k = st.tabs(["Uma variância (χ²)", "Igualdade de variâncias (2 ou mais grupos)"])

with aba_um:
    st.caption(
        "Compara o desvio padrão de uma amostra com um valor de referência (σ₀). Exige normalidade mesmo com "
        "n ≥ 30: o TCL não vale para variâncias."
    )
    if ativa is None:
        st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    else:
        nome, df = ativa
        numericas = componentes.exigir_numericas(df, nome)
        var = st.selectbox("Variável", numericas, key="v1_var")
        sigma0 = st.number_input(
            "Desvio padrão de referência (σ₀)", value=1.0, min_value=0.0, key="v1_sigma0", format="%.4f"
        )
        alt = componentes.escolher_alternativa("v1_alt", "σ > σ₀", "σ < σ₀")
        variavel = componentes.nome_variavel("v1_nome", var)
        try:
            res = analisar_uma_variancia(df[var].to_numpy(dtype=float), sigma0, alpha=alpha, alternativa=alt, nome=var)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            componentes.mostrar(res, variavel)
            if res.ic_variancia is not None:
                st.caption(
                    f"IC 95% para a variância (σ²): ({num(res.ic_variancia[0], 4)}; {num(res.ic_variancia[1], 4)})"
                )
            componentes.botao_relatorio("v1", componentes.item(res, f"Uma variância: {var}", variavel))

with aba_k:
    st.caption(
        "Grupos normais: teste F (2 grupos) ou Bartlett (3 ou mais). Algum grupo não normal: Levene centrado na "
        "mediana, robusto à falta de normalidade. A razão maior/menor variância (critério ≤ 9 da ANOVA) é "
        "mostrada junto."
    )
    if ativa is None:
        st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    else:
        nome, df = ativa
        componentes.exigir_numericas(df, nome)
        grupos = componentes.selecionar_grupos(df, "vk")
        if grupos is not None:
            variavel_k = componentes.nome_variavel("vk_nome", componentes.nome_padrao_grupos("vk"))
            try:
                res_k = igualdade_variancias(grupos, alpha=alpha)
            except ErroDeDados as exc:
                st.error(str(exc))
            else:
                componentes.mostrar(res_k, variavel_k)
                st.subheader("Todos os testes")
                linhas = []
                if res_k.p_f is not None:
                    linhas.append({"Teste": "F (razão de variâncias)", "Exige normalidade": "sim", "p": res_k.p_f})
                linhas += [
                    {"Teste": "Bartlett", "Exige normalidade": "sim", "p": res_k.p_bartlett},
                    {"Teste": "Levene (mediana)", "Exige normalidade": "não", "p": res_k.p_levene},
                ]
                for linha in linhas:
                    linha["Decidiu?"] = "✔" if linha["Teste"].startswith(res_k.metodo) else ""
                    linha["p"] = p_valor(linha["p"]).removeprefix("= ")
                st.dataframe(pd.DataFrame(linhas), hide_index=True)
                st.dataframe(
                    pd.DataFrame(
                        {"Grupo": list(res_k.desvios), "Desvio padrão": [num(d, 4) for d in res_k.desvios.values()]}
                    ),
                    hide_index=True,
                )
                st.metric("Razão maior/menor variância", num(res_k.razao, 2))
                if res_k.razao > 9:
                    st.caption(
                        "Razão > 9: pelo critério da disciplina, a ANOVA não deve ser usada (vai para Kruskal-Wallis)."
                    )
                else:
                    st.caption("Razão ≤ 9: atende ao critério de variâncias da ANOVA na disciplina.")
                componentes.botao_relatorio("vk", componentes.item(res_k, "Igualdade de variâncias", variavel_k))
