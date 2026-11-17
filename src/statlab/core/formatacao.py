"""Formatação de números no padrão brasileiro (vírgula decimal, ponto de milhar)."""

from __future__ import annotations

import math
from collections.abc import Iterable


def num(x: float, casas: int = 2) -> str:
    """1452.781 -> '1.452,78'. Negativos com sinal '-'. NaN/inf viram '—' (nunca 'nan' na tela)."""
    if x is None or not math.isfinite(x):
        return "—"
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def p_valor(p: float | None) -> str:
    """Texto do p com sinal: '< 0,001' ou '= 0,047'."""
    if p is None or not math.isfinite(p):
        return "= —"
    if p < 0.001:
        return "< 0,001"
    return f"= {num(p, 3)}"


def p_numero(p: float | None) -> str:
    """Só o número do p, sem sinal: '< 0,001' ou '0,047'."""
    if p is None or not math.isfinite(p):
        return "—"
    if p < 0.001:
        return "< 0,001"
    return num(p, 3)


def lista(valores: Iterable[float]) -> str:
    """Lista de valores separada por '; '. Inteiros sem casas decimais."""
    out = []
    for v in valores:
        v = float(v)
        out.append(num(v, 0) if v.is_integer() else num(v, 1))
    return "; ".join(out)


def pct(x: float, casas: int = 1) -> str:
    """Fração já em percentual: 92.1 -> '92,1%'."""
    return f"{num(x, casas)}%"
