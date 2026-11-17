"""Duas proporções: teste z (aproximação normal) e exato de Fisher, como análises independentes.

Qual das duas usar é escolha de quem chama. Os critérios da apostila (n·p·q ≥ 5) e de "muitos
livros" (n·p ≥ 5 e n·q ≥ 5) são calculados e reportados como diagnóstico — eles informam, não
decidem.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy import stats

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.nao_parametricos import validar_alternativa
from statlab.core.resultados import ALPHA_PADRAO, ATENCAO, OK, Resultado, Verificacao


@dataclass(kw_only=True)
class Proporcoes(Resultado):
    nome_1: str = "grupo 1"
    nome_2: str = "grupo 2"
    p1: float = 0.0
    p2: float = 0.0
    p_combinada: float = 0.0
    diferenca: float = 0.0  # p1 − p2
    z: float | None = None  # só no método z
    p_fisher: float | None = None  # só no método exato
    alternativa: str = "bilateral"


def _checar_entrada(x: int, n: int, nome: str) -> None:
    if n < 1:
        raise ErroDeDados(f"{nome}: o total deve ser pelo menos 1.")
    if not (0 <= x <= n):
        raise ErroDeDados(f"{nome}: ocorrências ({x}) devem estar entre 0 e o total ({n}).")


def criterios_amostra_grande(x1: int, n1: int, x2: int, n2: int, nome_1: str, nome_2: str) -> list[Verificacao]:
    """Diagnóstico dos critérios de aproximação normal. Informativo: não troca o método.

    ⚠ quando o critério não é atendido — a leitura (usar o exato de Fisher) é do usuário.
    """
    p1, p2 = x1 / n1, x2 / n2
    pq1, pq2 = n1 * p1 * (1 - p1), n2 * p2 * (1 - p2)
    pq_ok = pq1 >= 5 and pq2 >= 5
    np_nq_ok = min(n1 * p1, n1 * (1 - p1)) >= 5 and min(n2 * p2, n2 * (1 - p2)) >= 5
    return [
        Verificacao(
            nome="n·p·q ≥ 5 (apostila)",
            status=OK if pq_ok else ATENCAO,
            detalhe=f"{nome_1} = {num(pq1)}; {nome_2} = {num(pq2)}",
        ),
        Verificacao(
            nome="n·p ≥ 5 e n·q ≥ 5 (muitos livros)",
            status=OK if np_nq_ok else ATENCAO,
            detalhe=(
                f"{nome_1}: n·p = {num(n1 * p1)}, n·q = {num(n1 * (1 - p1))}; "
                f"{nome_2}: n·p = {num(n2 * p2)}, n·q = {num(n2 * (1 - p2))}"
            ),
        ),
    ]


def _preparar(
    x1: int, n1: int, x2: int, n2: int, nome_1: str, nome_2: str, alternativa: str
) -> tuple[int, int, int, int, float, float, float, str]:
    x1, n1, x2, n2 = int(x1), int(n1), int(x2), int(n2)
    _checar_entrada(x1, n1, nome_1)
    _checar_entrada(x2, n2, nome_2)
    scipy_alt = validar_alternativa(alternativa)
    p1, p2 = x1 / n1, x2 / n2
    pc = (x1 + x2) / (n1 + n2)
    return x1, n1, x2, n2, p1, p2, pc, scipy_alt


def z_duas_proporcoes(
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
    """Teste z de duas proporções, com erro padrão pela proporção combinada (como a apostila)."""
    x1, n1, x2, n2, p1, p2, pc, _ = _preparar(x1, n1, x2, n2, nome_1, nome_2, alternativa)
    ep = (pc * (1 - pc) * (1 / n1 + 1 / n2)) ** 0.5
    if ep == 0.0:
        raise ErroDeDados("A proporção combinada é 0 ou 1 nos dois grupos; o teste z não se aplica.")
    z = (p1 - p2) / ep
    if alternativa == "bilateral":
        p = float(2 * stats.norm.sf(abs(z)))
    elif alternativa == "maior":
        p = float(stats.norm.sf(z))
    else:
        p = float(stats.norm.cdf(z))
    return Proporcoes(
        nome="Teste z de duas proporções",
        alpha=alpha,
        estatistica=float(z),
        rotulo_estatistica="z",
        p=p,
        n=n1 + n2,
        nome_1=nome_1,
        nome_2=nome_2,
        p1=p1,
        p2=p2,
        p_combinada=pc,
        diferenca=p1 - p2,
        z=float(z),
        alternativa=alternativa,
        verificacoes=criterios_amostra_grande(x1, n1, x2, n2, nome_1, nome_2),
        passos=[
            f"p̂1 = {x1}/{n1} = {num(p1, 4)}; p̂2 = {x2}/{n2} = {num(p2, 4)}; p combinada = {num(pc, 4)}",
            f"EP = √(p·q·(1/n1 + 1/n2)) = {num(ep, 4)}; z = (p̂1 − p̂2)/EP = {num(z, 3)}; p {p_valor(p)}",
        ],
    )


def fisher_duas_proporcoes(
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
    """Teste exato de Fisher na tabela 2 × 2 das duas proporções."""
    x1, n1, x2, n2, p1, p2, pc, scipy_alt = _preparar(x1, n1, x2, n2, nome_1, nome_2, alternativa)
    p = float(stats.fisher_exact([[x1, n1 - x1], [x2, n2 - x2]], alternative=scipy_alt).pvalue)
    return Proporcoes(
        nome="Teste exato de Fisher",
        alpha=alpha,
        p=p,
        n=n1 + n2,
        nome_1=nome_1,
        nome_2=nome_2,
        p1=p1,
        p2=p2,
        p_combinada=pc,
        diferenca=p1 - p2,
        p_fisher=p,
        alternativa=alternativa,
        verificacoes=criterios_amostra_grande(x1, n1, x2, n2, nome_1, nome_2),
        passos=[
            f"p̂1 = {x1}/{n1} = {num(p1, 4)}; p̂2 = {x2}/{n2} = {num(p2, 4)}",
            f"Tabela 2 × 2: [[{x1}, {n1 - x1}], [{x2}, {n2 - x2}]]; exato de Fisher: p {p_valor(p)}",
        ],
    )
