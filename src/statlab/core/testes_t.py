"""Testes t (pareado e independente) e os fluxos que escolhem entre paramétrico e não paramétrico.

Hipótese unilateral: só use ``alternativa='maior'`` ou ``'menor'`` se a direção foi definida antes
de olhar os dados. Se a diferença observada for na direção oposta, o p unilateral sai > 0,5 (não significativo).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from statlab.core.dados import amostra, exigir_minimo, exigir_variacao, pares
from statlab.core.descritiva import descrever, detectar_outliers, sem_extremos, texto_outliers
from statlab.core.formatacao import num, p_valor
from statlab.core.nao_parametricos import (
    TesteNaoParametrico,
    mann_whitney,
    validar_alternativa,
    wilcoxon_pareado,
)
from statlab.core.normalidade import shapiro_wilk
from statlab.core.resultados import ALPHA_PADRAO, Resultado
from statlab.core.variancias import teste_f


def _p_t(t: float, gl: float, alternativa: str) -> float:
    validar_alternativa(alternativa)
    if alternativa == "bilateral":
        return float(2 * stats.t.sf(abs(t), gl))
    if alternativa == "maior":
        return float(stats.t.sf(t, gl))
    return float(stats.t.cdf(t, gl))


def _rotulo_alt(alternativa: str) -> str:
    return {"bilateral": "bilateral", "maior": "unilateral: 1º > 2º", "menor": "unilateral: 1º < 2º"}[alternativa]


@dataclass(kw_only=True)
class TesteT(Resultado):
    media_diferenca: float | None = None
    erro_padrao: float | None = None
    alternativa: str = "bilateral"
    variancias_iguais: bool | None = None
    medias: dict[str, float] = field(default_factory=dict)


def t_pareado(
    antes: np.ndarray,
    depois: np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
) -> TesteT:
    """t pareado sobre d = antes − depois. gl = n − 1; IC 95% para a média de d."""
    a = np.asarray(antes, dtype=float)
    b = np.asarray(depois, dtype=float)
    d = a - b
    exigir_minimo(d, 2, "Teste t pareado")
    exigir_variacao(d, "diferenças")
    n = len(d)
    dbar = float(d.mean())
    sd = float(d.std(ddof=1))
    ep = sd / np.sqrt(n)
    t = dbar / ep
    gl = n - 1
    p = _p_t(t, gl, alternativa)
    tc = float(stats.t.ppf(0.975, gl))
    ic = (dbar - tc * ep, dbar + tc * ep)
    passos = [
        f"d̄ = {num(dbar)}; s_d = {num(sd)}; EP = s_d/√n = {num(ep)}",
        f"t = d̄ / EP = {num(t)}; gl = {gl}; p {p_valor(p)} ({_rotulo_alt(alternativa)})",
        f"IC 95% para a diferença média (antes − depois): ({num(ic[0])}; {num(ic[1])})",
    ]
    return TesteT(
        nome="t pareado",
        alpha=alpha,
        estatistica=t,
        rotulo_estatistica="t",
        gl=(float(gl),),
        p=p,
        n=n,
        ic=ic,
        ic_descricao="diferença média (antes − depois)",
        media_diferenca=dbar,
        erro_padrao=ep,
        alternativa=alternativa,
        medias={"antes": float(a.mean()), "depois": float(b.mean())},
        passos=passos,
    )


def t_independente(
    a: np.ndarray,
    b: np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome_a: str = "grupo 1",
    nome_b: str = "grupo 2",
) -> TesteT:
    """t independente: variância combinada se F não rejeita a igualdade; senão Welch.

    IC 95% para μ_a − μ_b.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    var = teste_f(a, b, alpha=alpha)
    na, nb = len(a), len(b)
    va, vb = float(a.var(ddof=1)), float(b.var(ddof=1))
    ma, mb = float(a.mean()), float(b.mean())
    diff = ma - mb

    if var.iguais:
        gl = float(na + nb - 2)
        sp = np.sqrt(((na - 1) * va + (nb - 1) * vb) / gl)
        ep = float(sp * np.sqrt(1 / na + 1 / nb))
        nome = "t independente (variâncias iguais)"
        extra = [f"s_p = {num(sp, 3)}; EP = s_p·√(1/n1 + 1/n2) = {num(ep, 3)}"]
    else:
        ep = float(np.sqrt(va / na + vb / nb))
        gl = float((va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)))
        nome = "t de Welch (variâncias diferentes)"
        extra = [f"EP = √(s²₁/n₁ + s²₂/n₂) = {num(ep, 3)}; gl (Welch-Satterthwaite) = {num(gl, 1)}"]

    t = diff / ep
    p = _p_t(t, gl, alternativa)
    tc = float(stats.t.ppf(0.975, gl))
    ic = (diff - tc * ep, diff + tc * ep)
    passos = (
        list(var.passos)
        + extra
        + [
            f"t = {num(t, 3)}; gl = {num(gl, 0 if var.iguais else 1)}; p {p_valor(p)} ({_rotulo_alt(alternativa)})",
            f"IC 95% para μ({nome_a}) − μ({nome_b}): ({num(ic[0])}; {num(ic[1])})",
        ]
    )
    return TesteT(
        nome=nome,
        alpha=alpha,
        estatistica=float(t),
        rotulo_estatistica="t",
        gl=(gl,),
        p=p,
        n=na + nb,
        ic=ic,
        ic_descricao=f"μ({nome_a}) − μ({nome_b})",
        media_diferenca=diff,
        erro_padrao=ep,
        alternativa=alternativa,
        variancias_iguais=var.iguais,
        medias={nome_a: ma, nome_b: mb},
        prerequisitos=[f"Variâncias: {var.passos[0]}"],
        passos=passos,
    )


