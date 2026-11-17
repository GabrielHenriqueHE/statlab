"""Testes não paramétricos: Wilcoxon (pareado), Mann-Whitney, Kruskal-Wallis e comparações 2 a 2."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.resultados import ALPHA_PADRAO, ParComparacao, Resultado

ALTERNATIVA_SCIPY = {"bilateral": "two-sided", "maior": "greater", "menor": "less"}


def validar_alternativa(alternativa: str) -> str:
    """'bilateral' (padrão), 'maior' (H1: 1º > 2º) ou 'menor' (H1: 1º < 2º)."""
    if alternativa not in ALTERNATIVA_SCIPY:
        raise ValueError(f"alternativa inválida: {alternativa!r}. Use 'bilateral', 'maior' ou 'menor'.")
    return ALTERNATIVA_SCIPY[alternativa]


@dataclass(kw_only=True)
class TesteNaoParametrico(Resultado):
    medianas: dict[str, float] = field(default_factory=dict)
    alternativa: str = "bilateral"
    comparacoes: list[ParComparacao] = field(default_factory=list)


def wilcoxon_pareado(
    antes: np.ndarray,
    depois: np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
) -> TesteNaoParametrico:
    """Wilcoxon dos postos sinalizados sobre d = antes − depois (zeros descartados, método do scipy)."""
    a = np.asarray(antes, dtype=float)
    b = np.asarray(depois, dtype=float)
    d = a - b
    if not np.any(d != 0):
        raise ErroDeDados("Todas as diferenças são zero; o teste de Wilcoxon não se aplica.")
    w = stats.wilcoxon(a, b, alternative=validar_alternativa(alternativa))
    med_a, med_b, med_d = float(np.median(a)), float(np.median(b)), float(np.median(d))
    passos = [
        f"Mediana antes = {num(med_a)}; mediana depois = {num(med_b)}; mediana das diferenças = {num(med_d)}",
        f"W = {num(float(w.statistic), 1)}; p {p_valor(float(w.pvalue))} ({_rotulo_alt(alternativa)})",
    ]
    return TesteNaoParametrico(
        nome="Wilcoxon (pareado)",
        alpha=alpha,
        estatistica=float(w.statistic),
        rotulo_estatistica="W",
        p=float(w.pvalue),
        n=len(d),
        medianas={"antes": med_a, "depois": med_b, "diferenças": med_d},
        alternativa=alternativa,
        passos=passos,
    )


def mann_whitney(
    a: np.ndarray,
    b: np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome_a: str = "grupo 1",
    nome_b: str = "grupo 2",
) -> TesteNaoParametrico:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mw = stats.mannwhitneyu(a, b, alternative=validar_alternativa(alternativa))
    med_a, med_b = float(np.median(a)), float(np.median(b))
    passos = [
        f"Medianas: {nome_a} = {num(med_a)}; {nome_b} = {num(med_b)}",
        f"U = {num(float(mw.statistic), 1)}; p {p_valor(float(mw.pvalue))} ({_rotulo_alt(alternativa)})",
    ]
    return TesteNaoParametrico(
        nome="Mann-Whitney",
        alpha=alpha,
        estatistica=float(mw.statistic),
        rotulo_estatistica="U",
        p=float(mw.pvalue),
        n=len(a) + len(b),
        medianas={nome_a: med_a, nome_b: med_b},
        alternativa=alternativa,
        passos=passos,
    )


def kruskal_wallis(grupos: Mapping[str, np.ndarray], *, alpha: float = ALPHA_PADRAO) -> TesteNaoParametrico:
    """Kruskal-Wallis (com correção de empates, método do scipy). gl = k − 1."""
    nomes = list(grupos)
    dados = [np.asarray(grupos[k], dtype=float) for k in nomes]
    kw = stats.kruskal(*dados)
    medianas = {k: float(np.median(v)) for k, v in zip(nomes, dados, strict=True)}
    passos = [
        "Medianas: " + "; ".join(f"{k} = {num(m)}" for k, m in medianas.items()),
        f"H = {num(float(kw.statistic), 3)}; gl = {len(nomes) - 1}; p {p_valor(float(kw.pvalue))}",
    ]
    return TesteNaoParametrico(
        nome="Kruskal-Wallis",
        alpha=alpha,
        estatistica=float(kw.statistic),
        rotulo_estatistica="H",
        gl=(float(len(nomes) - 1),),
        p=float(kw.pvalue),
        n=sum(len(v) for v in dados),
        medianas=medianas,
        passos=passos,
    )


def comparacoes_mann_whitney_bonferroni(grupos: Mapping[str, np.ndarray]) -> list[ParComparacao]:
    """Mann-Whitney 2 a 2 com correção de Bonferroni (p × número de comparações, máximo 1).

    Fora da apostila: usado como post hoc de Kruskal-Wallis; a UI deve avisar isso.
    """
    nomes = list(grupos)
    m = len(nomes) * (len(nomes) - 1) // 2
    out: list[ParComparacao] = []
    for i, j in combinations(range(len(nomes)), 2):
        ga, gb = np.asarray(grupos[nomes[i]], float), np.asarray(grupos[nomes[j]], float)
        p_raw = float(stats.mannwhitneyu(ga, gb, alternative="two-sided").pvalue)
        out.append(
            ParComparacao(
                grupo_a=nomes[i],
                grupo_b=nomes[j],
                p=min(1.0, p_raw * m),
                metodo=f"Mann-Whitney com Bonferroni (× {m})",
            )
        )
    return out


def _rotulo_alt(alternativa: str) -> str:
    return {"bilateral": "bilateral", "maior": "unilateral: 1º > 2º", "menor": "unilateral: 1º < 2º"}[alternativa]
