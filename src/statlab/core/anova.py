"""ANOVA de 1 fator, Tukey HSD, ANOVA de Welch (conferência) e a escolha entre ANOVA e Kruskal-Wallis.

Regra da disciplina: ANOVA se cada grupo for normal (ou n ≥ 30) E a razão maior/menor variância ≤ 9.
Caso contrário, Kruskal-Wallis. Significativo ⇒ post hoc (Tukey na ANOVA; Mann-Whitney com Bonferroni no KW).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np
from scipy import stats
from statsmodels.stats.oneway import anova_oneway

from statlab.core.dados import ErroDeDados, amostra, exigir_minimo
from statlab.core.formatacao import num, p_valor
from statlab.core.resultados import ALPHA_PADRAO, ParComparacao, Resultado


@dataclass(kw_only=True)
class Anova(Resultado):
    """Resultado da comparação de k grupos.

    ``modelo`` diz qual teste decidiu: "ANOVA (1 fator)" ou "Kruskal-Wallis".
    Campos de ANOVA ficam None quando o modelo é Kruskal-Wallis, e vice-versa (exceto as conferências).
    """

    modelo: str = ""
    sq_entre: float | None = None
    sq_dentro: float | None = None
    sq_total: float | None = None
    gl_entre: int | None = None
    gl_dentro: int | None = None
    qm_entre: float | None = None
    qm_dentro: float | None = None
    r2: float | None = None  # fração 0..1 (SQE/SQT)
    medias: dict[str, float] = field(default_factory=dict)
    medianas: dict[str, float] = field(default_factory=dict)
    comparacoes: list[ParComparacao] = field(default_factory=list)
    metodo_comparacoes: str = ""
    conferencia: str = ""  # linha de conferência (Welch ou ANOVA, conforme o modelo)


def anova_um_fator(grupos: Mapping[str, object], *, alpha: float = ALPHA_PADRAO) -> Anova:
    """Tabela da ANOVA de um fator (SQE, SQD, QM, F, p) e R².

    Não verifica pré-requisitos e não aplica post hoc: para as comparações 2 a 2, chame ``tukey_hsd``.
    Valores faltantes são descartados por grupo, com o n efetivo reportado nos avisos.
    """
    nomes = list(grupos)
    if len(nomes) < 2:
        raise ErroDeDados("A ANOVA precisa de pelo menos 2 grupos.")
    dados: list[np.ndarray] = []
    avisos: list[str] = []
    for nome in nomes:
        v, faltantes = amostra(grupos[nome], nome)
        if faltantes:
            avisos.append(f"{nome}: {faltantes} valor(es) faltante(s) descartado(s); n = {len(v)}.")
        exigir_minimo(v, 2, nome)
        dados.append(v)
    k = len(dados)
    todos = np.concatenate(dados)
    n_total = len(todos)
    gm = float(todos.mean())
    sqe = float(sum(len(g) * (g.mean() - gm) ** 2 for g in dados))
    sqd = float(sum(((g - g.mean()) ** 2).sum() for g in dados))
    sqt = sqe + sqd
    gl_e, gl_d = k - 1, n_total - k
    if gl_d <= 0:
        raise ErroDeDados("Dados insuficientes para a ANOVA (graus de liberdade dentro dos grupos ≤ 0).")
    qme, qmd = sqe / gl_e, sqd / gl_d
    if qmd == 0.0:
        raise ErroDeDados("Não há variação dentro dos grupos; a ANOVA não se aplica.")
    f_stat = qme / qmd
    p = float(stats.f.sf(f_stat, gl_e, gl_d))
    r2 = sqe / sqt if sqt > 0 else 0.0
    medias = {nm: float(g.mean()) for nm, g in zip(nomes, dados, strict=True)}

    passos = [
        "Fonte | gl | SQ | QM | F | p",
        f"Entre grupos | {gl_e} | {num(sqe)} | {num(qme)} | {num(f_stat, 3)} | {p_valor(p)}",
        f"Dentro | {gl_d} | {num(sqd)} | {num(qmd)} | | ",
        f"Total | {n_total - 1} | {num(sqt)} | | | ",
        f"R² = {num(r2 * 100, 1)}%",
    ]
    return Anova(
        nome="ANOVA (1 fator)",
        alpha=alpha,
        modelo="ANOVA (1 fator)",
        estatistica=f_stat,
        rotulo_estatistica="F",
        gl=(float(gl_e), float(gl_d)),
        p=p,
        n=n_total,
        sq_entre=sqe,
        sq_dentro=sqd,
        sq_total=sqt,
        gl_entre=gl_e,
        gl_dentro=gl_d,
        qm_entre=qme,
        qm_dentro=qmd,
        r2=r2,
        medias=medias,
        avisos=avisos,
        passos=passos,
    )


def tukey_hsd(grupos: Mapping[str, np.ndarray], *, confianca: float = 0.95) -> list[ParComparacao]:
    """Tukey HSD para todos os pares. Diferença = média_a − média_b, com IC simultâneo."""
    if len(grupos) < 3:
        raise ErroDeDados("O Tukey compara pares entre 3 ou mais grupos; com 2 grupos, use o teste t.")
    nomes = list(grupos)
    dados = [np.asarray(grupos[k], dtype=float) for k in nomes]
    res = stats.tukey_hsd(*dados)
    ci = res.confidence_interval(confianca)
    out: list[ParComparacao] = []
    for i in range(len(dados)):
        for j in range(i + 1, len(dados)):
            out.append(
                ParComparacao(
                    grupo_a=nomes[i],
                    grupo_b=nomes[j],
                    p=float(res.pvalue[i, j]),
                    metodo="Tukey HSD",
                    diferenca=float(dados[i].mean() - dados[j].mean()),
                    ic=(float(ci.low[i, j]), float(ci.high[i, j])),
                )
            )
    return out


def welch_anova(grupos: Mapping[str, np.ndarray]) -> tuple[float, float]:
    """ANOVA de Welch (não supõe variâncias iguais). Devolve (F, p)."""
    res = anova_oneway(
        [np.asarray(g, dtype=float) for g in grupos.values()],
        use_var="unequal",
        welch_correction=True,
    )
    return float(res.statistic), float(res.pvalue)