# ----------------------------------------------------------------------------- fluxos de decisão


def _decidir_pareado(a: np.ndarray, b: np.ndarray, alpha: float, alternativa: str) -> tuple[Resultado, bool]:
    """Escolhe t pareado (diferenças normais ou n ≥ 30) ou Wilcoxon. Devolve (resultado, normal_ok)."""
    d = a - b
    norm = shapiro_wilk(d, alpha=alpha, tcl=True, nome="diferenças")
    if norm.atende:
        return t_pareado(a, b, alpha=alpha, alternativa=alternativa), True
    return wilcoxon_pareado(a, b, alpha=alpha, alternativa=alternativa), False


def analisar_antes_depois(
    antes: list[object] | np.ndarray,
    depois: list[object] | np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
) -> Resultado:
    """Análise completa de medidas pareadas: outliers, normalidade das diferenças, teste escolhido.

    Extremos saem (aviso com n antes/depois); suaves são testados com e sem.
    """
    a, b, descartados = pares(antes, depois, "antes", "depois")
    avisos: list[str] = []
    prereq: list[str] = []
    if descartados:
        avisos.append(f"{descartados} par(es) com dado faltante foram descartados.")
    exigir_minimo(a, 2, "Antes × depois")

    d = a - b
    out = detectar_outliers(d)
    prereq.append(texto_outliers("diferenças d", d, out))
    if out.tem_extremo:
        n_antes = len(a)
        keep = ~out.extremo
        a, b = a[keep], b[keep]
        n_excl = int(out.extremo.sum())
        avisos.append(f"{n_excl} par(es) com outlier extremo excluído(s): análise com n = {len(a)} (antes: {n_antes}).")
        exigir_minimo(a, 2, "Antes × depois")
        d = a - b
        out = detectar_outliers(d)

    res, normal_ok = _decidir_pareado(a, b, alpha, alternativa)
    norm = shapiro_wilk(d, alpha=alpha, tcl=True, nome="diferenças")
    prereq.append(norm.passos[0])
    prereq.append(
        "Normalidade das diferenças: " + ("atendida → t pareado." if normal_ok else "não atendida (n < 30) → Wilcoxon.")
    )
    res.passos = [_linha_descritiva("antes", a), _linha_descritiva("depois", b), *res.passos]

    if out.tem_suave:
        m = ~out.suave
        if int(m.sum()) >= 2:
            sub, _ = _decidir_pareado(a[m], b[m], alpha, alternativa)
            mudou = sub.significativo != res.significativo
            res.avisos.append(
                f"Sem o(s) outlier(s) suave(s) (n = {int(m.sum())}): {sub.nome}, p {p_valor(sub.p)} → "
                + (
                    "a conclusão MUDA. Se for erro de medição, vale a análise sem ele; senão relate as duas."
                    if mudou
                    else "a conclusão se mantém."
                )
            )
        else:
            res.avisos.append("Poucos pares restam sem o outlier suave; a análise sem ele não foi feita.")

    res.prerequisitos = prereq + res.prerequisitos
    res.avisos = avisos + res.avisos
    return res


