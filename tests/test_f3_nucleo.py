"""F3 (núcleo): uma amostra, qui-quadrado, verificações estruturadas (✓/⚠/✗) e gráfico de Tukey."""

import numpy as np
import pytest
from scipy import stats

from statlab import graficos
from statlab.core.anova import tukey_hsd
from statlab.core.correlacao import correlacao
from statlab.core.dados import ErroDeDados
from statlab.core.nao_parametricos import kruskal_wallis
from statlab.core.proporcoes import z_duas_proporcoes
from statlab.core.qui_quadrado import aderencia, independencia, tabela_contingencia
from statlab.core.resultados import ATENCAO, FALHA, OK
from statlab.core.uma_amostra import (
    binomial_uma_proporcao,
    t_uma_amostra,
    wilcoxon_uma_amostra,
    z_uma_amostra,
    z_uma_proporcao,
)
from tests.helpers import aprox, gabarito, p_menor_que, pdf

X = np.random.default_rng(5).normal(52, 6, 25)

# --------------------------------------------------------------------------- uma amostra


@pytest.mark.parametrize("alt, scipy_alt", [("bilateral", "two-sided"), ("maior", "greater"), ("menor", "less")])
def test_t_uma_amostra_igual_ao_scipy(alt, scipy_alt):
    r = t_uma_amostra(X, 50, alternativa=alt)
    ref = stats.ttest_1samp(X, 50, alternative=scipy_alt)
    assert r.estatistica == pytest.approx(float(ref.statistic))
    assert r.p == pytest.approx(float(ref.pvalue))
    assert r.gl == (24.0,)


def test_t_uma_amostra_ic_95():
    r = t_uma_amostra(X, 50)
    ci = stats.ttest_1samp(X, 50).confidence_interval(0.95)
    assert r.ic == pytest.approx((float(ci.low), float(ci.high)))


def test_z_uma_amostra_formula():
    r = z_uma_amostra(X, 50, 6)
    z = (X.mean() - 50) / (6 / np.sqrt(len(X)))
    assert r.estatistica == pytest.approx(z)
    assert r.p == pytest.approx(2 * stats.norm.sf(abs(z)))
    assert r.ic == pytest.approx((X.mean() - 1.959964 * 6 / 5, X.mean() + 1.959964 * 6 / 5), rel=1e-6)


def test_z_sigma_invalido():
    with pytest.raises(ErroDeDados, match="σ"):
        z_uma_amostra(X, 50, 0)


def test_wilcoxon_uma_amostra_igual_ao_scipy():
    r = wilcoxon_uma_amostra(X, 50, alternativa="maior")
    ref = stats.wilcoxon(X - 50, alternative="greater")
    assert r.estatistica == float(ref.statistic)
    assert r.p == pytest.approx(float(ref.pvalue))


def test_uma_proporcao_normal_formula():
    r = z_uma_proporcao(58, 148, 0.5)
    z = (58 / 148 - 0.5) / np.sqrt(0.25 / 148)
    assert r.nome.endswith("(aproximação normal)")
    assert r.estatistica == pytest.approx(z)
    assert r.p == pytest.approx(2 * stats.norm.sf(abs(z)))


def test_uma_proporcao_binomial_exata():
    r = binomial_uma_proporcao(2, 10, 0.5, alternativa="menor")
    ref = stats.binomtest(2, 10, 0.5, alternative="less")
    assert r.nome.endswith("(binomial exata)")
    assert r.p == pytest.approx(ref.pvalue)
    ci = stats.binomtest(2, 10, 0.5).proportion_ci(method="exact")
    assert r.ic == pytest.approx((ci.low, ci.high))


def test_uma_proporcao_criterio_falho_e_so_diagnostico():
    """n·p̂·q̂ = 1,6 < 5: o z roda se for pedido, com ⚠️ nas verificações."""
    r = z_uma_proporcao(2, 10, 0.5)
    assert r.nome.endswith("(aproximação normal)")
    assert any(v.status == ATENCAO for v in r.verificacoes)


@pytest.mark.parametrize("x, n, p0", [(11, 10, 0.5), (1, 0, 0.5), (1, 10, 0.0), (1, 10, 1.0)])
def test_uma_proporcao_entradas_invalidas(x, n, p0):
    with pytest.raises(ErroDeDados):
        z_uma_proporcao(x, n, p0)


# --------------------------------------------------------------------------- qui-quadrado


def test_independencia_formula_manual_e_razao_verossimilhanca():
    obs = np.array([[31, 31], [117, 65]], dtype=float)
    r = independencia(obs)
    e = obs.sum(1, keepdims=True) * obs.sum(0) / obs.sum()
    assert r.estatistica == pytest.approx(((obs - e) ** 2 / e).sum())
    assert r.razao_verossimilhanca[0] == pytest.approx(2 * (obs * np.log(obs / e)).sum())
    assert r.gl == (1.0,)
    assert r.verificacoes[0].status == OK


