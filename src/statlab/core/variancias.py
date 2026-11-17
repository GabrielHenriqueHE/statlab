"""Igualdade de variâncias: teste F (ratio of variances), Levene (centrado na mediana) e Bartlett."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados, amostra, exigir_minimo, exigir_variacao
from statlab.core.descritiva import detectar_outliers, sem_extremos, texto_outliers, verificacao_outliers
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import shapiro_wilk, verificacao_normalidade
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


# ----------------------------------------------------------------------------- k grupos (Teste de variâncias iguais)


@dataclass(kw_only=True)
class IgualdadeVariancias(Resultado):
    """Comparação das variâncias de 2 ou mais grupos.

    ``metodo``: o teste que decidiu — F (2 grupos normais), Bartlett (3+ grupos normais) ou Levene (algum
    grupo não normal). Os outros p ficam como conferência. ``razao``: maior/menor variância (critério ≤ 9
    da ANOVA na disciplina).
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


def _p_variancias(dados: Sequence[np.ndarray], todos_normais: bool) -> tuple[str, float, float | None, float, float]:
    """(método, p decisivo, p_F ou None, p_Bartlett, p_Levene)."""
    p_bart = float(stats.bartlett(*dados).pvalue)
    p_lev = float(stats.levene(*dados, center="median").pvalue)
    p_f = None
    if len(dados) == 2:
        p_f = teste_f(dados[0], dados[1]).p
    if not todos_normais:
        return "Levene", p_lev, p_f, p_bart, p_lev
    if p_f is not None:
        return "F", p_f, p_f, p_bart, p_lev
    return "Bartlett", p_bart, p_f, p_bart, p_lev


def igualdade_variancias(grupos: Mapping[str, object], *, alpha: float = ALPHA_PADRAO) -> IgualdadeVariancias:
    """Teste de igualdade de variâncias entre grupos, como o "Teste de variâncias iguais" do Minitab.

    Grupos normais (Shapiro-Wilk, sem o atalho do TCL): F (2 grupos) ou Bartlett (3 ou mais). Algum grupo não
    normal: Levene centrado na mediana (Brown-Forsythe, o "Levene" do Minitab), que é robusto à não
    normalidade. Outliers: extremos saem; suaves, análise com e sem.
    """
    if len(grupos) < 2:
        raise ErroDeDados("Escolha pelo menos 2 grupos.")
    avisos: list[str] = []
    prereq: list[str] = []
    verif = []
    limpos: dict[str, np.ndarray] = {}
    suaves: dict[str, np.ndarray] = {}
    for nome, valores in grupos.items():
        v, faltantes = amostra(valores, nome)  # type: ignore[arg-type]
        if faltantes:
            avisos.append(f"{nome}: {faltantes} valor(es) faltante(s) descartado(s).")
        exigir_minimo(v, 3, nome)
        exigir_variacao(v, nome)
        out = detectar_outliers(v)
        prereq.append(texto_outliers(nome, v, out))
        verif.append(verificacao_outliers(nome, v, out))
        if out.tem_extremo:
            n_antes = len(v)
            v = sem_extremos(v, out)
            avisos.append(f"{nome}: outlier extremo excluído: n = {len(v)} (antes: {n_antes}).")
            exigir_minimo(v, 3, nome)
            exigir_variacao(v, nome)
        limpos[nome] = v
        suaves[nome] = detectar_outliers(v).suave

    todos_normais = True
    for nome, v in limpos.items():
        norm = shapiro_wilk(v, alpha=alpha, tcl=False, nome=nome)
        prereq.append(norm.passos[0])
        verif.append(verificacao_normalidade(norm, nome, "usa-se o Levene (robusto à falta de normalidade)"))
        todos_normais = todos_normais and norm.normal

    nomes = list(limpos)
    dados = [limpos[k] for k in nomes]
    metodo, p, p_f, p_bart, p_lev = _p_variancias(dados, todos_normais)
    desvios = {k: float(limpos[k].std(ddof=1)) for k in nomes}
    razao = razao_maior_menor(dados)
    estat, rotulo, gl = _estatistica(metodo, dados)

    if any(m.any() for m in suaves.values()):
        sem = {k: limpos[k][~suaves[k]] for k in nomes}
        if all(len(x) >= 3 and float(np.ptp(x)) > 0 for x in sem.values()):
            _, p_sem, *_ = _p_variancias(list(sem.values()), todos_normais)
            mudou = (p_sem <= alpha) != (p <= alpha)
            avisos.append(
                f"Sem os outliers suaves: {metodo} p {p_valor(p_sem)} → "
                + ("a conclusão MUDA; relate as duas análises." if mudou else "a conclusão se mantém.")
            )
        else:
            avisos.append(
                "Sem os outliers suaves, algum grupo fica com menos de 3 valores ou sem variação; "
                "a análise sem eles não foi feita."
            )

    passos = [
        "Desvios padrão: " + "; ".join(f"{k} = {num(d, 4)}" for k, d in desvios.items()),
        f"Razão maior/menor variância = {num(razao, 2)} "
        + (
            "(≤ 9: atende ao critério da ANOVA na disciplina)"
            if razao <= RAZAO_MAXIMA_ANOVA
            else "(> 9: a ANOVA não deve ser usada; vai para Kruskal-Wallis)"
        ),
    ]
    if p_f is not None:
        passos.append(f"Teste F (2 grupos, exige normalidade): p {p_valor(p_f)}")
    passos += [
        f"Bartlett (exige normalidade): p {p_valor(p_bart)}",
        f"Levene, centrado na mediana (robusto): p {p_valor(p_lev)}",
        f"Decide: {metodo} ({'grupos normais' if todos_normais else 'algum grupo não normal'}) → "
        + ("variâncias diferentes" if p <= alpha else "sem evidência de variâncias diferentes"),
    ]
    if metodo != "F":
        avisos.append(
            "Bartlett e Levene não estão na apostila revisada: nela, dois grupos usam o teste F e a ANOVA usa a "
            "razão maior/menor variância ≤ 9."
        )
    return IgualdadeVariancias(
        nome=f"Igualdade de variâncias ({metodo})",
        alpha=alpha,
        estatistica=estat,
        rotulo_estatistica=rotulo,
        gl=gl,
        p=p,
        n=sum(len(v) for v in dados),
        metodo=metodo,
        desvios=desvios,
        razao=razao,
        p_f=p_f,
        p_bartlett=p_bart,
        p_levene=p_lev,
        prerequisitos=prereq,
        verificacoes=verif,
        passos=passos,
        avisos=avisos,
    )


def _estatistica(metodo: str, dados: Sequence[np.ndarray]) -> tuple[float, str, tuple[float, ...]]:
    k = len(dados)
    n = sum(len(d) for d in dados)
    if metodo == "F":
        f = teste_f(dados[0], dados[1])
        return float(f.estatistica), "F", f.gl  # type: ignore[arg-type,return-value]
    if metodo == "Bartlett":
        return float(stats.bartlett(*dados).statistic), "B (χ²)", (float(k - 1),)
    return float(stats.levene(*dados, center="median").statistic), "W (Levene)", (float(k - 1), float(n - k))