def analisar_dois_grupos(
    grupo_a: list[object] | np.ndarray,
    grupo_b: list[object] | np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome_a: str = "Grupo 1",
    nome_b: str = "Grupo 2",
) -> Resultado:
    """Compara dois grupos independentes: t (normais ou n ≥ 30, com teste F) ou Mann-Whitney."""
    a, fa = amostra(grupo_a, nome_a)
    b, fb = amostra(grupo_b, nome_b)
    avisos: list[str] = []
    prereq: list[str] = []
    if fa or fb:
        avisos.append(f"Faltantes descartados: {nome_a} = {fa}; {nome_b} = {fb}.")
    exigir_minimo(a, 2, nome_a)
    exigir_minimo(b, 2, nome_b)

    desc_txt = []
    outs = {}
    for nome, v in ((nome_a, a), (nome_b, b)):
        out = detectar_outliers(v)
        outs[nome] = out
        prereq.append(texto_outliers(nome, v, out))
        desc_txt.append(_linha_descritiva(nome, v))
    if outs[nome_a].tem_extremo or outs[nome_b].tem_extremo:
        n_antes = (len(a), len(b))
        a = sem_extremos(a, outs[nome_a])
        b = sem_extremos(b, outs[nome_b])
        avisos.append(
            f"Outliers extremos excluídos: {nome_a} n = {len(a)} (antes: {n_antes[0]}); "
            f"{nome_b} n = {len(b)} (antes: {n_antes[1]})."
        )
        exigir_minimo(a, 2, nome_a)
        exigir_minimo(b, 2, nome_b)

    res, normal_ok = _decidir_grupos(a, b, nome_a, nome_b, alpha, alternativa)
    prereq.append(
        "Normalidade e n ≥ 30: "
        + ("atendidas → teste t." if normal_ok else "não atendidas em algum grupo → Mann-Whitney.")
    )
    res.passos = desc_txt + res.passos

    # outliers suaves recalculados sobre a amostra já sem extremos (mesma regra das demais análises)
    suave_a = detectar_outliers(a).suave
    suave_b = detectar_outliers(b).suave
    if suave_a.any() or suave_b.any():
        a2, b2 = a[~suave_a], b[~suave_b]
        if len(a2) >= 2 and len(b2) >= 2:
            sub, _ = _decidir_grupos(a2, b2, nome_a, nome_b, alpha, alternativa)
            mudou = sub.significativo != res.significativo
            res.avisos.append(
                f"Sem os outliers suaves ({nome_a} n = {len(a2)}; {nome_b} n = {len(b2)}): {sub.nome}, p "
                f"{p_valor(sub.p)} → "
                + ("a conclusão MUDA; relate as duas análises." if mudou else "a conclusão se mantém.")
            )

    res.prerequisitos = prereq + res.prerequisitos
    res.avisos = avisos + res.avisos
    return res


def _linha_descritiva(nome: str, v: np.ndarray) -> str:
    d = descrever(v)
    return (
        f"{nome}: n = {d.n}; média = {num(d.media)}; mediana = {num(d.mediana)}; "
        f"dp = {num(d.dp)}; variância = {num(d.variancia)}"
    )


def _decidir_grupos(
    a: np.ndarray,
    b: np.ndarray,
    nome_a: str,
    nome_b: str,
    alpha: float,
    alternativa: str,
) -> tuple[Resultado, bool]:
    na = shapiro_wilk(a, alpha=alpha, tcl=True, nome=nome_a)
    nb = shapiro_wilk(b, alpha=alpha, tcl=True, nome=nome_b)
    if na.atende and nb.atende:
        return t_independente(a, b, alpha=alpha, alternativa=alternativa, nome_a=nome_a, nome_b=nome_b), True
    mw: TesteNaoParametrico = mann_whitney(a, b, alpha=alpha, alternativa=alternativa, nome_a=nome_a, nome_b=nome_b)
    mw.passos = na.passos + nb.passos + mw.passos
    return mw, False
