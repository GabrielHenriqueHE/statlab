"""Menu Gráfico: os tipos do menu Gráficos do Minitab, sobre a worksheet ativa."""

from __future__ import annotations

import streamlit as st

from statlab import graficos
from statlab.core import tabela as tab_mod
from statlab.ui.comandos import _base as b

MENU = "Gráfico"
SEM_GRUPO = "(nenhum)"


def _por_grupo(df, vars_, agrupar):
    if agrupar == SEM_GRUPO:
        return {v: df[v].to_numpy(dtype=float) for v in vars_}
    return {str(n): s.to_numpy(dtype=float) for n, s in df.groupby(agrupar, sort=False)[vars_[0]]}


def _grafico_de_grupos(chave: str, titulo: str, desenhar) -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    vars_ = b.escolher_variaveis(df, "Variáveis", f"{chave}_vars")
    agrupar = st.selectbox(
        "Agrupar por (opcional; usa a 1ª variável)", [SEM_GRUPO, *tab_mod.colunas_texto(df)], key=f"{chave}_gr"
    )
    if not vars_:
        st.info("Escolha pelo menos uma variável.")
        return

    def executar():
        fig = desenhar(_por_grupo(df, vars_, agrupar))
        return b.item_simples(titulo, comando_nome=titulo, figuras=[fig])

    b.rodar(executar, "Desenhar")


@b.comando(MENU, "", "Histograma")
def histograma() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    vars_ = b.escolher_variaveis(df, "Variáveis", "h_vars")
    curva = st.checkbox("Mostrar a curva normal ajustada", value=True, key="h_curva")
    if not vars_:
        st.info("Escolha pelo menos uma variável.")
        return

    def executar():
        fig = graficos.histograma({v: df[v].to_numpy(dtype=float) for v in vars_}, curva_normal=curva)
        return b.item_simples("Histograma", comando_nome="Histograma", figuras=[fig])

    b.rodar(executar, "Desenhar")


@b.comando(MENU, "", "Boxplot")
def boxplot() -> None:
    _grafico_de_grupos("bx", "Boxplot", graficos.boxplot)


@b.comando(MENU, "", "Gráfico de valores individuais")
def valores_individuais() -> None:
    _grafico_de_grupos("vi", "Gráfico de valores individuais", graficos.valores_individuais)


@b.comando(MENU, "", "Gráfico de intervalos (IC da média)")
def intervalos() -> None:
    _grafico_de_grupos("iv", "Gráfico de intervalos", graficos.intervalos)


@b.comando(MENU, "", "Diagrama de dispersão")
def dispersao() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cols = b.numericas(df, minimo=2)
    if not cols:
        return
    c1, c2 = st.columns(2)
    x = c1.selectbox("X", cols, key="d_x")
    y = c2.selectbox("Y", cols, index=1, key="d_y")
    grupo = st.selectbox("Grupo por cor (opcional)", [SEM_GRUPO, *tab_mod.colunas_texto(df)], key="d_gr")
    reta = st.checkbox("Mostrar a reta de regressão", value=False, key="d_reta")

    def executar():
        mascara = df[[x, y]].notna().all(axis=1)
        fig = graficos.dispersao(
            df.loc[mascara, x].to_numpy(dtype=float),
            df.loc[mascara, y].to_numpy(dtype=float),
            grupos=df.loc[mascara, grupo].to_numpy() if grupo != SEM_GRUPO else None,
            linha_regressao=reta,
            nome_x=x,
            nome_y=y,
            titulo=f"{y} × {x}",
        )
        return b.item_simples(f"Dispersão: {y} × {x}", comando_nome="Dispersão", figuras=[fig])

    b.rodar(executar, "Desenhar")


@b.comando(MENU, "", "Gráfico de probabilidade normal")
def probabilidade_normal() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    var = b.escolher_coluna(df, "Variável", "pn_var")
    if var is None:
        return

    def executar():
        fig = graficos.probabilidade_normal(df[var].to_numpy(dtype=float))
        return b.item_simples(f"Probabilidade normal: {var}", comando_nome="Probabilidade normal", figuras=[fig])

    b.rodar(executar, "Desenhar")


@b.comando(MENU, "", "Gráfico de Pareto")
def pareto() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cat = st.selectbox("Coluna de categorias", list(df.columns), key="pa_cat")
    contagem = st.selectbox("Contagens", ["(contar ocorrências)", *tab_mod.colunas_numericas(df)], key="pa_cont")

    def executar():
        if contagem == "(contar ocorrências)":
            cont = df[cat].dropna().astype(str).value_counts()
            fig = graficos.pareto(list(cont.index), cont.to_numpy())
        else:
            base = df[[cat, contagem]].dropna().groupby(cat)[contagem].sum()
            fig = graficos.pareto(list(base.index.astype(str)), base.to_numpy())
        return b.item_simples("Gráfico de Pareto", comando_nome="Pareto", figuras=[fig])

    b.rodar(executar, "Desenhar")


@b.comando(MENU, "", "Gráfico de barras")
def barras() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cat = st.selectbox("Categorias", list(df.columns), key="ba_cat")
    val = b.escolher_coluna(df, "Valores (média por categoria)", "ba_val")
    if val is None:
        return

    def executar():
        base = df[[cat, val]].dropna().groupby(cat)[val].mean()
        fig = graficos.barras(list(base.index.astype(str)), base.to_numpy(), titulo=f"Média de {val} por {cat}")
        return b.item_simples("Gráfico de barras", comando_nome="Barras", figuras=[fig])

    b.rodar(executar, "Desenhar")


@b.comando(MENU, "", "Série temporal")
def serie_temporal() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    val = b.escolher_coluna(df, "Variável", "st_val")
    rot = st.selectbox("Rótulos do eixo X (opcional)", ["(ordem das linhas)", *df.columns], key="st_rot")
    if val is None:
        return

    def executar():
        rotulos = None if rot == "(ordem das linhas)" else df[rot].tolist()
        fig = graficos.serie_temporal(df[val].tolist(), rotulos=rotulos, titulo=f"{val} ao longo do tempo", nome_y=val)
        return b.item_simples(f"Série temporal: {val}", comando_nome="Série temporal", figuras=[fig])

    b.rodar(executar, "Desenhar")


@b.comando(MENU, "", "Correlograma")
def correlograma() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    vars_ = b.escolher_variaveis(df, "Variáveis (≥ 2)", "cg_vars", padrao=3)
    if len(vars_) < 2:
        st.info("Escolha pelo menos duas variáveis.")
        return

    def executar():
        return b.item_simples("Correlograma", comando_nome="Correlograma", figuras=[graficos.correlograma(df[vars_])])

    b.rodar(executar, "Desenhar")


@b.comando(MENU, "", "Matriz de dispersão")
def matriz_dispersao() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    vars_ = b.escolher_variaveis(df, "Variáveis (≥ 2)", "md_vars", padrao=3)
    if len(vars_) < 2:
        st.info("Escolha pelo menos duas variáveis.")
        return

    def executar():
        linhas = int(df[vars_].dropna().shape[0])
        return b.item_simples(
            "Matriz de dispersão",
            comando_nome="Matriz de dispersão",
            linhas=[f"Linhas completas usadas: {linhas} de {len(df)}."],
            figuras=[graficos.matriz_dispersao(df, vars_)],
        )

    b.rodar(executar, "Desenhar")
