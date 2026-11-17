"""Gráficos Plotly do statlab (equivalentes aos do menu Gráficos do Minitab).

Funções puras: recebem dados e devolvem ``plotly.graph_objects.Figure``. Não importam Streamlit.
Dados faltantes (NaN) são removidos por grupo, e a quantidade descartada aparece no título quando relevante.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import p_valor
from statlab.core.normalidade import anderson_darling
from statlab.core.regressao import coeficientes

TEMPLATE = "plotly_white"
COR_GRUPOS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf", "#8c564b", "#e377c2"]


def _limpo(v: object) -> np.ndarray:
    return np.asarray(v, dtype=float)[~np.isnan(np.asarray(v, dtype=float))]


def _grupos_limpos(dados: Mapping[str, object], minimo: int = 1) -> dict[str, np.ndarray]:
    if not dados:
        raise ErroDeDados("Escolha pelo menos uma variável.")
    out: dict[str, np.ndarray] = {}
    for nome, v in dados.items():
        x = _limpo(v)
        if len(x) < minimo:
            raise ErroDeDados(f"{nome}: são necessárias pelo menos {minimo} observações não faltantes (há {len(x)}).")
        out[str(nome)] = x
    return out


def _aplicar_tema(fig: go.Figure, titulo: str, x: str | None = None, y: str | None = None) -> go.Figure:
    fig.update_layout(template=TEMPLATE, title=titulo, xaxis_title=x, yaxis_title=y, legend_title_text="")
    return fig


def histograma(
    dados: Mapping[str, object],
    *,
    titulo: str = "Histograma",
    curva_normal: bool = True,
    bins: int | None = None,
) -> go.Figure:
    """Histograma sobreposto por grupo, com curva normal ajustada (como o histograma com ajuste do Minitab)."""
    grupos = _grupos_limpos(dados, minimo=2)
    todos = np.concatenate(list(grupos.values()))
    arestas = np.histogram_bin_edges(todos, bins=bins if bins else "auto")
    largura = float(arestas[1] - arestas[0])
    centros = (arestas[:-1] + arestas[1:]) / 2
    fig = go.Figure()
    for i, (nome, x) in enumerate(grupos.items()):
        cor = COR_GRUPOS[i % len(COR_GRUPOS)]
        contagem, _ = np.histogram(x, bins=arestas)
        fig.add_bar(x=centros, y=contagem, width=largura, name=nome, opacity=0.55, marker_color=cor)
        dp = float(x.std(ddof=1))
        if curva_normal and dp > 0:
            xs = np.linspace(arestas[0], arestas[-1], 200)
            escala = len(x) * largura
            fig.add_scatter(
                x=xs,
                y=stats.norm.pdf(xs, x.mean(), dp) * escala,
                mode="lines",
                name=f"Normal ({nome})",
                line=dict(color=cor, width=2),
            )
    fig.update_layout(barmode="overlay")
    return _aplicar_tema(fig, titulo, "Valores", "Frequência")


def boxplot(dados: Mapping[str, object], *, titulo: str = "Boxplot") -> go.Figure:
    """Boxplot por grupo. Os pontos fora de 1,5 × D aparecem como outliers (mesma regra do diagrama de caixa)."""
    grupos = _grupos_limpos(dados, minimo=2)
    fig = go.Figure()
    for i, (nome, x) in enumerate(grupos.items()):
        fig.add_box(y=x, name=nome, boxpoints="outliers", marker_color=COR_GRUPOS[i % len(COR_GRUPOS)])
    return _aplicar_tema(fig, titulo, None, "Valores")


def dispersao(
    x: Sequence[object],
    y: Sequence[object],
    *,
    grupos: Sequence[object] | None = None,
    linha_regressao: bool = False,
    titulo: str = "Diagrama de dispersão",
    nome_x: str = "x",
    nome_y: str = "y",
) -> go.Figure:
    """Diagrama de dispersão (pares completos). Com ``grupos``, uma cor por grupo.

    ``linha_regressao`` traça a reta de mínimos quadrados (no conjunto inteiro).
    """
    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)
    if len(xs) != len(ys):
        raise ErroDeDados("X e Y precisam ter o mesmo número de pares.")
    mascara = ~(np.isnan(xs) | np.isnan(ys))
    if mascara.sum() < 2:
        raise ErroDeDados("O diagrama de dispersão precisa de pelo menos 2 pares completos.")
    fig = go.Figure()
    if grupos is None:
        fig.add_scatter(x=xs[mascara], y=ys[mascara], mode="markers", name="Dados")
    else:
        g = np.asarray(grupos, dtype=object)
        for i, nivel in enumerate(pd.unique(g[mascara])):
            sel = mascara & (g == nivel)
            fig.add_scatter(
                x=xs[sel], y=ys[sel], mode="markers", name=str(nivel), marker_color=COR_GRUPOS[i % len(COR_GRUPOS)]
            )
    if linha_regressao and mascara.sum() >= 2 and np.ptp(xs[mascara]) > 0:
        a, b = coeficientes(xs[mascara], ys[mascara])
        xl = np.array([xs[mascara].min(), xs[mascara].max()])
        fig.add_scatter(x=xl, y=a * xl + b, mode="lines", name="Regressão", line=dict(color="black", dash="dash"))
    return _aplicar_tema(fig, titulo, nome_x, nome_y)


def valores_individuais(dados: Mapping[str, object], *, titulo: str = "Gráfico de valores individuais") -> go.Figure:
    """Cada observação como um ponto na coluna do seu grupo, com a média do grupo unida por linha."""
    grupos = _grupos_limpos(dados, minimo=1)
    fig = go.Figure()
    medias_x, medias_y = [], []
    for i, (nome, x) in enumerate(grupos.items()):
        fig.add_scatter(
            x=[nome] * len(x),
            y=x,
            mode="markers",
            name=nome,
            marker=dict(color=COR_GRUPOS[i % len(COR_GRUPOS)], size=7, opacity=0.7),
        )
        medias_x.append(nome)
        medias_y.append(float(x.mean()))
    fig.add_scatter(x=medias_x, y=medias_y, mode="lines+markers", name="Média", line=dict(color="black"))
    return _aplicar_tema(fig, titulo, "Grupo", "Valores")


def intervalos(
    dados: Mapping[str, object],
    *,
    confianca: float = 0.95,
    titulo: str | None = None,
) -> go.Figure:
    """Intervalo de confiança para a média de cada grupo (t de Student, desvio amostral)."""
    grupos = _grupos_limpos(dados, minimo=2)
    nomes, medias, erros = [], [], []
    for nome, x in grupos.items():
        n = len(x)
        ep = float(x.std(ddof=1)) / np.sqrt(n)
        tc = float(stats.t.ppf((1 + confianca) / 2, n - 1))
        nomes.append(nome)
        medias.append(float(x.mean()))
        erros.append(tc * ep)
    fig = go.Figure()
    fig.add_scatter(
        x=nomes,
        y=medias,
        mode="markers",
        error_y=dict(type="data", array=erros, visible=True),
        name="Média",
        marker=dict(size=9, color="#1f77b4"),
    )
    pct = int(round(confianca * 100))
    return _aplicar_tema(fig, titulo or f"IC de {pct}% para a média", "Grupo", "Média")


def probabilidade_normal(valores: object, *, titulo: str | None = None) -> go.Figure:
    """Gráfico de probabilidade normal (quantis teóricos × observados) com reta de referência.

    O título traz o teste de Anderson-Darling (padrão do Minitab), quando há dados suficientes.
    """
    x = _limpo(valores)
    if len(x) < 3:
        raise ErroDeDados("O gráfico de probabilidade normal precisa de pelo menos 3 observações.")
    (osm, osr), (slope, intercept, _) = stats.probplot(x, dist="norm")
    xs = np.array([osm.min(), osm.max()])
    fig = go.Figure()
    fig.add_scatter(x=osm, y=osr, mode="markers", name="Dados", marker=dict(color="#1f77b4"))
    fig.add_scatter(x=xs, y=slope * xs + intercept, mode="lines", name="Normal ajustada", line=dict(color="red"))
    if titulo is None:
        if np.ptp(x) > 0:
            ad = anderson_darling(x)
            titulo = f"Probabilidade normal — Anderson-Darling A² = {ad.estatistica:.3f}, p {p_valor(ad.p)}"
        else:
            titulo = "Probabilidade normal"
    return _aplicar_tema(fig, titulo, "Quantis teóricos da normal", "Valores observados")


def pareto(categorias: Sequence[str], contagens: Sequence[float], *, titulo: str = "Gráfico de Pareto") -> go.Figure:
    """Barras em ordem decrescente e linha de porcentagem acumulada (eixo direito)."""
    cats = [str(c) for c in categorias]
    vals = np.asarray(contagens, dtype=float)
    if len(cats) != len(vals) or len(cats) == 0:
        raise ErroDeDados("Pareto: categorias e contagens devem ter o mesmo tamanho e não podem estar vazias.")
    if np.any(vals < 0) or np.nansum(vals) <= 0:
        raise ErroDeDados("Pareto: as contagens devem ser não negativas e ter soma positiva.")
    ordem = np.argsort(-vals, kind="stable")
    cats = [cats[i] for i in ordem]
    vals = vals[ordem]
    acumulada = np.cumsum(vals) / vals.sum() * 100
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=cats, y=vals, name="Contagem", marker_color="#1f77b4", secondary_y=False)
    fig.add_scatter(
        x=cats, y=acumulada, mode="lines+markers", name="% acumulada", line=dict(color="red"), secondary_y=True
    )
    fig.update_yaxes(range=[0, 105], ticksuffix="%", secondary_y=True)
    return _aplicar_tema(fig, titulo, "Categoria", "Contagem")


def barras(categorias: Sequence[str], valores: Sequence[float], *, titulo: str = "Gráfico de barras") -> go.Figure:
    cats = [str(c) for c in categorias]
    vals = np.asarray(valores, dtype=float)
    if len(cats) != len(vals) or not cats:
        raise ErroDeDados("Gráfico de barras: categorias e valores devem ter o mesmo tamanho.")
    fig = go.Figure(go.Bar(x=cats, y=vals, marker_color="#1f77b4"))
    return _aplicar_tema(fig, titulo, "Categoria", "Valor")


def serie_temporal(
    valores: Sequence[object],
    *,
    rotulos: Sequence[object] | None = None,
    titulo: str = "Gráfico de série temporal",
    nome_y: str = "Valor",
) -> go.Figure:
    """Valores na ordem em que aparecem. Com ``rotulos`` (ex.: datas), o eixo X usa esses rótulos."""
    y = np.asarray(valores, dtype=float)
    x = list(rotulos) if rotulos is not None else list(range(1, len(y) + 1))
    if len(x) != len(y):
        raise ErroDeDados("Série temporal: rótulos e valores devem ter o mesmo tamanho.")
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines+markers", name=nome_y, connectgaps=False))
    return _aplicar_tema(fig, titulo, "Tempo / ordem", nome_y)


def correlograma(tabela: pd.DataFrame, *, titulo: str = "Correlograma (Pearson)") -> go.Figure:
    """Matriz de correlações de Pearson entre colunas numéricas (pares completos por par de colunas)."""
    num = tabela.select_dtypes(include="number")
    if num.shape[1] < 2:
        raise ErroDeDados("O correlograma precisa de pelo menos 2 colunas numéricas.")
    corr = num.corr(method="pearson", min_periods=3)
    if corr.isna().all().all():
        raise ErroDeDados("Não há pares suficientes para calcular as correlações.")
    texto = [[("—" if pd.isna(v) else f"{v:.2f}".replace(".", ",")) for v in linha] for linha in corr.to_numpy()]
    fig = go.Figure(
        go.Heatmap(
            z=corr.to_numpy(),
            x=list(corr.columns),
            y=list(corr.index),
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
            reversescale=True,
            text=texto,
            texttemplate="%{text}",
            colorbar=dict(title="r"),
        )
    )
    return _aplicar_tema(fig, titulo)


def matriz_dispersao(tabela: pd.DataFrame, colunas: Sequence[str], *, titulo: str = "Matriz de dispersão") -> go.Figure:
    """Gráficos de dispersão duas a duas (linhas com faltantes em qualquer coluna são removidas)."""
    cols = list(colunas)
    if len(cols) < 2:
        raise ErroDeDados("A matriz de dispersão precisa de pelo menos 2 colunas.")
    sub = tabela[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(sub) < 2:
        raise ErroDeDados("A matriz de dispersão precisa de pelo menos 2 linhas completas.")
    fig = go.Figure(go.Splom(dimensions=[dict(label=c, values=sub[c].to_numpy()) for c in cols], marker=dict(size=5)))
    return _aplicar_tema(fig, titulo)


def tukey_intervalos(comparacoes: Sequence[object], *, titulo: str = "ICs simultâneos de 95% de Tukey") -> go.Figure:
    """Diferença de médias de cada par com o IC de Tukey. Intervalo que não contém o zero = diferença significativa."""
    pares = [c for c in comparacoes if getattr(c, "ic", None) is not None and getattr(c, "diferenca", None) is not None]
    if not pares:
        raise ErroDeDados("Não há intervalos de Tukey para mostrar.")
    rotulos = [f"{c.grupo_a} − {c.grupo_b}" for c in pares]
    centros = [c.diferenca for c in pares]
    fig = go.Figure(
        go.Scatter(
            x=centros,
            y=rotulos,
            mode="markers",
            marker=dict(size=9, color="#1f77b4"),
            error_x=dict(
                type="data",
                symmetric=False,
                array=[c.ic[1] - c.diferenca for c in pares],
                arrayminus=[c.diferenca - c.ic[0] for c in pares],
            ),
            name="Diferença",
        )
    )
    fig.add_vline(x=0, line_dash="dash", line_color="green")
    fig.update_yaxes(autorange="reversed")
    fig.add_annotation(
        text="Se um intervalo não contém o zero, as médias correspondentes são significativamente diferentes.",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.18,
        showarrow=False,
        font=dict(size=11),
    )
    return _aplicar_tema(fig, titulo, "Diferença de médias", None)
