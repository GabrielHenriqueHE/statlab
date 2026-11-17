"""Entrada de dados: conversão de números (inclusive pt-BR), faltantes, pareamento e validações.

Não contém regras estatísticas. Erros de dados viram ``ErroDeDados`` com mensagem em português,
para a UI mostrar em vez de traceback.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence

import numpy as np


class ErroDeDados(ValueError):
    """Dados que impedem o cálculo. A mensagem é para o usuário final."""


_RE_MILHAR = re.compile(r"[-+]?\d{1,3}(\.\d{3})+$")


def numero(valor: object) -> float | None:
    """Converte um valor para float. Texto aceita vírgula decimal e ponto de milhar ('1.100' -> 1100).

    Devolve None para célula vazia/NaN. Levanta ``ErroDeDados`` para texto não numérico ou infinito.
    """
    if valor is None:
        return None
    if isinstance(valor, bool):
        raise ErroDeDados(f"Valor booleano não é um número: {valor!r}.")
    if isinstance(valor, str):
        t = valor.strip()
        if t == "":
            return None
        if "," in t:
            t = t.replace(".", "").replace(",", ".")
        elif _RE_MILHAR.match(t):
            t = t.replace(".", "")
        try:
            x = float(t)
        except ValueError as exc:
            raise ErroDeDados(f"Valor não numérico: {valor!r}.") from exc
    else:
        try:
            x = float(valor)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise ErroDeDados(f"Valor não numérico: {valor!r}.") from exc
    if math.isnan(x):
        return None
    if not math.isfinite(x):
        raise ErroDeDados(f"Valor infinito não é aceito: {valor!r}.")
    return x


def amostra(valores: Iterable[object] | None, nome: str) -> tuple[np.ndarray, int]:
    """Converte uma coluna em array de float, descartando faltantes.

    Devolve ``(valores, faltantes_descartados)``.
    """
    if valores is None:
        raise ErroDeDados(f"{nome}: nenhum dado informado.")
    out: list[float] = []
    faltantes = 0
    for v in valores:
        try:
            x = numero(v)
        except ErroDeDados as exc:
            raise ErroDeDados(f"{nome}: {exc}") from exc
        if x is None:
            faltantes += 1
        else:
            out.append(x)
    return np.asarray(out, dtype=float), faltantes


def pares(
    x: Sequence[object] | None,
    y: Sequence[object] | None,
    nome_x: str = "x",
    nome_y: str = "y",
) -> tuple[np.ndarray, np.ndarray, int]:
    """Pareia duas colunas pela posição e descarta pares com qualquer valor faltante.

    Colunas de tamanhos diferentes são completadas com faltantes. Devolve ``(x, y, descartados)``.
    """
    if x is None or y is None:
        raise ErroDeDados("Informe as duas variáveis.")
    xs = [numero(v) for v in x] if x is not None else []
    ys = [numero(v) for v in y]
    total = max(len(xs), len(ys))
    xs += [None] * (total - len(xs))
    ys += [None] * (total - len(ys))
    px: list[float] = []
    py: list[float] = []
    for a, b in zip(xs, ys, strict=True):
        if a is None or b is None:
            continue
        px.append(a)
        py.append(b)
    descartados = total - len(px)
    return np.asarray(px, dtype=float), np.asarray(py, dtype=float), descartados


def exigir_minimo(v: np.ndarray, minimo: int, nome: str) -> None:
    """Levanta ``ErroDeDados`` se houver menos de ``minimo`` observações."""
    if len(v) < minimo:
        raise ErroDeDados(f"{nome}: são necessárias pelo menos {minimo} observações (há {len(v)}).")


def exigir_variacao(v: np.ndarray, nome: str) -> None:
    """Levanta ``ErroDeDados`` se todos os valores forem iguais (não há o que testar)."""
    if len(v) > 0 and float(np.ptp(v)) == 0.0:
        raise ErroDeDados(f"{nome}: todos os valores são iguais ({v[0]:g}); não há variação para testar.")


_SEPARADORES = re.compile(r"[;\n\t ]+")


def parse_lista(texto: str) -> list[float | None]:
    """Lê uma lista digitada: separada por ';', espaço, tab ou quebra de linha.

    Itens vazios são ignorados. Lança ``ErroDeDados`` com o item problemático.
    """
    if texto is None:
        return []
    itens = [t for t in _SEPARADORES.split(texto.strip()) if t != ""]
    return [numero(t) for t in itens]
