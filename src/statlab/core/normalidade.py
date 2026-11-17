"""Teste de normalidade (Shapiro-Wilk) e a regra do Teorema Central do Limite da disciplina."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from statlab.core.dados import exigir_minimo, exigir_variacao
from statlab.core.formatacao import p_valor
from statlab.core.resultados import ALPHA_PADRAO, Resultado

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
