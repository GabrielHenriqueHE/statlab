"""Teste de normalidade (Shapiro-Wilk) e a regra do Teorema Central do Limite da disciplina."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from statlab.core.dados import exigir_minimo, exigir_variacao
from statlab.core.formatacao import p_valor
from statlab.core.resultados import ALPHA_PADRAO, ATENCAO, FALHA, OK, Resultado, Verificacao

N_MINIMO_TCL = 30


@dataclass(kw_only=True)
class Normalidade(Resultado):
    """``normal``: p > α (não se rejeita a normalidade).
    ``atende``: pré-requisito atendido — normal, ou n ≥ 30 quando o atalho do TCL é permitido.
    ``pelo_tcl``: atendido apenas pelo TCL (não normal, mas n ≥ 30).
    """

    normal: bool = False
    atende: bool = False
    pelo_tcl: bool = False


def shapiro_wilk(
    v: np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    tcl: bool = True,
    nome: str = "amostra",
) -> Normalidade:
    """Shapiro-Wilk sobre ``v``.

    ``tcl=False`` desliga o atalho n ≥ 30 (usado na correlação, onde a regra não se aplica).
    """
    v = np.asarray(v, dtype=float)
    exigir_minimo(v, 3, nome)
    exigir_variacao(v, nome)
    estat, p = stats.shapiro(v)
    normal = bool(p > alpha)
    n = len(v)
    pelo_tcl = (not normal) and tcl and n >= N_MINIMO_TCL
    atende = normal or pelo_tcl

    if normal:
        conc = "pode-se assumir normalidade"
    elif pelo_tcl:
        conc = f"não normal, mas n = {n} ≥ {N_MINIMO_TCL} (TCL) → requisito atendido"
    else:
        conc = f"NÃO normal e n = {n} < {N_MINIMO_TCL}"
    passos = [f"Shapiro-Wilk ({nome}): W = {estat:.3f}; p {p_valor(float(p))} → {conc}"]

    return Normalidade(
        nome="Shapiro-Wilk",
        alpha=alpha,
        estatistica=float(estat),
        rotulo_estatistica="W",
        p=float(p),
        n=n,
        normal=normal,
        atende=atende,
        pelo_tcl=pelo_tcl,
        passos=passos,
    )


# ----------------------------------------------------------------------------- Anderson-Darling (padrão do Minitab)


def estatistica_anderson_darling(v: np.ndarray) -> float:
    """A² = −n − (1/n) Σ (2i − 1)[ln Φ(z_i) + ln(1 − Φ(z_{n+1−i}))], com média e desvio amostrais (ddof = 1)."""
    v = np.sort(np.asarray(v, dtype=float))
    n = len(v)
    exigir_minimo(v, 3, "Anderson-Darling")
    exigir_variacao(v, "Anderson-Darling")
    z = (v - v.mean()) / v.std(ddof=1)
    cdf = stats.norm.cdf(z)
    eps = 1e-300
    i = np.arange(1, n + 1)
    soma = np.sum((2 * i - 1) * (np.log(np.maximum(cdf, eps)) + np.log(np.maximum(1 - cdf[::-1], eps))))
    return float(-n - soma / n)


def p_anderson_darling(a2: float, n: int) -> float:
    """p-valor de Stephens (D'Agostino & Stephens, 1986) para normalidade com média e variância estimadas.

    É a aproximação usada pelo Minitab. Ex.: A² = 0,2524 com n = 50 dá p ≈ 0,724 (relatório da brochure).
    """
    a = a2 * (1 + 0.75 / n + 2.25 / n**2)
    if a < 0.2:
        p = 1 - np.exp(-13.436 + 101.14 * a - 223.73 * a**2)
    elif a < 0.34:
        p = 1 - np.exp(-8.318 + 42.796 * a - 59.938 * a**2)
    elif a < 0.6:
        p = np.exp(0.9177 - 4.279 * a - 1.38 * a**2)
    elif a <= 13:
        p = np.exp(1.2937 - 5.709 * a + 0.0186 * a**2)
    else:
        p = 0.0
    return float(min(1.0, max(0.0, p)))


def anderson_darling(v: np.ndarray, *, alpha: float = ALPHA_PADRAO, nome: str = "amostra") -> Normalidade:
    """Teste de normalidade Anderson-Darling (o padrão do Minitab). Não usa o atalho do TCL."""
    v = np.asarray(v, dtype=float)
    exigir_minimo(v, 3, nome)
    exigir_variacao(v, nome)
    a2 = estatistica_anderson_darling(v)
    p = p_anderson_darling(a2, len(v))
    normal = bool(p > alpha)
    conc = "pode-se assumir normalidade" if normal else "rejeita-se a normalidade"
    return Normalidade(
        nome="Anderson-Darling",
        alpha=alpha,
        estatistica=a2,
        rotulo_estatistica="A²",
        p=p,
        n=len(v),
        normal=normal,
        atende=normal,
        pelo_tcl=False,
        passos=[f"Anderson-Darling ({nome}): A² = {a2:.4f}; p {p_valor(p)} → {conc}"],
    )


def verificacao_normalidade(norm: Normalidade, nome: str, consequencia_falha: str = "") -> Verificacao:
    """✓ normal; ⚠ não normal mas n ≥ 30 (TCL); ✗ não normal (``consequencia_falha`` diz o que muda)."""
    if norm.normal:
        status = OK
    elif norm.pelo_tcl:
        status = ATENCAO
    else:
        status = FALHA
    detalhe = norm.passos[0]
    if status == FALHA and consequencia_falha:
        detalhe += f" → {consequencia_falha}"
    return Verificacao(nome=f"Normalidade — {nome}", status=status, detalhe=detalhe)
