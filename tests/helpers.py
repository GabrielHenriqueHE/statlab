"""Utilitários dos testes: fixtures JSON e comparação com a precisão de impressão do PDF."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"


def carregar(nome: str) -> dict[str, Any]:
    return json.loads((FIXTURES / nome).read_text(encoding="utf-8"))


def pdf() -> dict[str, Any]:
    """Dados dos exemplos resolvidos do PDF revisado (planilhas da disciplina)."""
    return carregar("pdf_exemplos.json")


def gabarito() -> dict[str, Any]:
    """Dados do gabarito 2026 (dados_2026.xlsx) e o enunciado bruto para os casos com extremos."""
    return carregar("gabarito_2026.json")


def aprox(obtido: float, esperado: float, casas: int = 3) -> None:
    """Confere com a precisão de impressão do PDF: tolerância = meio último dígito impresso.

    Ex.: ``aprox(r, 0.975, 3)`` aceita 0,9745 a 0,9755. Isso é mais rigoroso que uma tolerância fixa
    quando o PDF imprime poucas casas (ex.: b = 12,20 não aceita 12,25).
    """
    tol = 0.5 * 10 ** (-casas) + 1e-9
    assert abs(obtido - esperado) <= tol, f"obtido={obtido!r}, esperado={esperado!r} (casas={casas}, tol={tol:g})"


def p_menor_que(p: float | None, limite: float = 0.001) -> None:
    """O PDF escreve 'p < 0,001'."""
    assert p is not None and p < limite, f"p={p!r} deveria ser < {limite}"
