"""Regressão linear simples (mínimos quadrados), condicionada à correlação significativa."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from statlab.core.correlacao import analisar_correlacao
from statlab.core.formatacao import num, p_valor
from statlab.core.resultados import ALPHA_PADRAO, Resultado


@dataclass(kw_only=True)
class Regressao(Resultado):
    """``permitida``: False quando a correlação não é significativa e a regressão não foi forçada.

    Quando não permitida, ``a`` e ``b`` ficam None.
    """

    permitida: bool = False
    a: float | None = None
    b: float | None = None
    r2: float | None = None
    x_min: float | None = None
    x_max: float | None = None
    equacao: str = ""
    correlacao_p: float | None = None


def coeficientes(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """a = (nΣxy − ΣxΣy)/(nΣx² − (Σx)²); b = ȳ − a·x̄."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    sx, sy = x.sum(), y.sum()
    sxy = (x * y).sum()
    sx2 = (x * x).sum()
    a = (n * sxy - sx * sy) / (n * sx2 - sx**2)
    b = sy / n - a * sx / n
    return float(a), float(b)


def prever(reg: Regressao, x0: float) -> tuple[float, str | None]:
    """ŷ = a·x0 + b. Devolve também um aviso se x0 estiver fora da faixa observada."""
    if reg.a is None or reg.b is None:
        raise ValueError("Regressão não calculada (correlação não significativa).")
    aviso = None
    if reg.x_min is not None and reg.x_max is not None and not (reg.x_min <= x0 <= reg.x_max):
        aviso = (
            f"x = {num(x0, 2)} está fora da faixa observada ({num(reg.x_min, 2)} a {num(reg.x_max, 2)}): "
            "extrapolação, leia com cautela."
        )
    return reg.a * x0 + reg.b, aviso


def analisar_regressao(
    x: list[object] | np.ndarray,
    y: list[object] | np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    forcar: bool = False,
    nome_x: str = "x",
    nome_y: str = "y",
) -> Regressao:
    """Calcula a reta só se a correlação (Pearson ou Spearman, conforme a normalidade) for significativa.

    Usa os mesmos dados da correlação, já sem os outliers extremos.
    """
    cor = analisar_correlacao(x, y, alpha=alpha, nome_x=nome_x, nome_y=nome_y)
    xs, ys = cor.x_usado, cor.y_usado
    avisos = list(cor.avisos)
    passos = [f"Base: correlação ({cor.metodo}) com n = {cor.n}; p {p_valor(cor.p)}"]
    prereq = [f"Correlação significativa ({cor.metodo}): {'sim' if cor.significativo else 'não'}"]

    permitida = bool(cor.significativo) or forcar
    if not cor.significativo:
        if forcar:
            avisos.append(
                "Correlação NÃO significativa: a reta foi calculada por escolha do usuário, mas não é recomendada."
            )
        else:
            avisos.append("Correlação não significativa: a regressão não deve ser feita. Veja o diagrama de dispersão.")
            return Regressao(
                nome="Regressão linear simples",
                alpha=alpha,
                n=cor.n,
                permitida=False,
                correlacao_p=cor.p,
                prerequisitos=prereq,
                passos=passos,
                avisos=avisos,
            )

    a, b = coeficientes(xs, ys)
    r2 = cor.r2
    passos += [
        f"a = {num(a, 4)} (coeficiente angular): a cada unidade a mais de x, y "
        f"{'aumenta' if a > 0 else 'diminui'} em média {num(abs(a), 3)}.",
        f"b = {num(b, 3)} (intercepto: valor estimado de y quando x = 0; só faz sentido se x = 0 estiver na faixa).",
        f"ŷ = {num(a, 4)}·x {'+' if b >= 0 else '−'} {num(abs(b), 3)}",
    ]
    sinal = "+" if b >= 0 else "−"
    return Regressao(
        nome="Regressão linear simples",
        alpha=alpha,
        n=cor.n,
        permitida=permitida,
        a=a,
        b=b,
        r2=r2,
        x_min=float(xs.min()),
        x_max=float(xs.max()),
        equacao=f"ŷ = {num(a, 4)}·x {sinal} {num(abs(b), 3)}",
        correlacao_p=cor.p,
        prerequisitos=prereq,
        passos=passos,
        avisos=avisos,
    )
