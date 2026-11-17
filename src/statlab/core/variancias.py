"""Igualdade de variâncias: teste F (ratio of variances) e Levene (centrado na mediana)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados, exigir_minimo
from statlab.core.formatacao import num, p_valor
from statlab.core.resultados import ALPHA_PADRAO, Resultado

RAZAO_MAXIMA_ANOVA = 9.0  # critério da disciplina: maior variância até 9× a menor


@dataclass(kw_only=True)
class Variancias(Resultado):
    """``iguais``: p do teste F > α. ``p_levene``: conferência (p de Levene centrado na mediana)."""

    razao: float = 0.0
    iguais: bool = False
    p_levene: float | None = None


def razao_maior_menor(grupos: Sequence[np.ndarray]) -> float:
    """Maior variância amostral dividida pela menor."""
    variancias = []
    for g in grupos:
        g = np.asarray(g, dtype=float)
        exigir_minimo(g, 2, "grupo")
        variancias.append(float(g.var(ddof=1)))
    menor = min(variancias)
    if menor == 0.0:
        raise ErroDeDados("Um dos grupos tem variância zero; a razão de variâncias não existe.")
    return max(variancias) / menor


def teste_f(a: np.ndarray, b: np.ndarray, *, alpha: float = ALPHA_PADRAO) -> Variancias:
    """Teste F bilateral: F = s²maior / s²menor, gl = (n_maior − 1; n_menor − 1)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    exigir_minimo(a, 2, "grupo 1")
    exigir_minimo(b, 2, "grupo 2")
    va, vb = float(a.var(ddof=1)), float(b.var(ddof=1))
    if min(va, vb) == 0.0:
        raise ErroDeDados("Um dos grupos tem variância zero; o teste F não se aplica.")
    maior_e_a = va >= vb
    f_stat = max(va, vb) / min(va, vb)
    gl_num = (len(a) if maior_e_a else len(b)) - 1
    gl_den = (len(b) if maior_e_a else len(a)) - 1
    p = min(1.0, 2.0 * float(stats.f.sf(f_stat, gl_num, gl_den)))
    iguais = bool(p > alpha)
    p_lev = float(stats.levene(a, b, center="median").pvalue)

    conc = "variâncias iguais → t com variância combinada" if iguais else "variâncias diferentes → t de Welch"
    passos = [
        f"Teste F: F = {num(max(va, vb), 2)} / {num(min(va, vb), 2)} = {num(f_stat, 3)}; "
        f"gl = ({gl_num}; {gl_den}); p {p_valor(p)} (Levene: p {p_valor(p_lev)}) → {conc}"
    ]
    return Variancias(
        nome="Teste F de variâncias",
        alpha=alpha,
        estatistica=f_stat,
        rotulo_estatistica="F",
        gl=(float(gl_num), float(gl_den)),
        p=p,
        n=len(a) + len(b),
        razao=f_stat,
        iguais=iguais,
        p_levene=p_lev,
        passos=passos,
    )


def levene_mediana(*grupos: np.ndarray) -> float:
    """p de Levene centrado na mediana (mais robusto que o F à falta de normalidade)."""
    return float(stats.levene(*[np.asarray(g, dtype=float) for g in grupos], center="median").pvalue)
