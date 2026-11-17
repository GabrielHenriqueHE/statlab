"""Exportação de gráficos: somente HTML interativo (decisão do usuário).

O arquivo traz o plotly.js embutido (sem CDN), então abre offline e não consulta servidores externos.
Para uma imagem, use o botão de câmera do próprio gráfico no navegador (o Plotly baixa um PNG).
"""

from __future__ import annotations

from plotly import graph_objects as go


def html(fig: go.Figure) -> bytes:
    return fig.to_html(include_plotlyjs=True, full_html=True).encode("utf-8")
