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
from statlab.core.descritiva import detectar_outliers, sem_extremos, texto_outliers
from statlab.core.formatacao import num, p_valor
from statlab.core.nao_parametricos import comparacoes_mann_whitney_bonferroni, kruskal_wallis
from statlab.core.normalidade import shapiro_wilk
from statlab.core.resultados import ALPHA_PADRAO, ParComparacao, Resultado
from statlab.core.variancias import RAZAO_MAXIMA_ANOVA, razao_maior_menor


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


def anova_um_fator(grupos: Mapping[str, np.ndarray], *, alpha: float = ALPHA_PADRAO) -> Anova:
    """Tabela da ANOVA (SQE, SQD, QM, F, p) e R². Não faz pré-requisitos — use ``analisar_grupos``."""
    nomes = list(grupos)
    dados = [np.asarray(grupos[k], dtype=float) for k in nomes]
    k = len(dados)
    if k < 2:
        raise ErroDeDados("A ANOVA precisa de pelo menos 2 grupos.")
    for nome, g in zip(nomes, dados, strict=True):
        exigir_minimo(g, 2, nome)
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
        passos=passos,
    )


def tukey_hsd(grupos: Mapping[str, np.ndarray]) -> list[ParComparacao]:
    """Tukey HSD para todos os pares. Diferença = média_a − média_b, com IC 95%."""
    nomes = list(grupos)
    dados = [np.asarray(grupos[k], dtype=float) for k in nomes]
    res = stats.tukey_hsd(*dados)
    ci = res.confidence_interval(0.95)
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


def analisar_grupos(
    grupos: Mapping[str, list[object] | np.ndarray],
    *,
    alpha: float = ALPHA_PADRAO,
) -> Anova:
    """Compara k ≥ 2 grupos independentes com a regra da disciplina.

    Extremos saem por grupo (com aviso); pré-requisitos e o modelo escolhido vão para os campos do resultado.
    """
    if len(grupos) < 2:
        raise ErroDeDados("Informe pelo menos 2 grupos.")
    prereq: list[str] = []
    avisos: list[str] = []
    limpos: dict[str, np.ndarray] = {}
    for nome, bruto in grupos.items():
        v, faltantes = amostra(bruto, nome)
        if faltantes:
            avisos.append(f"{nome}: {faltantes} faltante(s) descartado(s).")
        exigir_minimo(v, 3, nome)
        out = detectar_outliers(v)
        prereq.append(texto_outliers(nome, v, out))
        if out.tem_extremo:
            n_antes = len(v)
            v = sem_extremos(v, out)
            avisos.append(f"{nome}: outlier extremo excluído; n = {len(v)} (antes: {n_antes}).")
            exigir_minimo(v, 3, nome)
        limpos[nome] = v

    normalidades = {nome: shapiro_wilk(v, alpha=alpha, tcl=True, nome=nome) for nome, v in limpos.items()}
    for nr in normalidades.values():
        prereq.append(nr.passos[0])
    normal_ok = all(nr.atende for nr in normalidades.values())
    razao = razao_maior_menor(list(limpos.values()))
    var_ok = razao <= RAZAO_MAXIMA_ANOVA
    prereq.append(
        f"Variâncias: maior/menor = {num(razao)} → "
        + (f"dentro do critério (≤ {RAZAO_MAXIMA_ANOVA:g}×)." if var_ok else f"acima de {RAZAO_MAXIMA_ANOVA:g}×.")
    )

    if normal_ok and var_ok:
        res = anova_um_fator(limpos, alpha=alpha)
        welch_f, welch_p = welch_anova(limpos)
        res.conferencia = (
            f"Conferência (Welch, sem supor variâncias iguais): F = {num(welch_f, 2)}; p {p_valor(welch_p)}"
        )
        if res.significativo:
            res.comparacoes = tukey_hsd(limpos)
            res.metodo_comparacoes = "Tukey HSD"
        res.passos = ["Modelo: ANOVA (normalidade e razão de variâncias atendidas)", *res.passos]
    else:
        motivo = (
            "normalidade (n < 30 e não normal)" if not normal_ok else f"razão de variâncias > {RAZAO_MAXIMA_ANOVA:g}"
        )
        kw = kruskal_wallis(limpos, alpha=alpha)
        f_conf = stats.f_oneway(*limpos.values())
        res = Anova(
            nome="Kruskal-Wallis",
            alpha=alpha,
            modelo="Kruskal-Wallis",
            estatistica=kw.estatistica,
            rotulo_estatistica="H",
            gl=kw.gl,
            p=kw.p,
            n=kw.n,
            medias={nm: float(v.mean()) for nm, v in limpos.items()},
            medianas=kw.medianas,
            conferencia=(
                f"Conferência (ANOVA): F = {num(float(f_conf.statistic), 2)}; p {p_valor(float(f_conf.pvalue))}"
            ),
            passos=[f"Modelo: Kruskal-Wallis — pré-requisito da ANOVA violado ({motivo})", *kw.passos],
        )
        if res.significativo:
            res.comparacoes = comparacoes_mann_whitney_bonferroni(limpos)
            res.metodo_comparacoes = "Mann-Whitney com Bonferroni"
            avisos.append(
                "Post hoc Mann-Whitney com Bonferroni é fora do conteúdo da apostila; confirme com o professor."
            )

    res.prerequisitos = prereq + res.prerequisitos
    res.avisos = avisos + res.avisos
    res.n = sum(len(v) for v in limpos.values())
    return res
