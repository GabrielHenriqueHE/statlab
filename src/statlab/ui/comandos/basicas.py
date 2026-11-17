"""Estat › Estatísticas básicas: descritivas, normalidade, testes t, proporções e correlação."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from statlab.core import correlacao as cor_mod
from statlab.core import uma_amostra as ua
from statlab.core.descritiva import matriz_covariancia, resumo_estatistico
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import anderson_darling, shapiro_wilk
from statlab.core.proporcoes import fisher_duas_proporcoes, z_duas_proporcoes
from statlab.core.testes_t import t_independente, t_pareado
from statlab.ui.comandos import _base as b

MENU, GRUPO = "Estat", "Estatísticas básicas"


@b.comando(MENU, GRUPO, "Exibição de estatísticas descritivas")
def descritivas() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    vars_ = b.escolher_variaveis(df, "Variáveis", "desc_vars")
    conf = b.confianca("desc_conf")
    if not vars_:
        st.info("Escolha pelo menos uma variável.")
        return

    def executar():
        linhas = []
        for v in vars_:
            r = resumo_estatistico(df[v].tolist(), confianca=conf)
            linhas.append(
                {
                    "Variável": v,
                    "N": r.n,
                    "N*": r.n_faltantes,
                    "Média": num(r.media),
                    "EP Média": num(r.ep_media),
                    "DesvPad": num(r.dp),
                    "Mínimo": num(r.minimo),
                    "Q1": num(r.q1),
                    "Mediana": num(r.mediana),
                    "Q3": num(r.q3),
                    "Máximo": num(r.maximo),
                    "Assimetria": num(r.assimetria),
                    "Curtose": num(r.curtose),
                    f"IC {num(conf * 100, 0)}%": f"({num(r.ic_media[0])}; {num(r.ic_media[1])})",
                }
            )
        return b.item_simples(
            "Estatísticas descritivas",
            comando_nome="Descritivas",
            tabelas=[("Estatísticas", pd.DataFrame(linhas))],
        )

    b.rodar(executar)


@b.comando(MENU, GRUPO, "Covariância")
def covariancia() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    vars_ = b.escolher_variaveis(df, "Variáveis (2 ou mais)", "cov_vars", padrao=2)
    if len(vars_) < 2:
        st.info("Escolha pelo menos duas variáveis.")
        return

    def executar():
        cov, pares = matriz_covariancia(df, vars_)
        return b.item_simples(
            "Covariância",
            comando_nome="Covariância",
            tabelas=[
                ("Matriz de covariância", cov.reset_index(names="")),
                ("Pares completos", pares.reset_index(names="")),
            ],
        )

    b.rodar(executar)


@b.comando(MENU, GRUPO, "Teste de normalidade")
def normalidade() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    var = b.escolher_coluna(df, "Variável", "norm_var")
    metodo = st.radio("Teste", ["Anderson-Darling (padrão do Minitab)", "Shapiro-Wilk"], key="norm_met")
    conf = b.confianca("norm_conf")
    if var is None:
        return

    def executar():
        v = df[var].to_numpy(dtype=float)
        v = v[~np.isnan(v)]
        alpha = b.alpha_de(conf)
        if metodo.startswith("Anderson"):
            res = anderson_darling(v, alpha=alpha, nome=var)
        else:
            res = shapiro_wilk(v, alpha=alpha, tcl=False, nome=var)
        return b.item_de_resultado(res, f"Normalidade: {var}")

    b.rodar(executar)


@b.comando(MENU, GRUPO, "t de 1 amostra")
def t_uma() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    var = b.escolher_coluna(df, "Variável", "t1_var")
    mu0 = st.number_input("Média hipotética (μ₀)", value=0.0, key="t1_mu0", format="%.4f")
    alt = b.alternativa("t1_alt", "média > μ₀", "média < μ₀")
    conf = b.confianca("t1_conf")
    excluir = b.excluir_extremos("t1_out")
    if var is None:
        return

    def executar():
        v = df[var].to_numpy(dtype=float)
        v = v[~np.isnan(v)]
        amostras, notas = b.aplicar_exclusao({var: v}, excluir)
        res = ua.t_uma_amostra(amostras[var], mu0, alpha=b.alpha_de(conf), alternativa=alt)
        return b.item_de_resultado(res, f"t de 1 amostra: {var}", notas=notas)

    b.rodar(executar)


@b.comando(MENU, GRUPO, "Z de 1 amostra (σ conhecido)")
def z_uma() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    var = b.escolher_coluna(df, "Variável", "z1_var")
    c1, c2 = st.columns(2)
    mu0 = c1.number_input("Média hipotética (μ₀)", value=0.0, key="z1_mu0", format="%.4f")
    sigma = c2.number_input("Desvio padrão conhecido (σ)", value=1.0, min_value=0.0, key="z1_sigma")
    alt = b.alternativa("z1_alt", "média > μ₀", "média < μ₀")
    conf = b.confianca("z1_conf")
    if var is None:
        return

    def executar():
        v = df[var].to_numpy(dtype=float)
        res = ua.z_uma_amostra(v[~np.isnan(v)], mu0, sigma, alpha=b.alpha_de(conf), alternativa=alt)
        return b.item_de_resultado(res, f"Z de 1 amostra: {var}")

    b.rodar(executar)


@b.comando(MENU, GRUPO, "t de 2 amostras")
def t_duas() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    escolha = b.escolher_grupos(df, "t2", minimo=2, maximo=2)
    iguais = st.checkbox(
        "Assumir variâncias iguais (variância combinada)",
        value=False,
        key="t2_iguais",
        help="Desmarcado, usa o t de Welch. Para avaliar, rode Estat › Variâncias › Teste F.",
    )
    conf = b.confianca("t2_conf")
    excluir = b.excluir_extremos("t2_out")
    if escolha is None:
        return
    grupos, notas_falta = escolha
    (na, _), (nb, _) = grupos.items()
    alt = b.alternativa("t2_alt", f"{na} > {nb}", f"{na} < {nb}")

    def executar():
        amostras, notas = b.aplicar_exclusao(grupos, excluir)
        notas = notas_falta + notas
        (nome_a, va), (nome_b, vb) = amostras.items()
        res = t_independente(
            va,
            vb,
            variancias_iguais=iguais,
            alpha=b.alpha_de(conf),
            alternativa=alt,
            nome_a=nome_a,
            nome_b=nome_b,
            confianca=conf,
        )
        return b.item_de_resultado(res, f"t de 2 amostras: {nome_a} × {nome_b}", notas=notas)

    b.rodar(executar)


@b.comando(MENU, GRUPO, "t pareado")
def t_par() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cols = b.numericas(df, minimo=2)
    if not cols:
        return
    c1, c2 = st.columns(2)
    antes = c1.selectbox("Primeira amostra", cols, key="tp_a")
    depois = c2.selectbox("Segunda amostra", cols, index=1, key="tp_b")
    alt = b.alternativa("tp_alt", "1ª > 2ª", "1ª < 2ª")
    conf = b.confianca("tp_conf")
    if antes == depois:
        st.info("Escolha colunas diferentes.")
        return

    def executar():
        res = t_pareado(
            df[antes].to_numpy(dtype=float),
            df[depois].to_numpy(dtype=float),
            alpha=b.alpha_de(conf),
            alternativa=alt,
        )
        return b.item_de_resultado(res, f"t pareado: {antes} × {depois}")

    b.rodar(executar)


@b.comando(MENU, GRUPO, "1 proporção")
def uma_proporcao() -> None:
    c1, c2, c3 = st.columns(3)
    x = c1.number_input("Eventos (x)", min_value=0, value=10, step=1, key="p1_x")
    n = c2.number_input("Tentativas (n)", min_value=1, value=20, step=1, key="p1_n")
    p0 = c3.number_input("Proporção hipotética (p₀)", min_value=0.0, max_value=1.0, value=0.5, key="p1_p0")
    metodo = st.radio("Método", ["Aproximação normal (z)", "Binomial exata"], key="p1_met")
    alt = b.alternativa("p1_alt", "p > p₀", "p < p₀")
    conf = b.confianca("p1_conf")

    def executar():
        fn = ua.z_uma_proporcao if metodo.startswith("Aproximação") else ua.binomial_uma_proporcao
        res = fn(int(x), int(n), float(p0), alpha=b.alpha_de(conf), alternativa=alt, confianca=conf)
        return b.item_de_resultado(res, "1 proporção")

    b.rodar(executar)


@b.comando(MENU, GRUPO, "2 proporções")
def duas_proporcoes() -> None:
    c1, c2 = st.columns(2)
    x1 = c1.number_input("Eventos — amostra 1", min_value=0, value=31, step=1, key="p2_x1")
    n1 = c1.number_input("Tentativas — amostra 1", min_value=1, value=62, step=1, key="p2_n1")
    x2 = c2.number_input("Eventos — amostra 2", min_value=0, value=117, step=1, key="p2_x2")
    n2 = c2.number_input("Tentativas — amostra 2", min_value=1, value=182, step=1, key="p2_n2")
    metodo = st.radio("Método", ["Aproximação normal (z)", "Exato de Fisher"], key="p2_met")
    alt = b.alternativa("p2_alt", "p₁ > p₂", "p₁ < p₂")
    conf = b.confianca("p2_conf")

    def executar():
        fn = z_duas_proporcoes if metodo.startswith("Aproximação") else fisher_duas_proporcoes
        res = fn(
            int(x1),
            int(n1),
            int(x2),
            int(n2),
            alpha=b.alpha_de(conf),
            alternativa=alt,
            nome_1="Amostra 1",
            nome_2="Amostra 2",
        )
        linhas = [f"p̂1 = {num(res.p1, 4)}; p̂2 = {num(res.p2, 4)}; diferença = {num(res.diferenca, 4)}"]
        item = b.item_de_resultado(res, "2 proporções")
        item.resultado = linhas + item.resultado
        return item

    b.rodar(executar)


@b.comando(MENU, GRUPO, "Correlação")
def correlacao_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cols = b.numericas(df, minimo=2)
    if not cols:
        return
    c1, c2 = st.columns(2)
    x = c1.selectbox("Variável X", cols, key="cor_x")
    y = c2.selectbox("Variável Y", cols, index=1, key="cor_y")
    metodo = st.radio("Método", ["Pearson", "Spearman"], key="cor_met", horizontal=True)
    conf = b.confianca("cor_conf")
    if x == y:
        st.info("Escolha colunas diferentes.")
        return

    def executar():
        res = cor_mod.correlacao(
            df[x].tolist(), df[y].tolist(), metodo=metodo, alpha=b.alpha_de(conf), nome_x=x, nome_y=y
        )
        item = b.item_de_resultado(res, f"Correlação: {x} × {y}")
        item.resultado += [
            f"r (Pearson) = {num(res.r, 4)} (p {p_valor(res.p_pearson)})",
            f"rₛ (Spearman) = {num(res.r_s, 4)} (p {p_valor(res.p_spearman)})",
            f"r² = {num(res.r2 * 100, 1)}%; força de |r| = {res.forca}",
            f"Críticos da tabela A.6 (n = {res.n}): {num(res.r_critico_5, 3)} a 5%; {num(res.r_critico_1, 3)} a 1%",
        ]
        return item

    b.rodar(executar)
