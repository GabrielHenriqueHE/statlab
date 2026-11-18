"""Estat › Variâncias, ANOVA, Não paramétricos, Regressão e Tabelas."""

from __future__ import annotations

import numpy as np
import pandas as pd

from statlab.core import nao_parametricos as npar
from statlab.core import qui_quadrado as qq
from statlab.core import uma_amostra as ua
from statlab.core import variancias as var_mod
from statlab.core.anova import anova_um_fator, tukey_hsd, welch_anova
from statlab.core.anova_dois_fatores import analisar_anova_dois_fatores
from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.regressao_multipla import analisar_regressao_multipla, prever_multipla
from statlab.ui.comandos import _base as b
from statlab.ui.comandos import formulario as st

MENU = "Estat"


def _tabela_comparacoes(comparacoes, alpha: float) -> pd.DataFrame:
    linhas = []
    for c in comparacoes:
        linha = {"Par": f"{c.grupo_a} − {c.grupo_b}", "Método": c.metodo}
        if c.diferenca is not None:
            linha["Diferença"] = num(c.diferenca)
        linha["p"] = p_valor(c.p).removeprefix("= ")
        if c.ic is not None:
            linha["IC"] = f"({num(c.ic[0])}; {num(c.ic[1])})"
        linha["Significativo?"] = "sim" if c.significativo(alpha) else "não"
        linhas.append(linha)
    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------- variâncias


@b.comando(MENU, "Variâncias", "Teste F (2 variâncias)")
def teste_f_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    escolha = b.escolher_grupos(df, "vf", minimo=2, maximo=2)
    conf = b.confianca("vf_conf")
    if escolha is None:
        return
    grupos, notas = escolha

    def executar():
        (na, va), (nb, vb) = grupos.items()
        res = var_mod.teste_f(va, vb, alpha=b.alpha_de(conf))
        return b.item_de_resultado(res, f"Teste F: {na} × {nb}", notas=notas)

    b.rodar(executar)


@b.comando(MENU, "Variâncias", "Bartlett / Levene (k variâncias)")
def igualdade_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    escolha = b.escolher_grupos(df, "vk", minimo=2)
    metodo = st.radio("Teste", ["Bartlett (supõe normalidade)", "Levene (mediana, robusto)"], key="vk_met")
    conf = b.confianca("vk_conf")
    if escolha is None:
        return
    grupos, notas = escolha

    def executar():
        fn = var_mod.bartlett if metodo.startswith("Bartlett") else var_mod.levene
        res = fn(grupos, alpha=b.alpha_de(conf))
        desvios = pd.DataFrame({"Grupo": list(res.desvios), "DesvPad": [num(d, 4) for d in res.desvios.values()]})
        item = b.item_de_resultado(res, "Igualdade de variâncias", notas=notas)
        item.tabelas.append(("Desvios padrão", desvios))
        return item

    b.rodar(executar)


@b.comando(MENU, "Variâncias", "1 variância (χ²)")
def uma_variancia_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    var = b.escolher_coluna(df, "Variável", "v1_var")
    sigma0 = st.number_input("Desvio padrão hipotético (σ₀)", min_value=0.0, value=1.0, key="v1_s0", format="%.4f")
    alt = b.alternativa("v1_alt", "σ > σ₀", "σ < σ₀")
    conf = b.confianca("v1_conf")
    if var is None:
        return

    def executar():
        v = df[var].to_numpy(dtype=float)
        res = ua.qui_quadrado_variancia(v[~np.isnan(v)], sigma0, alpha=b.alpha_de(conf), alternativa=alt)
        return b.item_de_resultado(res, f"1 variância: {var}")

    b.rodar(executar)


# --------------------------------------------------------------------------- ANOVA


