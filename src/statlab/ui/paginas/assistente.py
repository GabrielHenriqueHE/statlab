"""Página Assistente "Qual teste usar?": por perguntas (árvore de decisão) ou rodando a análise nos dados."""

import pandas as pd
import streamlit as st

from statlab.core import assistente, qui_quadrado, tabela
from statlab.core.dados import ErroDeDados
from statlab.ui import componentes, estado

st.header("Qual teste usar?")
st.caption("Segue a Tabela 2 da apostila: paramétrico se os pré-requisitos forem atendidos; senão, o não paramétrico.")

alpha = estado.alpha()
CHAVES = list(assistente.OBJETIVOS)
RESPOSTAS = {"Sim": True, "Não": False, "Não sei": None}


def _rotulo(chave: str) -> str:
    return assistente.OBJETIVOS[chave].descricao


def _pergunta(rotulo: str, chave: str) -> bool | None:
    return RESPOSTAS[st.radio(rotulo, list(RESPOSTAS), index=2, key=chave, horizontal=True)]


aba_perguntas, aba_dados, aba_tabela = st.tabs(["Pelas perguntas", "Pelos meus dados", "Tabela de referência"])

# ---------------------------------------------------------------- árvore de decisão
with aba_perguntas:
    objetivo = st.radio("Qual é o objetivo?", CHAVES, format_func=_rotulo, key="as_obj")
    respostas: dict[str, object] = {}
    if objetivo == "relacao":
        respostas["normal"] = _pergunta("x e y são normais (Shapiro-Wilk p > α)?", "as_normal")
    elif objetivo in ("dois_grupos", "pareado", "tres_grupos", "uma_amostra"):
        alvo = "As diferenças (antes − depois)" if objetivo == "pareado" else "Os dados de cada grupo"
        respostas["normal"] = _pergunta(f"{alvo} são normais (Shapiro-Wilk p > α)?", "as_normal")
        respostas["n_grande"] = st.checkbox("Todos os grupos têm n ≥ 30", key="as_n30")
        if objetivo == "dois_grupos":
            respostas["variancias_iguais"] = _pergunta("As variâncias são iguais (teste F, p > α)?", "as_var")
        if objetivo == "tres_grupos":
            respostas["razao_ate_9"] = _pergunta("A maior variância é até 9 vezes a menor?", "as_razao")
    elif objetivo == "proporcoes":
        respostas["npq_ok"] = _pergunta("n·p·q ≥ 5 e n·p, n·q ≥ 5 em cada grupo?", "as_npq")
    else:
        respostas["esperados_ok"] = _pergunta(
            "As contagens esperadas atendem o critério (nenhuma < 1, ≤ 20% < 5)?", "as_esp"
        )
        respostas["tabela_2x2"] = st.checkbox("A tabela é 2 × 2", key="as_2x2")

    decisao = assistente.decidir(objetivo, **respostas)
    for linha in decisao.caminho:
        st.markdown(f"- {linha}")
    if decisao.teste:
        st.success(f"Use: **{decisao.teste}** — página **{decisao.pagina}**.")
    for pendencia in decisao.pendencias:
        st.info(pendencia)

# ---------------------------------------------------------------- com os dados
with aba_dados:
    objetivo_d = st.selectbox("Qual é o objetivo?", CHAVES, format_func=_rotulo, key="as_obj_dados")
    ativa = estado.ativa()
    argumentos: dict[str, object] | None = None
    if objetivo_d == "proporcoes":
        c1, c2, c3, c4 = st.columns(4)
        argumentos = {
            "x1": int(c1.number_input("Ocorrências 1", min_value=0, value=31, key="asd_x1")),
            "n1": int(c2.number_input("Total 1", min_value=1, value=62, key="asd_n1")),
            "x2": int(c3.number_input("Ocorrências 2", min_value=0, value=117, key="asd_x2")),
            "n2": int(c4.number_input("Total 2", min_value=1, value=182, key="asd_n2")),
        }
    elif ativa is None:
        st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    else:
        _, df = ativa
        numericas = tabela.colunas_numericas(df)
        if objetivo_d in ("relacao", "pareado"):
            if len(numericas) < 2:
                st.info("São necessárias duas colunas numéricas.")
            else:
                c1, c2 = st.columns(2)
                rot = ("X", "Y") if objetivo_d == "relacao" else ("Antes", "Depois")
                col1 = c1.selectbox(rot[0], numericas, key="asd_c1")
                col2 = c2.selectbox(rot[1], numericas, index=1, key="asd_c2")
                if col1 == col2:
                    st.info("Escolha colunas diferentes.")
                elif objetivo_d == "relacao":
                    argumentos = {"x": df[col1].tolist(), "y": df[col2].tolist(), "nome_x": col1, "nome_y": col2}
                else:
                    argumentos = {"antes": df[col1].tolist(), "depois": df[col2].tolist()}
        elif objetivo_d == "dois_grupos":
            grupos = componentes.selecionar_grupos(df, "asd_g2", minimo=2, maximo=2)
            if grupos is not None:
                (na, va), (nb, vb) = grupos.items()
                argumentos = {"a": va, "b": vb, "nome_a": na, "nome_b": nb}
        elif objetivo_d == "tres_grupos":
            grupos = componentes.selecionar_grupos(df, "asd_g3", minimo=2)
            if grupos is not None:
                argumentos = {"grupos": grupos}
        elif objetivo_d == "associacao":
            colunas = list(df.columns)
            c1, c2 = st.columns(2)
            col_l = c1.selectbox("Linhas", colunas, key="asd_lin")
            col_c = c2.selectbox("Colunas", colunas, index=min(1, len(colunas) - 1), key="asd_col")
            try:
                argumentos = {"tabela": qui_quadrado.tabela_contingencia(df, col_l, col_c)}
            except ErroDeDados as exc:
                st.error(str(exc))
        elif not numericas:
            st.info("A worksheet não tem colunas numéricas.")
        else:
            var = st.selectbox("Variável", numericas, key="asd_var")
            mu0 = st.number_input("Valor de referência (μ₀)", value=0.0, key="asd_mu0")
            argumentos = {"valores": df[var].to_numpy(dtype=float), "mu0": mu0, "nome": var}

    if argumentos is not None:
        try:
            res = assistente.analisar(objetivo_d, alpha=alpha, **argumentos)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            st.subheader("Caminho da decisão")
            for linha in assistente.caminho(objetivo_d, res):
                st.markdown(f"- {linha}")
            componentes.resultado(res)
            componentes.avisos(res)
            st.caption(
                f"Para gráficos e o cálculo completo, abra a página **{assistente.OBJETIVOS[objetivo_d].pagina}**."
            )

# ---------------------------------------------------------------- tabela
with aba_tabela:
    st.dataframe(
        pd.DataFrame(
            {
                "Objetivo": [o.descricao for o in assistente.OBJETIVOS.values()],
                "Teste paramétrico": [o.parametrico for o in assistente.OBJETIVOS.values()],
                "Pré-requisitos principais": [o.prerequisitos for o in assistente.OBJETIVOS.values()],
                "Não paramétrico": [o.nao_parametrico for o in assistente.OBJETIVOS.values()],
                "Página": [o.pagina for o in assistente.OBJETIVOS.values()],
            }
        ),
        hide_index=True,
    )
