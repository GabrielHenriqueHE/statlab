"""Gráficos do statlab (Plotly). Ver ``figuras`` para os tipos e ``exportar`` para HTML."""

from statlab.graficos.exportar import html
from statlab.graficos.figuras import (
    barras,
    boxplot,
    correlograma,
    dispersao,
    efeitos_principais,
    histograma,
    interacao,
    intervalos,
    matriz_dispersao,
    pareto,
    probabilidade_normal,
    residuos_quatro,
    serie_temporal,
    tukey_intervalos,
    valores_individuais,
)

__all__ = [
    "barras",
    "boxplot",
    "correlograma",
    "dispersao",
    "efeitos_principais",
    "histograma",
    "html",
    "interacao",
    "intervalos",
    "matriz_dispersao",
    "pareto",
    "probabilidade_normal",
    "residuos_quatro",
    "serie_temporal",
    "tukey_intervalos",
    "valores_individuais",
]