@b.comando(MENU, "ANOVA", "Um fator")
def anova_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    escolha = b.escolher_grupos(df, "an", minimo=2)
    com_tukey = st.checkbox("Comparações: Tukey", value=False, key="an_tukey")
    com_welch = st.checkbox("Também a ANOVA de Welch (não supõe variâncias iguais)", value=False, key="an_welch")
    conf = b.confianca("an_conf")
    excluir = b.excluir_extremos("an_out")
    if escolha is None:
        return
    grupos, notas_falta = escolha

    def executar():
        amostras, notas = b.aplicar_exclusao(grupos, excluir)
        notas = notas_falta + notas
        alpha = b.alpha_de(conf)
        res = anova_um_fator(amostras, alpha=alpha)
        tabela = pd.DataFrame(
            {
                "Fonte": ["Fator", "Erro", "Total"],
                "GL": [res.gl_entre, res.gl_dentro, res.gl_entre + res.gl_dentro],
                "SQ (Aj.)": [num(res.sq_entre, 3), num(res.sq_dentro, 3), num(res.sq_total, 3)],
                "QM (Aj.)": [num(res.qm_entre, 4), num(res.qm_dentro, 4), ""],
                "Valor F": [num(res.estatistica, 2), "", ""],
                "Valor-P": [p_valor(res.p).removeprefix("= "), "", ""],
            }
        )
        item = b.item_de_resultado(res, "ANOVA de um fator", notas=notas)
        item.tabelas.append(("Análise de variância", tabela))
        item.resultado.append(f"R² = {num(res.r2 * 100, 1)}%")
        if com_welch:
            f_w, p_w = welch_anova(amostras)
            item.resultado.append(f"ANOVA de Welch: F = {num(f_w, 2)}; p {p_valor(p_w)}")
        if com_tukey:
            comps = tukey_hsd(amostras, confianca=conf)
            item.tabelas.append((f"Tukey ({num(conf * 100, 0)}%)", _tabela_comparacoes(comps, alpha)))
        return item

    b.rodar(executar)


@b.comando(MENU, "ANOVA", "Dois fatores")
def anova2_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cols = list(df.columns)
    resposta = b.escolher_coluna(df, "Resposta (numérica)", "a2_y")
    c1, c2 = st.columns(2)
    fa = c1.selectbox("Fator A", cols, key="a2_a")
    fb = c2.selectbox("Fator B", cols, index=min(1, len(cols) - 1), key="a2_b")
    inter = st.checkbox("Incluir a interação", value=True, key="a2_int")
    conf = b.confianca("a2_conf")
    if resposta is None or fa == fb:
        st.info("Escolha dois fatores diferentes.")
        return

    def executar():
        res = analisar_anova_dois_fatores(df, resposta, fa, fb, interacao=inter, alpha=b.alpha_de(conf))
        tabela = pd.DataFrame(
            {
                "Fonte": [lin.fonte for lin in res.tabela],
                "GL": [str(lin.gl) for lin in res.tabela],
                "SQ (Aj.)": [num(lin.sq, 3) for lin in res.tabela],
                "QM (Aj.)": ["" if lin.qm is None else num(lin.qm, 4) for lin in res.tabela],
                "Valor F": ["" if lin.f is None else num(lin.f, 2) for lin in res.tabela],
                "Valor-P": ["" if lin.p is None else p_valor(lin.p).removeprefix("= ") for lin in res.tabela],
            }
        )
        item = b.item_de_resultado(res, f"ANOVA de dois fatores: {resposta}")
        item.tabelas.append(("Análise de variância (SQ ajustadas)", tabela))
        item.resultado += [
            f"S = {num(res.s, 4)}",
            f"R² = {num(res.r2 * 100, 2)}%",
            f"R²(aj) = {num(res.r2_aj * 100, 2)}%",
        ]
        return item

    b.rodar(executar)


# --------------------------------------------------------------------------- não paramétricos


@b.comando(MENU, "Não paramétricos", "Mann-Whitney")
def mann_whitney_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    escolha = b.escolher_grupos(df, "mw", minimo=2, maximo=2)
    conf = b.confianca("mw_conf")
    if escolha is None:
        return
    grupos, notas = escolha
    (na, _), (nb, _) = grupos.items()
    alt = b.alternativa("mw_alt", f"{na} > {nb}", f"{na} < {nb}")

    def executar():
        (nome_a, va), (nome_b, vb) = grupos.items()
        res = npar.mann_whitney(va, vb, alpha=b.alpha_de(conf), alternativa=alt, nome_a=nome_a, nome_b=nome_b)
        return b.item_de_resultado(res, f"Mann-Whitney: {nome_a} × {nome_b}", notas=notas)

    b.rodar(executar)


@b.comando(MENU, "Não paramétricos", "Wilcoxon (pareado)")
def wilcoxon_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cols = b.numericas(df, minimo=2)
    if not cols:
        return
    c1, c2 = st.columns(2)
    antes = c1.selectbox("Primeira amostra", cols, key="wx_a")
    depois = c2.selectbox("Segunda amostra", cols, index=1, key="wx_b")
    alt = b.alternativa("wx_alt", "1ª > 2ª", "1ª < 2ª")
    conf = b.confianca("wx_conf")
    if antes == depois:
        st.info("Escolha colunas diferentes.")
        return

    def executar():
        res = npar.wilcoxon_pareado(
            df[antes].to_numpy(dtype=float),
            df[depois].to_numpy(dtype=float),
            alpha=b.alpha_de(conf),
            alternativa=alt,
        )
        return b.item_de_resultado(res, f"Wilcoxon pareado: {antes} × {depois}")

    b.rodar(executar)


