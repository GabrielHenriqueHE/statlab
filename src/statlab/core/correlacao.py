"""Correlação linear (Pearson) e por postos (Spearman).

O método é escolha de quem chama. A função pareia x e y (descartando pares com faltantes e
reportando quantos), calcula r, p, os valores críticos da tabela A.6, a força e r², e reporta a
normalidade de x e de y como diagnóstico — sem trocar de método e sem excluir outliers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados, exigir_minimo, exigir_variacao, pares
from statlab.core.descritiva import detectar_outliers, verificacao_outliers
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import shapiro_wilk, verificacao_normalidade
from statlab.core.resultados import ALPHA_PADRAO, Resultado

N_MINIMO_PARES = 3


def pearson(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """r pela fórmula n·Σxy − Σx·Σy / √[(nΣx² − (Σx)²)(nΣy² − (Σy)²)] e p pelo t com n − 2 gl."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    sx, sy = x.sum(), y.sum()
    sxy = (x * y).sum()
    sx2, sy2 = (x * x).sum(), (y * y).sum()
    den = np.sqrt((n * sx2 - sx**2) * (n * sy2 - sy**2))
    if den == 0:
        raise ErroDeDados("Não é possível calcular a correlação: uma das variáveis não varia.")
    r = float(np.clip((n * sxy - sx * sy) / den, -1.0, 1.0))
    if abs(r) >= 1.0:
        return r, 0.0
    t = r * np.sqrt((n - 2) / (1 - r * r))
    return r, float(2 * stats.t.sf(abs(t), n - 2))


def spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Correlação de postos e p (teste bilateral)."""
    rs, p = stats.spearmanr(x, y)
    return float(rs), float(p)


def r_critico(n: int, alpha: float = ALPHA_PADRAO) -> float:
    """Valor crítico de |r| (bilateral), igual à tabela A.6: r = t / √(t² + n − 2), gl = n − 2.

    Para n = 4 e α = 0,01 dá 0,990 (o livro traz 0,999, erro de impressão).
    """
    if n < 3:
        raise ErroDeDados("O valor crítico de r exige n ≥ 3.")
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    return float(t / np.sqrt(t * t + n - 2))


def forca(r: float) -> str:
    """Classificação de |r| pela tabela 3 da apostila. Só use se a correlação for significativa."""
    a = abs(r)
    if a < 0.2:
        return "bem fraca"
    if a < 0.4:
        return "fraca"
    if a < 0.7:
        return "moderada"
    if a < 0.9:
        return "forte"
    return "muito forte"


@dataclass(kw_only=True)
class Correlacao(Resultado):
    nome_x: str = "x"
    nome_y: str = "y"
    metodo: str = ""  # "Pearson" ou "Spearman" (o que foi pedido)
    r: float = 0.0
    r_s: float = 0.0
    p_pearson: float = 1.0
    p_spearman: float = 1.0
    r2: float = 0.0  # r² de Pearson: % da variação de y explicada por x (interpretar se normal)
    r_critico_5: float = 0.0
    r_critico_1: float = 0.0
    forca: str | None = None  # classificação de |r| (interpretar só se significativo)
    normal_x: bool = False
    normal_y: bool = False
    n_extremos_excluidos: int = 0
    r_sem_suave: float | None = None
    p_sem_suave: float | None = None
    n_sem_suave: int | None = None
    conclusao_muda: bool | None = None
    x_usado: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    y_usado: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))


def correlacao(
    x: list[object] | np.ndarray,
    y: list[object] | np.ndarray,
    *,
    metodo: str = "Pearson",
    alpha: float = ALPHA_PADRAO,
    nome_x: str = "x",
    nome_y: str = "y",
) -> Correlacao:
    """Correlação entre x e y pelo método pedido ("Pearson" ou "Spearman").

    Usa apenas os pares completos (reportando quantos foram descartados). A normalidade de x e de y
    entra como diagnóstico: aqui não vale o atalho do TCL, mas a leitura é do usuário.
    """
    if metodo not in ("Pearson", "Spearman"):
        raise ErroDeDados(f"Método de correlação desconhecido: {metodo!r}. Use 'Pearson' ou 'Spearman'.")
    xs, ys, descartados = pares(x, y, nome_x, nome_y)
    exigir_minimo(xs, N_MINIMO_PARES, "pares (x, y)")
    exigir_variacao(xs, nome_x)
    exigir_variacao(ys, nome_y)
    n = len(xs)

    r_p, p_p = pearson(xs, ys)
    r_s, p_s = spearman(xs, ys)
    r_dec, p_dec = (r_p, p_p) if metodo == "Pearson" else (r_s, p_s)
    rotulo = "r" if metodo == "Pearson" else "rₛ"

    nx = shapiro_wilk(xs, alpha=alpha, tcl=False, nome=nome_x)
    ny = shapiro_wilk(ys, alpha=alpha, tcl=False, nome=nome_y)
    out_x, out_y = detectar_outliers(xs), detectar_outliers(ys)

    avisos: list[str] = []
    if descartados:
        avisos.append(f"{descartados} par(es) com dado faltante foram descartados: n = {n}.")
    if p_dec > alpha:
        avisos.append(
            f"A correlação não é significativa (p {p_valor(p_dec)} > α = {num(alpha, 2)}): a classificação "
            "da força e o r² não devem ser interpretados."
        )

    rc5, rc1 = r_critico(n, 0.05), r_critico(n, 0.01)
    passos = [
        f"n = {n} pares",
        f"Pearson: r = {num(r_p, 4)}; p {p_valor(p_p)}",
        f"Spearman: rₛ = {num(r_s, 4)}; p {p_valor(p_s)}",
        f"Valores críticos de |r| (tabela A.6, n = {n}): {num(rc5, 3)} a 5% e {num(rc1, 3)} a 1%",
        f"{metodo}: {rotulo} = {num(r_dec, 4)}; p {p_valor(p_dec)}; "
        f"força de |{rotulo}| = {forca(r_dec)}; {rotulo}² = {num(r_dec * r_dec * 100, 1)}%",
    ]
    return Correlacao(
        nome=f"Correlação de {metodo}",
        alpha=alpha,
        estatistica=r_dec,
        rotulo_estatistica=rotulo,
        gl=(float(n - 2),) if metodo == "Pearson" else None,
        p=p_dec,
        n=n,
        nome_x=nome_x,
        nome_y=nome_y,
        metodo=metodo,
        r=r_p,
        r_s=r_s,
        p_pearson=p_p,
        p_spearman=p_s,
        r2=r_dec * r_dec,
        r_critico_5=rc5,
        r_critico_1=rc1,
        forca=forca(r_dec),
        normal_x=nx.normal,
        normal_y=ny.normal,
        x_usado=xs,
        y_usado=ys,
        verificacoes=[
            verificacao_outliers(nome_x, xs, out_x),
            verificacao_outliers(nome_y, ys, out_y),
            verificacao_normalidade(nx, nome_x),
            verificacao_normalidade(ny, nome_y),
        ],
        passos=passos,
        avisos=avisos,
    )
