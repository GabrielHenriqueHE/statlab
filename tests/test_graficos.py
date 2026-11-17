"""F2: gráficos Plotly e exportação. Verifica a estrutura das figuras (traces, títulos, valores)."""

import numpy as np
import pandas as pd
import pytest

from statlab import graficos
from statlab.core.dados import ErroDeDados

RNG = np.random.default_rng(11)
X = RNG.normal(10, 2, 40)


def test_histograma_um_grupo_com_curva_normal():
    fig = graficos.histograma({"Dias": X})
    tipos = [t.type for t in fig.data]
    assert tipos == ["bar", "scatter"]
    assert fig.data[1].name == "Normal (Dias)"


def test_histograma_contagens_somam_n():
    fig = graficos.histograma({"A": X, "B": X + 1}, curva_normal=False)
    assert sum(sum(t.y) for t in fig.data) == 2 * len(X)


def test_histograma_sem_curva_quando_desligada():
    fig = graficos.histograma({"A": X}, curva_normal=False)
    assert all(t.type == "bar" for t in fig.data)


def test_boxplot_um_trace_por_grupo():
    fig = graficos.boxplot({"A": X, "B": X * 2})
    assert [t.name for t in fig.data] == ["A", "B"]
    assert all(t.type == "box" for t in fig.data)


def test_dispersao_com_grupos_e_reta():
    x = np.arange(10, dtype=float)
    y = 2 * x + 1
    grupos = np.array(["a"] * 5 + ["b"] * 5, dtype=object)
    fig = graficos.dispersao(x, y, grupos=grupos, linha_regressao=True)
    nomes = [t.name for t in fig.data]
    assert nomes == ["a", "b", "Regressão"]
    reta = fig.data[-1]
    assert list(reta.y) == pytest.approx([1.0, 19.0])


def test_dispersao_ignora_pares_com_faltante():
    fig = graficos.dispersao([1.0, np.nan, 3.0, 4.0], [2.0, 4.0, 5.0, np.nan])
    assert list(fig.data[0].x) == [1.0, 3.0]


def test_dispersao_precisa_de_dois_pares():
    with pytest.raises(ErroDeDados):
        graficos.dispersao([1.0, np.nan], [np.nan, 2.0])


def test_valores_individuais_medias_corretas():
    fig = graficos.valores_individuais({"A": [1.0, 3.0], "B": [10.0, 20.0, 30.0]})
    media = fig.data[-1]
    assert list(media.y) == pytest.approx([2.0, 20.0])


def test_intervalos_centro_e_erro_t_student():
    from scipy import stats

    fig = graficos.intervalos({"A": X})
    erro = fig.data[0].error_y.array[0]
    esperado = stats.t.ppf(0.975, len(X) - 1) * X.std(ddof=1) / np.sqrt(len(X))
    assert erro == pytest.approx(esperado)
    assert "95%" in fig.layout.title.text


def test_probabilidade_normal_titulo_com_anderson_darling():
    fig = graficos.probabilidade_normal(X)
    assert "Anderson-Darling" in fig.layout.title.text
    assert len(fig.data[0].x) == len(X)


def test_probabilidade_normal_poucos_dados_erro():
    with pytest.raises(ErroDeDados):
        graficos.probabilidade_normal([1.0, 2.0])


def test_pareto_ordem_decrescente_e_acumulada_100():
    fig = graficos.pareto(["a", "b", "c"], [5, 3, 2])
    assert list(fig.data[0].x) == ["a", "b", "c"]
    assert list(fig.data[1].y) == pytest.approx([50.0, 80.0, 100.0])


def test_pareto_validacoes():
    with pytest.raises(ErroDeDados):
        graficos.pareto(["a"], [1, 2])
    with pytest.raises(ErroDeDados):
        graficos.pareto(["a", "b"], [0, 0])


def test_barras_e_serie_temporal():
    b = graficos.barras(["x", "y"], [1.0, 2.0])
    assert list(b.data[0].y) == [1.0, 2.0]
    s = graficos.serie_temporal([1.0, 2.0, 3.0], rotulos=["jan", "fev", "mar"])
    assert list(s.data[0].x) == ["jan", "fev", "mar"]
    with pytest.raises(ErroDeDados):
        graficos.serie_temporal([1.0, 2.0], rotulos=["x"])


def test_correlograma_matriz_simetrica_diagonal_um():
    df = pd.DataFrame({"a": X, "b": X * 2 + 1, "c": RNG.normal(size=len(X))})
    fig = graficos.correlograma(df)
    z = np.asarray(fig.data[0].z)
    assert z.shape == (3, 3)
    assert np.allclose(np.diag(z), 1.0)
    assert np.allclose(z, z.T)
    assert z[0, 1] == pytest.approx(1.0)


def test_correlograma_exige_duas_colunas():
    with pytest.raises(ErroDeDados):
        graficos.correlograma(pd.DataFrame({"a": X}))


def test_matriz_dispersao_remove_linhas_incompletas():
    df = pd.DataFrame({"a": [1.0, 2.0, np.nan, 4.0], "b": [1.0, np.nan, 3.0, 4.0]})
    fig = graficos.matriz_dispersao(df, ["a", "b"])
    assert len(fig.data[0].dimensions[0].values) == 2


def test_html_autocontido_sem_cdn():
    fig = graficos.histograma({"A": X})
    conteudo = graficos.html(fig).decode("utf-8")
    assert "<html" in conteudo.lower()
    assert '<script src="http' not in conteudo  # nada carregado de fora (privacidade e uso offline)


def test_png_disponivel_ou_erro_claro():
    fig = graficos.barras(["a"], [1.0])
    try:
        dados = graficos.imagem(fig, "png")
    except graficos.ErroExportacao as exc:
        assert "Chrome" in str(exc)
    else:
        assert dados[:8] == b"\x89PNG\r\n\x1a\n"


def test_formato_de_imagem_invalido():
    with pytest.raises(graficos.ErroExportacao):
        graficos.imagem(graficos.barras(["a"], [1.0]), "gif")
