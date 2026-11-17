"""Exportação de gráficos.

HTML interativo sempre funciona (plotly.js embutido, sem CDN). PNG/SVG usam Kaleido, que precisa de um
navegador Chrome instalado; quando não há, ``ErroExportacao`` traz a mensagem para a UI.
"""

from __future__ import annotations

from plotly import graph_objects as go


class ErroExportacao(RuntimeError):
    """Não foi possível gerar o arquivo solicitado neste ambiente."""


def html(fig: go.Figure) -> bytes:
    return fig.to_html(include_plotlyjs=True, full_html=True).encode("utf-8")


def imagem(fig: go.Figure, formato: str = "png", *, escala: float = 2.0) -> bytes:
    if formato not in {"png", "svg"}:
        raise ErroExportacao(f"Formato não suportado: {formato!r}.")
    try:
        return fig.to_image(format=formato, scale=escala if formato == "png" else 1)
    except Exception as exc:
        raise ErroExportacao(
            "Exportação de imagem indisponível neste ambiente (requer Kaleido v1 e um navegador Chrome). "
            "Use a exportação HTML, ou instale o Chrome para habilitar PNG/SVG."
        ) from exc
