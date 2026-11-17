"""Gráficos do statlab (Plotly). Ver ``figuras`` para os tipos e ``exportar`` para HTML."""

from statlab.graficos.exportar import html
from statlab.graficos.figuras import (
    barras,
    boxplot,
    correlograma,
    dispersao,
    histograma,
    intervalos,
    matriz_dispersao,
    pareto,
    probabilidade_normal,
    serie_temporal,
    tukey_intervalos,
    valores_individuais,
)

__all__ = [
    "barras",
    "boxplot",
    "correlograma",
    "dispersao",
    "histograma",
    "html",
    "intervalos",
    "matriz_dispersao",
    "pareto",
    "probabilidade_normal",
    "serie_temporal",
    "tukey_intervalos",
    "valores_individuais",
]