@b.comando(MENU, "Não paramétricos", "Wilcoxon de 1 amostra")
def wilcoxon1_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    var = b.escolher_coluna(df, "Variável", "w1_var")
    m0 = st.number_input("Mediana hipotética (m₀)", value=0.0, key="w1_m0", format="%.4f")
    alt = b.alternativa("w1_alt", "mediana > m₀", "mediana < m₀")
    conf = b.confianca("w1_conf")
    if var is None:
        return

    def executar():
        v = df[var].to_numpy(dtype=float)
        res = ua.wilcoxon_uma_amostra(v[~np.isnan(v)], m0, alpha=b.alpha_de(conf), alternativa=alt)
        return b.item_de_resultado(res, f"Wilcoxon de 1 amostra: {var}")

    b.rodar(executar)


@b.comando(MENU, "Não paramétricos", "Teste de sinal")
def sinal_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    var = b.escolher_coluna(df, "Variável", "sg_var")
    m0 = st.number_input("Mediana hipotética (m₀)", value=0.0, key="sg_m0", format="%.4f")
    alt = b.alternativa("sg_alt", "mediana > m₀", "mediana < m₀")
    conf = b.confianca("sg_conf")
    if var is None:
        return

    def executar():
        v = df[var].to_numpy(dtype=float)
        res = ua.teste_sinal(v[~np.isnan(v)], m0, alpha=b.alpha_de(conf), alternativa=alt)
        return b.item_de_resultado(res, f"Teste de sinal: {var}")

    b.rodar(executar)


@b.comando(MENU, "Não paramétricos", "Kruskal-Wallis")
def kruskal_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    escolha = b.escolher_grupos(df, "kw", minimo=2)
    com_pares = st.checkbox(
        "Comparações 2 a 2 (Mann-Whitney com Bonferroni)",
        value=False,
        key="kw_pares",
        help="Fora da apostila revisada.",
    )
    conf = b.confianca("kw_conf")
    if escolha is None:
        return
    grupos, notas = escolha

    def executar():
        alpha = b.alpha_de(conf)
        res = npar.kruskal_wallis(grupos, alpha=alpha)
        medianas = pd.DataFrame({"Grupo": list(res.medianas), "Mediana": [num(m) for m in res.medianas.values()]})
        item = b.item_de_resultado(res, "Kruskal-Wallis", notas=notas)
        item.tabelas.append(("Medianas", medianas))
        if com_pares:
            comps = npar.comparacoes_mann_whitney_bonferroni(grupos)
            item.tabelas.append(("Comparações 2 a 2 (Bonferroni)", _tabela_comparacoes(comps, alpha)))
        return item

    b.rodar(executar)


# --------------------------------------------------------------------------- regressão


def _regressao(df, resposta: str, preditores: list[str], conf: float, titulo: str):
    res = analisar_regressao_multipla(df, resposta, preditores, alpha=b.alpha_de(conf))
    coefs = pd.DataFrame(
        {
            "Termo": [c.termo for c in res.coeficientes],
            "Coef": [num(c.coef, 4) for c in res.coeficientes],
            "EP de Coef": [num(c.ep, 4) for c in res.coeficientes],
            "Valor-T": [num(c.t, 2) for c in res.coeficientes],
            "Valor-P": [p_valor(c.p).removeprefix("= ") for c in res.coeficientes],
            "VIF": ["" if c.vif is None else num(c.vif, 2) for c in res.coeficientes],
        }
    )
    anova = pd.DataFrame(
        {
            "Fonte": ["Regressão", "Erro", "Total"],
            "GL": [res.gl_regressao, res.gl_residuo, res.gl_regressao + res.gl_residuo],
            "SQ": [num(res.sq_regressao, 3), num(res.sq_residuo, 3), num(res.sq_total, 3)],
            "QM": [num(res.sq_regressao / res.gl_regressao, 4), num(res.sq_residuo / res.gl_residuo, 4), ""],
            "Valor F": [num(res.estatistica, 2), "", ""],
            "Valor-P": [p_valor(res.p).removeprefix("= "), "", ""],
        }
    )
    item = b.item_de_resultado(res, titulo)
    item.tabelas += [("Coeficientes", coefs), ("Análise de variância", anova)]
    item.resultado = [
        f"Equação: {res.equacao}",
        f"S = {num(res.s, 4)}",
        f"R² = {num(res.r2 * 100, 2)}%",
        f"R²(aj) = {num(res.r2_aj * 100, 2)}%",
        f"R²(pred) = {num(res.r2_pred * 100, 2)}%",
        *item.resultado,
    ]
    return res, item


