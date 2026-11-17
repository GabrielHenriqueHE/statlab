"""Gráficos do statlab (Plotly). Ver ``figuras`` para os tipos e ``exportar`` para HTML/PNG."""

from statlab.graficos.exportar import ErroExportacao, html, imagem
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
    valores_individuais,
)

__all__ = [
    "ErroExportacao",
    "barras",
    "boxplot",
    "correlograma",
    "dispersao",
    "histograma",
    "html",
    "imagem",
    "intervalos",
    "matriz_dispersao",
    "pareto",
    "probabilidade_normal",
    "serie_temporal",
    "valores_individuais",
]
