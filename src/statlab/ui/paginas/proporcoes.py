"""Página Duas proporções: teste z (aproximação normal) ou exato de Fisher."""

import pandas as pd
import streamlit as st

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num
from statlab.core.proporcoes import analisar_proporcoes
from statlab.ui import componentes, estado

st.header("Duas proporções")
st.caption(
    "Compara a proporção de um evento (sim/não) entre dois grupos independentes. Pré-requisito: n·p·q ≥ 5 "
    "(apostila) e n·p ≥ 5, n·q ≥ 5; se falhar, usa-se o exato de Fisher."
)
alpha = estado.alpha()
SUMARIZADO = "Dados sumarizados (contagens)"
COLUNAS = "A partir de colunas da worksheet"
modo = st.radio("Origem dos dados", [SUMARIZADO, COLUNAS], key="pr_modo", horizontal=True)

dados = None
if modo == SUMARIZADO:
    c1, c2, c3 = st.columns(3)
    nome_1 = c1.text_input("Grupo 1", value="Grupo 1", key="pr_n1")
    x1 = c2.number_input("Ocorrências no grupo 1", min_value=0, value=31, step=1, key="pr_x1")
    t1 = c3.number_input("Total do grupo 1", min_value=1, value=62, step=1, key="pr_t1")
    c4, c5, c6 = st.columns(3)
    nome_2 = c4.text_input("Grupo 2", value="Grupo 2", key="pr_n2")
    x2 = c5.number_input("Ocorrências no grupo 2", min_value=0, value=117, step=1, key="pr_x2")
    t2 = c6.number_input("Total do grupo 2", min_value=1, value=182, step=1, key="pr_t2")
    dados = (int(x1), int(t1), int(x2), int(t2), nome_1, nome_2)
else:
    ativa = estado.ativa()
    if ativa is None:
        st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    else:
        _, df = ativa
        colunas = list(df.columns)
        resultado_col = st.selectbox("Coluna com o resultado (ex.: aprovado/reprovado)", colunas, key="pr_res")
        valores = [str(v) for v in pd.unique(df[resultado_col].dropna())]
        evento = st.selectbox("Valor que conta como ocorrência", valores, key="pr_evento") if valores else None
        grupo_col = st.selectbox(
            "Coluna com os grupos", [c for c in colunas if c != resultado_col] or colunas, key="pr_grupo"
        )
        niveis = [str(v) for v in pd.unique(df[grupo_col].dropna())]
        escolhidos = st.multiselect("Os dois grupos", niveis, default=niveis[:2], key="pr_niveis", max_selections=2)
        if evento is None or len(escolhidos) != 2:
            st.info("Escolha o valor da ocorrência e exatamente dois grupos.")
        else:
            base = df[[resultado_col, grupo_col]].dropna().astype(str)
            contagens = []
            for g in escolhidos:
                sub = base[base[grupo_col] == g]
                contagens.append((int((sub[resultado_col] == evento).sum()), len(sub)))
            (x1, t1), (x2, t2) = contagens
            st.caption(f"{escolhidos[0]}: {x1} de {t1}; {escolhidos[1]}: {x2} de {t2}.")
            dados = (x1, t1, x2, t2, escolhidos[0], escolhidos[1])

if dados is not None:
    x1, t1, x2, t2, nome_1, nome_2 = dados
    alt = componentes.escolher_alternativa("pr_alt", f"p({nome_1}) > p({nome_2})", f"p({nome_1}) < p({nome_2})")
    variavel = componentes.nome_variavel("pr_nome", "ocorrência")
    try:
        res = analisar_proporcoes(x1, t1, x2, t2, alpha=alpha, alternativa=alt, nome_1=nome_1, nome_2=nome_2)
    except ErroDeDados as exc:
        st.error(str(exc))
    else:
        c1, c2 = st.columns(2)
        c1.metric(f"p̂ ({nome_1})", num(res.p1, 4))
        c2.metric(f"p̂ ({nome_2})", num(res.p2, 4))
        componentes.mostrar(res, variavel)
        componentes.botao_relatorio("pr", componentes.item(res, f"Duas proporções: {nome_1} × {nome_2}", variavel))