@b.comando(MENU, "Regressão", "Regressão simples")
def regressao_simples_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cols = b.numericas(df, minimo=2)
    if not cols:
        return
    c1, c2 = st.columns(2)
    y = c1.selectbox("Resposta (Y)", cols, key="rs_y")
    x = c2.selectbox("Preditor (X)", cols, index=1, key="rs_x")
    conf = b.confianca("rs_conf")
    if x == y:
        st.info("Escolha colunas diferentes.")
        return

    def executar():
        _, item = _regressao(df, y, [x], conf, f"Regressão: {y} em função de {x}")
        return item

    b.rodar(executar)


@b.comando(MENU, "Regressão", "Regressão múltipla")
def regressao_multipla_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cols = b.numericas(df, minimo=2)
    if not cols:
        return
    y = st.selectbox("Resposta (Y)", cols, key="rm_y")
    xs = st.multiselect("Preditores", [c for c in cols if c != y], default=[c for c in cols if c != y][:2], key="rm_x")
    conf = b.confianca("rm_conf")
    prever = st.checkbox("Incluir predição", value=False, key="rm_prev")
    valores = {}
    if prever and xs:
        colunas = st.columns(min(4, len(xs)))
        for i, c in enumerate(xs):
            valores[c] = colunas[i % len(colunas)].number_input(c, value=float(df[c].mean()), key=f"rm_v_{c}")
    if not xs:
        st.info("Escolha pelo menos um preditor.")
        return

    def executar():
        res, item = _regressao(df, y, xs, conf, f"Regressão múltipla: {y}")
        if prever:
            pv = prever_multipla(res, valores)
            item.resultado.append(
                f"Predição: ajuste = {num(pv.ajuste, 4)}; IC = ({num(pv.ic[0])}; {num(pv.ic[1])}); "
                f"IP = ({num(pv.ip[0])}; {num(pv.ip[1])})"
            )
            if pv.aviso:
                item.avisos.append(pv.aviso)
        return item

    b.rodar(executar)


# --------------------------------------------------------------------------- tabelas


@b.comando(MENU, "Tabelas", "Qui-quadrado de independência")
def independencia_cmd() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    _, df = alvo
    cols = list(df.columns)
    c1, c2 = st.columns(2)
    linhas = c1.selectbox("Linhas", cols, key="qi_l")
    colunas = c2.selectbox("Colunas", cols, index=min(1, len(cols) - 1), key="qi_c")
    metodo = st.radio("Método", ["Qui-quadrado de Pearson", "Exato de Fisher (2 × 2)"], key="qi_met")
    conf = b.confianca("qi_conf")
    if linhas == colunas:
        st.info("Escolha colunas diferentes.")
        return

    def executar():
        try:
            tab = qq.tabela_contingencia(df, linhas, colunas)
        except ErroDeDados as exc:
            raise ErroDeDados(str(exc)) from exc
        res = qq.independencia(tab, metodo="chi2" if metodo.startswith("Qui") else "fisher", alpha=b.alpha_de(conf))
        item = b.item_de_resultado(res, f"Qui-quadrado: {linhas} × {colunas}")
        item.tabelas.append(("Contagens observadas", tab.reset_index(names=linhas)))
        return item

    b.rodar(executar)


@b.comando(MENU, "Tabelas", "Qui-quadrado de aderência")
def aderencia_cmd() -> None:
    texto = st.text_area("Contagens observadas (uma por linha ou separadas por ';')", "20; 30; 25; 25", key="qa_obs")
    cats = st.text_input("Categorias (opcional, separadas por ';')", "", key="qa_cat")
    props = st.text_input("Proporções esperadas (opcional, separadas por ';')", "", key="qa_pro")
    conf = b.confianca("qa_conf")

    def executar():
        from statlab.core.dados import parse_lista

        obs = [v for v in parse_lista(texto) if v is not None]
        categorias = [c.strip() for c in cats.split(";") if c.strip()] or None
        proporcoes = [v for v in parse_lista(props) if v is not None] or None
        res = qq.aderencia(obs, categorias=categorias, proporcoes=proporcoes, alpha=b.alpha_de(conf))
        tab = pd.DataFrame(
            {
                "Categoria": res.colunas,
                "Observado": [num(v, 0) for v in res.observados[0]],
                "Esperado": [num(v, 2) for v in res.esperados[0]],
            }
        )
        item = b.item_de_resultado(res, "Qui-quadrado de aderência")
        item.tabelas.append(("Observado × esperado", tab))
        return item

    b.rodar(executar)
