"""Testes t: uma amostra pareada e duas amostras independentes.

Cada função roda **o** teste pedido, com as opções recebidas. Nada aqui escolhe entre paramétrico e
não paramétrico nem mexe nos dados: isso é decisão de quem chama.

Hipótese unilateral: só use ``alternativa='maior'`` ou ``'menor'`` se a direção foi definida antes
de olhar os dados. Se a diferença observada for na direção oposta, o p unilateral sai > 0,5 (não significativo).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados, exigir_minimo, exigir_variacao
from statlab.core.descritiva import descrever
from statlab.core.formatacao import num, p_valor
from statlab.core.nao_parametricos import validar_alternativa
from statlab.core.resultados import ALPHA_PADRAO, Resultado


def p_t_student(t: float, gl: float, alternativa: str) -> float:
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
    p = p_t_student(t, gl, alternativa)
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
    variancias_iguais: bool,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome_a: str = "grupo 1",
    nome_b: str = "grupo 2",
    confianca: float = 0.95,
) -> TesteT:
    """t para duas amostras independentes.

    ``variancias_iguais`` é escolha de quem chama (não é decidida aqui): True usa a variância
    combinada (gl = n1 + n2 − 2); False usa Welch (gl de Welch-Satterthwaite). Para avaliar a
    igualdade das variâncias, rode o teste F (``variancias.teste_f``) como análise própria.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    exigir_minimo(a, 2, nome_a)
    exigir_minimo(b, 2, nome_b)
    na, nb = len(a), len(b)
    va, vb = float(a.var(ddof=1)), float(b.var(ddof=1))
    ma, mb = float(a.mean()), float(b.mean())
    diff = ma - mb

    if variancias_iguais:
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

    if ep == 0.0:
        raise ErroDeDados("Os dois grupos não têm variação; o teste t não se aplica.")
    t = diff / ep
    p = p_t_student(t, gl, alternativa)
    tc = float(stats.t.ppf(0.5 + confianca / 2, gl))
    ic = (diff - tc * ep, diff + tc * ep)
    pct_ic = num(confianca * 100, 0)
    passos = [
        _linha_descritiva(nome_a, a),
        _linha_descritiva(nome_b, b),
        *extra,
        f"t = {num(t, 3)}; gl = {num(gl, 0 if variancias_iguais else 1)}; p {p_valor(p)} ({_rotulo_alt(alternativa)})",
        f"IC {pct_ic}% para μ({nome_a}) − μ({nome_b}): ({num(ic[0])}; {num(ic[1])})",
    ]
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
        variancias_iguais=variancias_iguais,
        medias={nome_a: ma, nome_b: mb},
        passos=passos,
    )


def _linha_descritiva(nome: str, v: np.ndarray) -> str:
    d = descrever(v)
    return (
        f"{nome}: n = {d.n}; média = {num(d.media)}; mediana = {num(d.mediana)}; "
        f"dp = {num(d.dp)}; variância = {num(d.variancia)}"
    )
