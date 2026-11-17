"""Saída da sessão: cada item reúne o comando, os diagnósticos, o resultado, as notas, o cálculo e os gráficos.

Exporta Markdown (texto, sem gráficos) e HTML autocontido (gráficos interativos, plotly.js embutido uma vez,
sem CDN). Não importa Streamlit.
"""

from __future__ import annotations

import html
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
from plotly import graph_objects as go

from statlab.core.formatacao import num, p_valor
from statlab.core.resultados import ATENCAO, FALHA, OK, Resultado

ICONES = {OK: "✅", ATENCAO: "⚠️", FALHA: "❌"}


@dataclass
class ItemRelatorio:
    """Um bloco da janela de sessão: o que um comando produziu."""

    titulo: str
    teste: str = ""
    resultado: list[str] = field(default_factory=list)
    verificacoes: list[tuple[str, str, str]] = field(default_factory=list)  # (ícone, nome, detalhe)
    passos: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    tabelas: list[tuple[str, pd.DataFrame]] = field(default_factory=list)
    figuras: list[go.Figure] = field(default_factory=list)
    criado_em: datetime = field(default_factory=datetime.now)


def _tabela_markdown(tab: pd.DataFrame) -> list[str]:
    """Tabela em Markdown sem depender de `tabulate`."""
    colunas = [str(c) for c in tab.columns]
    linhas = ["| " + " | ".join(colunas) + " |", "|" + "|".join(["---"] * len(colunas)) + "|"]
    for _, linha in tab.iterrows():
        linhas.append("| " + " | ".join("" if v is None else str(v) for v in linha) + " |")
    return linhas


def resumo_resultado(res: Resultado) -> list[str]:
    """Linhas com estatística, gl, p, n, IC e decisão (o mesmo que a tela mostra)."""
    linhas = []
    if res.estatistica is not None:
        linhas.append(f"{res.rotulo_estatistica or 'Estatística'} = {num(res.estatistica, 3)}")
    if res.gl:
        linhas.append("gl = " + "; ".join(num(g, 0) if float(g).is_integer() else num(g, 1) for g in res.gl))
    if res.p is not None:
        linhas.append(f"p {p_valor(res.p)}")
    if res.n is not None:
        linhas.append(f"n = {res.n}")
    if res.ic is not None:
        linhas.append(f"IC 95% para {res.ic_descricao}: ({num(res.ic[0])}; {num(res.ic[1])})")
    if res.significativo:
        linhas.append(f"Decisão: significativo com {res.nivel_confianca}% de confiança (α = {num(res.alpha, 2)})")
    elif res.significativo is False:
        linhas.append(f"Decisão: não significativo (α = {num(res.alpha, 2)})")
    return linhas


def item_de(
    res: Resultado,
    *,
    titulo: str,
    tabelas: Sequence[tuple[str, pd.DataFrame]] = (),
    figuras: Sequence[go.Figure] = (),
) -> ItemRelatorio:
    """Bloco de sessão a partir de um ``Resultado`` do núcleo."""
    return ItemRelatorio(
        titulo=titulo,
        teste=res.nome,
        tabelas=list(tabelas),
        resultado=resumo_resultado(res),
        verificacoes=[(ICONES.get(v.status, "•"), v.nome, v.detalhe) for v in res.verificacoes],
        passos=list(res.passos),
        avisos=list(res.avisos),
        figuras=list(figuras),
    )


def para_markdown(itens: Sequence[ItemRelatorio], titulo: str = "Relatório — statlab") -> str:
    partes = [f"# {titulo}", "", f"Gerado em {datetime.now():%d/%m/%Y %H:%M}. {len(itens)} análise(s).", ""]
    for i, item in enumerate(itens, start=1):
        partes += [f"## {i}. {item.titulo}", "", f"**Comando:** {item.teste}", ""]
        if item.verificacoes:
            partes += ["### Diagnósticos", ""] + [f"- {ic} **{nome}** — {det}" for ic, nome, det in item.verificacoes]
            partes.append("")
        for nome_tab, tab in item.tabelas:
            partes += [f"### {nome_tab}", "", *_tabela_markdown(tab), ""]
        if item.resultado:
            partes += ["### Resultado", ""] + [f"- {linha}" for linha in item.resultado] + [""]
        if item.avisos:
            partes += ["### Avisos", ""] + [f"- {a}" for a in item.avisos] + [""]
        if item.passos:
            partes += ["### Cálculo", "", "```text", *item.passos, "```", ""]
        if item.figuras:
            partes += [f"_{len(item.figuras)} gráfico(s) disponível(is) na versão HTML._", ""]
    return "\n".join(partes)


_CSS = """
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 960px; margin: 2rem auto;
       padding: 0 1rem; color: #1f2328; background: #ffffff; line-height: 1.5; }
h1 { border-bottom: 2px solid #1f77b4; padding-bottom: .3rem; }
h2 { margin-top: 2.5rem; border-bottom: 1px solid #d0d7de; padding-bottom: .2rem; }
.aviso { background: #fff8e1; border-left: 4px solid #f0ad4e; padding: .5rem 1rem; margin: .3rem 0; }
pre { background: #f6f8fa; padding: .75rem; overflow-x: auto; white-space: pre-wrap; }
@media (prefers-color-scheme: dark) {
  body { color: #e6edf3; background: #0d1117; }
  .aviso { background: #3a2f12; } pre { background: #161b22; }
}
"""


def para_html(itens: Sequence[ItemRelatorio], titulo: str = "Relatório — statlab") -> str:
    e = html.escape
    corpo = [
        f"<h1>{e(titulo)}</h1>",
        f"<p>Gerado em {datetime.now():%d/%m/%Y %H:%M}. {len(itens)} análise(s).</p>",
    ]
    plotly_incluido = False
    for i, item in enumerate(itens, start=1):
        corpo += [
            f"<h2>{i}. {e(item.titulo)}</h2>",
            f"<p><strong>Comando:</strong> {e(item.teste)}</p>",
        ]
        if item.verificacoes:
            corpo.append("<h3>Diagnósticos</h3><ul>")
            corpo += [f"<li>{ic} <strong>{e(nome)}</strong> — {e(det)}</li>" for ic, nome, det in item.verificacoes]
            corpo.append("</ul>")
        for nome_tab, tab in item.tabelas:
            corpo.append(f"<h3>{e(nome_tab)}</h3>" + tab.to_html(index=False, border=0))
        if item.resultado:
            corpo.append(
                "<h3>Resultado</h3><ul>" + "".join(f"<li>{e(linha)}</li>" for linha in item.resultado) + "</ul>"
            )
        corpo += [f'<p class="aviso">{e(a)}</p>' for a in item.avisos]
        for fig in item.figuras:
            corpo.append(fig.to_html(full_html=False, include_plotlyjs=not plotly_incluido))
            plotly_incluido = True
        if item.passos:
            corpo.append("<details><summary>Cálculo</summary><pre>" + e("\n".join(item.passos)) + "</pre></details>")
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{e(titulo)}</title><style>{_CSS}</style></head><body>" + "\n".join(corpo) + "</body></html>"
    )
