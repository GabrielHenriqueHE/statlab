"""Reta de mínimos quadrados no formato da apostila (y = a·x + b).

A regressão completa (EP, t, p dos coeficientes, R², R²(aj), R²(pred), ANOVA, resíduos e predição com
IC e IP) é a de ``regressao_multipla`` com um preditor. Aqui ficam só a fórmula fechada que a
apostila usa e a previsão pontual — sem condicionar nada à significância da correlação.
"""

from __future__ import annotations

import numpy as np

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num


def coeficientes(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """a = (nΣxy − ΣxΣy)/(nΣx² − (Σx)²); b = ȳ − a·x̄."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    sx, sy = x.sum(), y.sum()
    sxy = (x * y).sum()
    sx2 = (x * x).sum()
    den = n * sx2 - sx**2
    if den == 0:
        raise ErroDeDados("A variável x não varia; a reta de regressão não existe.")
    a = (n * sxy - sx * sy) / den
    b = sy / n - a * sx / n
    return float(a), float(b)


def equacao(a: float, b: float, nome_x: str = "x", nome_y: str = "y") -> str:
    """Equação da reta no formato "y = a·x + b", com o sinal de b já ajustado."""
    sinal = "+" if b >= 0 else "−"
    return f"{nome_y} = {num(a, 4)}·{nome_x} {sinal} {num(abs(b), 4)}"


def prever(
    a: float, b: float, x0: float, *, x_min: float | None = None, x_max: float | None = None
) -> tuple[float, str | None]:
    """ŷ = a·x0 + b. Devolve também um aviso se x0 estiver fora da faixa observada."""
    aviso = None
    if x_min is not None and x_max is not None and not (x_min <= x0 <= x_max):
        aviso = (
            f"x = {num(x0, 2)} está fora da faixa observada ({num(x_min, 2)} a {num(x_max, 2)}): "
            "extrapolação, leia com cautela."
        )
    return a * x0 + b, aviso
