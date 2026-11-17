"""Comparação de duas proporções: teste z (aproximação normal) ou exato de Fisher.

Pré-requisito do z: n·p·q ≥ 5 em cada grupo (critério da apostila) E n·p ≥ 5 e n·q ≥ 5 (critério
"de muitos livros"). Se qualquer um falhar, usa-se Fisher.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy import stats

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.nao_parametricos import validar_alternativa
from statlab.core.resultados import ALPHA_PADRAO, FALHA, OK, Resultado, Verificacao


@dataclass(kw_only=True)
class Proporcoes(Resultado):
    nome_1: str = "grupo 1"
    nome_2: str = "grupo 2"
    p1: float = 0.0
    p2: float = 0.0
    p_combinada: float = 0.0
    diferenca: float = 0.0  # p1 − p2
    z: float | None = None  # só no método z
    p_fisher: float | None = None  # conferência, quando calculada
    alternativa: str = "bilateral"


def _checar_entrada(x: int, n: int, nome: str) -> None:
    if n < 1:
        raise ErroDeDados(f"{nome}: o total deve ser pelo menos 1.")
    if not (0 <= x <= n):
        raise ErroDeDados(f"{nome}: ocorrências ({x}) devem estar entre 0 e o total ({n}).")


def analisar_proporcoes(
    x1: int,
    n1: int,
    x2: int,
    n2: int,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome_1: str = "grupo 1",
    nome_2: str = "grupo 2",
) -> Proporcoes:
    x1, n1, x2, n2 = int(x1), int(n1), int(x2), int(n2)
    _checar_entrada(x1, n1, nome_1)
    _checar_entrada(x2, n2, nome_2)
    scipy_alt = validar_alternativa(alternativa)

    p1, p2 = x1 / n1, x2 / n2
    pc = (x1 + x2) / (n1 + n2)
    passos = [
        f"p̂1 = {x1}/{n1} = {num(p1, 4)}; p̂2 = {x2}/{n2} = {num(p2, 4)}; p combinada = {num(pc, 4)}",
    ]

    pq_ok = all(n * p * (1 - p) >= 5 for n, p in ((n1, p1), (n2, p2)))
    np_nq_ok = all(min(n * p, n * (1 - p)) >= 5 for n, p in ((n1, p1), (n2, p2)))
    prereq = [
        f"n·p·q (apostila): {nome_1} = {num(n1 * p1 * (1 - p1))}; {nome_2} = {num(n2 * p2 * (1 - p2))} → "
        + ("atendido" if pq_ok else "NÃO atendido"),
        "n·p ≥ 5 e n·q ≥ 5 (critério de muitos livros): " + ("atendido" if np_nq_ok else "NÃO atendido"),
    ]

    verif = [
        Verificacao(nome="n·p·q ≥ 5 (apostila)", status=OK if pq_ok else FALHA, detalhe=prereq[0]),
        Verificacao(
            nome="n·p ≥ 5 e n·q ≥ 5",
            status=OK if np_nq_ok else FALHA,
            detalhe=prereq[1] + ("" if (pq_ok and np_nq_ok) else " → teste exato de Fisher"),
        ),
    ]

    fisher = stats.fisher_exact([[x1, n1 - x1], [x2, n2 - x2]], alternative=scipy_alt)

    if pq_ok and np_nq_ok:
        ep = (pc * (1 - pc) * (1 / n1 + 1 / n2)) ** 0.5
        z = (p1 - p2) / ep
        if alternativa == "bilateral":
            p = float(2 * stats.norm.sf(abs(z)))
        elif alternativa == "maior":
            p = float(stats.norm.sf(z))
        else:
            p = float(stats.norm.cdf(z))
        passos += [
            f"EP = √(p·q·(1/n1 + 1/n2)) = {num(ep, 4)}; z = (p̂1 − p̂2)/EP = {num(z, 3)}; p {p_valor(p)}",
            f"(Conferência — exato de Fisher: p {p_valor(float(fisher.pvalue))})",
        ]
        metodo = "Teste z de duas proporções"
        z_out: float | None = float(z)
        p_fisher = float(fisher.pvalue)
    else:
        p = float(fisher.pvalue)
        passos.append(f"Teste exato de Fisher (pré-requisito não atendido): p {p_valor(p)}")
        metodo = "Teste exato de Fisher"
        z_out = None
        p_fisher = p

    return Proporcoes(
        nome=metodo,
        alpha=alpha,
        estatistica=z_out,
        rotulo_estatistica="z" if z_out is not None else "",
        p=p,
        n=n1 + n2,
        nome_1=nome_1,
        nome_2=nome_2,
        p1=p1,
        p2=p2,
        p_combinada=pc,
        diferenca=p1 - p2,
        z=z_out,
        p_fisher=p_fisher,
        alternativa=alternativa,
        prerequisitos=prereq,
        verificacoes=verif,
        passos=passos,
    )