def test_independencia_2x2_equivale_ao_z_das_proporcoes_gabarito_ex6():
    """Ex. 6 do gabarito: z = −1,989 e p = 0,047. No 2 × 2, χ² (sem Yates) = z² e o p é o mesmo."""
    g = gabarito()["ex6"]
    x1, n1 = g["g1"]
    x2, n2 = g["g2"]
    chi = independencia([[x1, n1 - x1], [x2, n2 - x2]])
    prop = z_duas_proporcoes(x1, n1, x2, n2)
    assert chi.estatistica == pytest.approx(prop.z**2)
    assert chi.p == pytest.approx(prop.p)
    aprox(chi.p, 0.047, 3)


def test_independencia_fisher_quando_pedido():
    r = independencia([[1, 9], [6, 4]], metodo="fisher")
    assert r.nome.startswith("Teste exato de Fisher")
    assert r.p == pytest.approx(stats.fisher_exact([[1, 9], [6, 4]]).pvalue)


def test_independencia_esperados_pequenos_nao_trocam_o_metodo():
    """Antes o app pulava para Fisher sozinho; agora mantém o χ² pedido e avisa."""
    r = independencia([[1, 9], [6, 4]])
    assert r.nome == "Qui-quadrado de independência"
    assert r.verificacoes[0].status == ATENCAO
    assert any("Cochran" in a for a in r.avisos)


def test_independencia_esperados_pequenos_tabela_maior_avisa():
    r = independencia([[1, 2, 30], [2, 1, 25], [0, 3, 40]])
    assert r.nome == "Qui-quadrado de independência"
    assert any("agrupar" in a for a in r.avisos)


@pytest.mark.parametrize(
    "tabela",
    [[[1, 2]], [[1, -2], [3, 4]], [[1.5, 2], [3, 4]], [[0, 0], [3, 4]], [[1, np.nan], [3, 4]]],
)
def test_independencia_entradas_invalidas(tabela):
    with pytest.raises(ErroDeDados):
        independencia(tabela)


def test_tabela_contingencia_de_colunas():
    import pandas as pd

    df = pd.DataFrame({"Turma": ["A", "A", "B", "B", "B", None], "Aprov": ["s", "n", "s", "s", "n", "s"]})
    tab = tabela_contingencia(df, "Turma", "Aprov")
    assert tab.loc["B", "s"] == 2
    assert int(tab.to_numpy().sum()) == 5
    with pytest.raises(ErroDeDados):
        tabela_contingencia(df, "Turma", "Turma")


def test_aderencia_com_pesos_igual_ao_scipy():
    r = aderencia([18, 22, 20, 40], proporcoes=[1, 1, 1, 2], categorias=["a", "b", "c", "d"])
    ref = stats.chisquare([18, 22, 20, 40], [20, 20, 20, 40])
    assert r.estatistica == pytest.approx(float(ref.statistic))
    assert r.p == pytest.approx(float(ref.pvalue))
    assert r.gl == (3.0,)


def test_aderencia_uniforme_por_padrao():
    r = aderencia([10, 10, 10])
    assert r.estatistica == pytest.approx(0.0)
    assert r.p == pytest.approx(1.0)


def test_aderencia_entradas_invalidas():
    with pytest.raises(ErroDeDados):
        aderencia([5])
    with pytest.raises(ErroDeDados):
        aderencia([5, 5], proporcoes=[1])


# --------------------------------------------------------------------------- verificações nos fluxos antigos


def test_verificacoes_correlacao_pdf_ex3_sao_diagnostico():
    d = pdf()["ex3_atendimento"]
    c = correlacao(d["x"], d["y"], nome_x="Tempo", nome_y="Produtividade")
    status = {v.nome: v.status for v in c.verificacoes}
    assert status["Outliers — Produtividade"] == ATENCAO  # 1.100 é suave
    assert status["Normalidade — Tempo"] == FALHA
    # o diagnóstico não manda trocar de método: o Pearson pedido foi o que rodou
    assert c.metodo == "Pearson"


def test_verificacoes_proporcoes_criterio_nao_atendido():
    r = z_duas_proporcoes(2, 10, 5, 12)
    assert [v.status for v in r.verificacoes] == [ATENCAO, ATENCAO]


# --------------------------------------------------------------------------- Tukey (gráfico)


def test_grafico_tukey_reproduz_pdf_ex6():
    d = pdf()["ex6_forca"]
    fig = graficos.tukey_intervalos(tukey_hsd({"G1": d["g1"], "G2": d["g2"], "G3": d["g3"]}))
    assert list(fig.data[0].y) == ["G1 − G2", "G1 − G3", "G2 − G3"]
    aprox(fig.data[0].x[0], -12.68, 2)
    aprox(fig.data[0].x[0] - fig.data[0].error_x.arrayminus[0], -23.42, 2)


def test_grafico_tukey_sem_ic_erro():
    from statlab.core.resultados import ParComparacao

    with pytest.raises(ErroDeDados):
        graficos.tukey_intervalos([ParComparacao("a", "b", 0.5, "MW")])


def test_p_resistencia_kw_continua_igual():
    d = pdf()["ex7_resistencia"]
    r = kruskal_wallis({"G1": d["g1"], "G2": d["g2"], "G3": d["g3"]})
    aprox(r.estatistica, 29.37, 2)
    p_menor_que(r.p)
