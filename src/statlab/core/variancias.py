"""Igualdade de variâncias: teste F (ratio of variances), Levene (centrado na mediana) e Bartlett."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados, amostra, exigir_minimo, exigir_variacao
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
    """Teste F bilateral: F = s²maior / s²menor, gl = (n_maior − 1; n_menor − 1).

    Reporta o p (e o Levene como conferência). O campo ``iguais`` é a leitura p > α — informação para
    quem chama, não instrução sobre qual teste t usar.
    """
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

    passos = [
        f"s² = {num(max(va, vb), 2)} e {num(min(va, vb), 2)}",
        f"F = {num(max(va, vb), 2)} / {num(min(va, vb), 2)} = {num(f_stat, 3)}; "
        f"gl = ({gl_num}; {gl_den}); p {p_valor(p)}",
        f"Conferência — Levene (mediana): p {p_valor(p_lev)}",
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


# ----------------------------------------------------------------------------- k grupos (Teste de variâncias iguais)


@dataclass(kw_only=True)
class IgualdadeVariancias(Resultado):
    """Comparação das variâncias de 2 ou mais grupos.

    ``metodo``: o teste que o usuário pediu — "Bartlett" ou "Levene". ``razao``: maior/menor variância
    (o critério ≤ 9 da ANOVA na disciplina é reportado como nota, não aplicado).
    """

    metodo: str = ""
    desvios: dict[str, float] = field(default_factory=dict)
    razao: float = 0.0
    p_f: float | None = None
    p_bartlett: float | None = None
    p_levene: float | None = None

    @property
    def iguais(self) -> bool:
        return not self.significativo


def _grupos_limpos(grupos: Mapping[str, object], minimo: int) -> dict[str, np.ndarray]:
    """Converte os grupos em arrays, descartando faltantes. Não remove outliers."""
    if len(grupos) < minimo:
        raise ErroDeDados(f"Escolha pelo menos {minimo} grupos.")
    limpos: dict[str, np.ndarray] = {}
    for nome, valores in grupos.items():
        v, _ = amostra(valores, nome)
        exigir_minimo(v, 2, nome)
        exigir_variacao(v, nome)
        limpos[nome] = v
    return limpos


def _igualdade(
    grupos: Mapping[str, object],
    *,
    metodo: str,
    alpha: float,
) -> IgualdadeVariancias:
    limpos = _grupos_limpos(grupos, 2)
    dados = list(limpos.values())
    k = len(dados)
    n = sum(len(d) for d in dados)
    desvios = {nome: float(v.std(ddof=1)) for nome, v in limpos.items()}
    razao = razao_maior_menor(dados)

    if metodo == "Bartlett":
        res = stats.bartlett(*dados)
        estat, rotulo, gl = float(res.statistic), "B (χ²)", (float(k - 1),)
        p_bart: float | None = float(res.pvalue)
        p_lev: float | None = None
        p = float(res.pvalue)
        nota = "O Bartlett supõe grupos normais; sem normalidade, prefira o Levene."
    else:
        res = stats.levene(*dados, center="median")
        estat, rotulo, gl = float(res.statistic), "W (Levene)", (float(k - 1), float(n - k))
        p_bart = None
        p_lev = float(res.pvalue)
        p = float(res.pvalue)
        nota = "Levene centrado na mediana (Brown-Forsythe), robusto à falta de normalidade."

    return IgualdadeVariancias(
        nome=f"Igualdade de variâncias ({metodo})",
        alpha=alpha,
        estatistica=estat,
        rotulo_estatistica=rotulo,
        gl=gl,
        p=p,
        n=n,
        metodo=metodo,
        desvios=desvios,
        razao=razao,
        p_bartlett=p_bart,
        p_levene=p_lev,
        passos=[
            "Desvios padrão: " + "; ".join(f"{nome} = {num(dp)}" for nome, dp in desvios.items()),
            f"Razão maior/menor variância = {num(razao)} "
            f"(nota: a disciplina aceita até {RAZAO_MAXIMA_ANOVA:g}× na ANOVA)",
            f"{metodo}: {rotulo} = {num(estat, 3)}; p {p_valor(p)}",
        ],
        avisos=[
            nota,
            "Bartlett e Levene não estão na apostila revisada: nela, dois grupos usam o teste F e a ANOVA "
            "usa a razão maior/menor variância ≤ 9.",
        ],
    )


def bartlett(grupos: Mapping[str, object], *, alpha: float = ALPHA_PADRAO) -> IgualdadeVariancias:
    """Teste de Bartlett para igualdade de variâncias de 2 ou mais grupos (supõe normalidade)."""
    return _igualdade(grupos, metodo="Bartlett", alpha=alpha)


def levene(grupos: Mapping[str, object], *, alpha: float = ALPHA_PADRAO) -> IgualdadeVariancias:
    """Teste de Levene centrado na mediana (o "Levene" do Minitab), robusto à falta de normalidade."""
    return _igualdade(grupos, metodo="Levene", alpha=alpha)
