"""Testes de normalidade (Shapiro-Wilk, Anderson-Darling, Ryan-Joiner) e a regra do TCL da disciplina."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados, exigir_minimo, exigir_variacao
from statlab.core.formatacao import num, p_valor
from statlab.core.resultados import ALPHA_PADRAO, ATENCAO, FALHA, OK, Resultado, Verificacao

N_MINIMO_TCL = 30
N_MINIMO_RJ = 9  # abaixo disso a tabela de p do Ryan-Joiner não é monótona (cor10 > cor05 > cor01 falha)
N_CONFIAVEL_RJ = 25  # abaixo disso, por simulação, a taxa de rejeição com dados normais passa de α
ALFA_MINIMO_RJ = 0.01  # a tabela de p cobre α de 0,01 a 0,10
ALFA_MAXIMO_RJ = 0.10


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
    passos = [f"Shapiro-Wilk ({nome}): W = {num(float(estat), 3)}; p {p_valor(float(p))} → {conc}"]

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
        passos=[f"Anderson-Darling ({nome}): A² = {num(a2, 4)}; p {p_valor(p)} → {conc}"],
    )


# ----------------------------------------------------------------------------- Ryan-Joiner (opção do Minitab)


def estatistica_ryan_joiner(v: np.ndarray) -> float:
    """R_p = Σ(Y_i − Ȳ)·b_i / √(s²(n−1)·Σb_i²), com Y_i os dados ordenados e b_i = Φ⁻¹((i − 0,375)/(n + 0,25)).

    Como s²(n−1) = Σ(Y_i − Ȳ)², R_p é a correlação entre os dados ordenados e os escores normais.
    """
    v = np.sort(np.asarray(v, dtype=float))
    exigir_minimo(v, 3, "Ryan-Joiner")
    exigir_variacao(v, "Ryan-Joiner")
    n = len(v)
    i = np.arange(1, n + 1)
    b = stats.norm.ppf((i - 0.375) / (n + 0.25))
    d = v - v.mean()
    return float(np.sum(d * b) / np.sqrt(np.sum(d * d) * np.sum(b * b)))


def coeficientes_ryan_joiner(n: int) -> tuple[float, float, float]:
    """Fatores de correção cor10, cor05 e cor01 da apostila (para n ≥ 50 e para n < 50)."""
    r = np.sqrt(n)
    if n >= 50:
        cor10 = 1.0071 - 0.1371 / r - 0.3682 / n + 0.7780 / n**2
        cor05 = 1.0063 - 0.1288 / r - 0.6118 / n + 1.3505 / n**2
        cor01 = 0.9963 - 0.0211 / r - 1.4106 / n + 3.1791 / n**2
    else:
        cor10 = 0.999878 - 0.0009991 / r - 1.26149 / n + 2.22173 / n**1.5
        cor05 = 0.999494 + 0.0177805 / r - 1.77265 / n + 3.55823 / n**1.5
        cor01 = 0.999040 + 0.0362180 / r - 2.52631 / n + 4.36612 / n**1.5
    return float(cor10), float(cor05), float(cor01)


def p_ryan_joiner(rp: float, n: int) -> tuple[float, str]:
    """p pela regra da apostila, por interpolação entre 0,10, 0,05 e 0,01.

    Devolve ``(p, limite)``: ``limite`` é ``'>'`` (p > 0,10) ou ``'<'`` (p < 0,01) quando a tabela só dá limite.
    """
    cor10, cor05, cor01 = coeficientes_ryan_joiner(n)
    if rp > cor10:
        return 0.10, ">"
    if rp > cor05:
        return 0.05 + (rp - cor05) / (cor10 - cor05) * 0.05, ""
    if rp > cor01:
        return 0.01 + (rp - cor01) / (cor05 - cor01) * 0.04, ""
    return 0.01, "<"


def ryan_joiner(v: np.ndarray, *, alpha: float = ALPHA_PADRAO, nome: str = "amostra") -> Normalidade:
    """Teste de normalidade Ryan-Joiner (equivalente ao Shapiro-Wilk, disponível no Minitab). Não usa o atalho do TCL.

    O p vem da tabela da apostila, que cobre α de 0,01 a 0,10; fora dessa faixa o teste não é calculado.
    """
    v = np.asarray(v, dtype=float)
    exigir_minimo(v, N_MINIMO_RJ, "Ryan-Joiner")
    exigir_variacao(v, nome)
    if not ALFA_MINIMO_RJ - 1e-9 <= alpha <= ALFA_MAXIMO_RJ + 1e-9:
        raise ErroDeDados("Ryan-Joiner: a tabela de p da apostila cobre α de 0,01 a 0,10 (confiança de 90% a 99%).")
    n = len(v)
    rp = estatistica_ryan_joiner(v)
    cor10, cor05, cor01 = coeficientes_ryan_joiner(n)
    p, limite = p_ryan_joiner(rp, n)
    if limite == ">":
        rejeita = False
    elif limite == "<":
        rejeita = True
    else:
        rejeita = p <= alpha
    normal = not rejeita
    texto_p = f"p {limite} {num(p, 2)}" if limite else f"p {p_valor(p)}"
    conc = "pode-se assumir normalidade" if normal else "rejeita-se a normalidade"
    avisos = []
    if n < N_CONFIAVEL_RJ:
        avisos.append(
            f"Ryan-Joiner com n = {n} (< {N_CONFIAVEL_RJ}): por simulação, o p tabelado rejeita mais do que α "
            "mesmo quando os dados são normais."
        )
    return Normalidade(
        nome="Ryan-Joiner",
        alpha=alpha,
        estatistica=rp,
        rotulo_estatistica="Rp",
        p=p,
        p_limite=limite,
        n=n,
        normal=normal,
        atende=normal,
        pelo_tcl=False,
        passos=[
            f"Fatores de correção (n = {n}): cor10 = {num(cor10, 4)}; cor05 = {num(cor05, 4)}; cor01 = {num(cor01, 4)}",
            f"Ryan-Joiner ({nome}): Rp = {num(rp, 4)}; {texto_p} → {conc}",
        ],
        avisos=avisos,
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
