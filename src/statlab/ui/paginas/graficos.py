"""Página Gráficos: tipos de gráfico do menu Gráficos do Minitab, sobre a worksheet ativa."""

import streamlit as st

from statlab import graficos
from statlab.core import tabela
from statlab.core.dados import ErroDeDados
from statlab.ui import estado

TIPOS = [
    "Histograma",
    "Boxplot",
    "Diagrama de dispersão",
    "Valores individuais",
    "Intervalos (IC da média)",
    "Probabilidade normal",
    "Pareto",
    "Gráfico de barras",
    "Série temporal",
    "Correlograma",
    "Matriz de dispersão",
]

st.header("Gráficos")

ativa = estado.ativa()
if ativa is None:
    st.info("Não há worksheet. Importe ou cole dados na página **Dados**.")
    st.stop()

nome, df = ativa
numericas = tabela.colunas_numericas(df)
textuais = tabela.colunas_texto(df)
tipo = st.selectbox("Tipo de gráfico", TIPOS, key="graf_tipo")


def _dados_por_grupo(vars_: list[str], agrupar: str) -> dict[str, object]:
    if agrupar == "(nenhum)":
        return {v: df[v].to_numpy(dtype=float) for v in vars_}
    return {str(nivel): serie.to_numpy(dtype=float) for nivel, serie in df.groupby(agrupar, sort=False)[vars_[0]]}


def _variaveis(rotulo: str, chave: str, padrao: int = 1) -> list[str]:
    if not numericas:
        st.warning("A worksheet não tem colunas numéricas.")
        st.stop()
    return st.multiselect(rotulo, numericas, default=numericas[:padrao], key=chave) or []


fig = None
titulo_arquivo = tipo.lower().replace(" ", "_").replace("(", "").replace(")", "")
try:
    if tipo == "Histograma":
        vars_ = _variaveis("Variáveis", "h_vars")
        curva = st.checkbox("Mostrar curva normal ajustada", value=True, key="h_curva")
        if vars_:
            fig = graficos.histograma(_dados_por_grupo(vars_, "(nenhum)"), curva_normal=curva)
        else:
            st.info("Escolha pelo menos uma variável.")

    elif tipo in ("Boxplot", "Valores individuais", "Intervalos (IC da média)"):
        vars_ = _variaveis("Variável(is) numérica(s)", "g_vars")
        agrupar = st.selectbox(
            "Agrupar por (opcional: uma variável de grupo, usa a 1ª variável)",
            ["(nenhum)", *textuais],
            key="g_grupo",
        )
        if not vars_:
            st.info("Escolha pelo menos uma variável.")
        else:
            dados = _dados_por_grupo(vars_, agrupar)
            if tipo == "Boxplot":
                fig = graficos.boxplot(dados)
            elif tipo == "Valores individuais":
                fig = graficos.valores_individuais(dados)
            else:
                fig = graficos.intervalos(dados)

    elif tipo == "Diagrama de dispersão":
        col1, col2 = st.columns(2)
        x = col1.selectbox("X", numericas, key="d_x")
        y = col2.selectbox("Y", numericas, index=min(1, len(numericas) - 1), key="d_y")
        grupo = st.selectbox("Grupo por cor (opcional)", ["(nenhum)", *textuais], key="d_grupo")
        reta = st.checkbox("Mostrar reta de regressão", value=False, key="d_reta")
        mascara = df[[x, y]].notna().all(axis=1)
        fig = graficos.dispersao(
            df.loc[mascara, x].to_numpy(dtype=float),
            df.loc[mascara, y].to_numpy(dtype=float),
            grupos=df.loc[mascara, grupo].to_numpy() if grupo != "(nenhum)" else None,
            linha_regressao=reta,
            nome_x=x,
            nome_y=y,
            titulo=f"{y} × {x}",
        )

    elif tipo == "Probabilidade normal":
        vars_ = _variaveis("Variável", "p_vars")
        if vars_:
            fig = graficos.probabilidade_normal(df[vars_[0]].to_numpy(dtype=float))
        else:
            st.info("Escolha uma variável.")

    elif tipo == "Pareto":
        cat = st.selectbox("Coluna de categorias", list(df.columns), key="p_cat")
        contagem = st.selectbox(
            "Coluna de contagens (ou contar ocorrências)", ["(contar ocorrências)", *numericas], key="p_cont"
        )
        if contagem == "(contar ocorrências)":
            contagens = df[cat].dropna().astype(str).value_counts()
            fig = graficos.pareto(list(contagens.index), contagens.to_numpy())
        else:
            base = df[[cat, contagem]].dropna().groupby(cat)[contagem].sum()
            fig = graficos.pareto(list(base.index.astype(str)), base.to_numpy())

    elif tipo == "Gráfico de barras":
        cat = st.selectbox("Categorias", list(df.columns), key="b_cat")
        val = st.selectbox("Valores (média por categoria)", numericas, key="b_val")
        base = df[[cat, val]].dropna().groupby(cat)[val].mean()
        fig = graficos.barras(list(base.index.astype(str)), base.to_numpy(), titulo=f"Média de {val} por {cat}")

    elif tipo == "Série temporal":
        val = st.selectbox("Variável", numericas, key="s_val")
        rot = st.selectbox("Rótulos do eixo X (opcional)", ["(ordem das linhas)", *df.columns], key="s_rot")
        rotulos = None if rot == "(ordem das linhas)" else df[rot].tolist()
        fig = graficos.serie_temporal(df[val].tolist(), rotulos=rotulos, titulo=f"{val} ao longo do tempo", nome_y=val)

    elif tipo == "Correlograma":
        vars_ = _variaveis("Variáveis (≥ 2)", "c_vars", padrao=min(3, len(numericas)))
        if len(vars_) >= 2:
            fig = graficos.correlograma(df[vars_])
        else:
            st.info("Escolha pelo menos 2 variáveis para o correlograma.")

    elif tipo == "Matriz de dispersão":
        vars_ = _variaveis("Variáveis (≥ 2)", "m_vars", padrao=min(3, len(numericas)))
        if len(vars_) >= 2:
            linhas = int(df[vars_].dropna().shape[0])
            st.caption(f"Linhas completas usadas: {linhas} de {len(df)}.")
            fig = graficos.matriz_dispersao(df, vars_)
        else:
            st.info("Escolha pelo menos 2 variáveis para a matriz de dispersão.")
except ErroDeDados as exc:
    st.error(str(exc))
    fig = None

if fig is not None:
    st.plotly_chart(fig)
    st.download_button(
        "Baixar gráfico (HTML interativo)",
        data=graficos.html(fig),
        file_name=f"{titulo_arquivo}.html",
        mime="text/html",
        key="baixar_html",
    )
    st.caption("Para uma imagem PNG, use o ícone de câmera no canto do gráfico.")
