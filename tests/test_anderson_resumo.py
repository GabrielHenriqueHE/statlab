"""F2: Anderson-Darling (padrão do Minitab) e o resumo 'Estatísticas descritivas' do Minitab."""

import numpy as np
import pytest
from scipy import stats
from statsmodels.stats.diagnostic import normal_ad

from statlab.core.dados import ErroDeDados
from statlab.core.descritiva import resumo_estatistico
from statlab.core.normalidade import anderson_darling, estatistica_anderson_darling, p_anderson_darling


@pytest.mark.parametrize("n", [5, 12, 50, 200])
def test_ad_igual_ao_statsmodels(n):
    x = np.random.default_rng(n).normal(size=n) * 3 + 10
    a2_sm, p_sm = normal_ad(x)
    assert estatistica_anderson_darling(x) == pytest.approx(float(a2_sm), rel=1e-9)
    assert p_anderson_darling(estatistica_anderson_darling(x), n) == pytest.approx(float(p_sm), rel=1e-9)


def test_ad_formula_explicita_bate():
    """A² = −n − (1/n) Σ (2i−1)[ln Φ(z_i) + ln(1−Φ(z_{n+1−i}))] com z padronizado por média e DP amostrais."""
    x = np.sort(np.random.default_rng(7).gamma(2, size=25))
    n = len(x)
    z = (x - x.mean()) / x.std(ddof=1)
    i = np.arange(1, n + 1)
    manual = -n - np.sum((2 * i - 1) * (np.log(stats.norm.cdf(z)) + np.log(1 - stats.norm.cdf(z[::-1])))) / n
    assert estatistica_anderson_darling(x) == pytest.approx(manual, rel=1e-9)


def test_p_ad_reproduz_o_relatorio_da_brochure():
    """Brochure do Minitab: A-Squared 0,25 e P-Value 0,724 com N = 50 (A² ≈ 0,2524 arredonda para 0,25)."""
    assert p_anderson_darling(0.2524, 50) == pytest.approx(0.724, abs=0.001)


def test_anderson_darling_normal_nao_rejeita():
    x = np.random.default_rng(0).normal(50, 3, 80)
    r = anderson_darling(x)
    assert r.normal
    assert r.rotulo_estatistica == "A²"
    assert r.p > 0.05


def test_anderson_darling_exponencial_rejeita():
    x = np.random.default_rng(1).exponential(2, 120)
    assert not anderson_darling(x).normal


def test_ad_exige_variacao_e_tamanho():
    with pytest.raises(ErroDeDados):
        anderson_darling(np.array([2.0, 2.0, 2.0]))
    with pytest.raises(ErroDeDados):
        anderson_darling(np.array([1.0, 2.0]))


def test_resumo_formulas_minitab_assimetria_curtose():
    x = np.random.default_rng(4).gamma(2, size=30)
    n, m, s = len(x), x.mean(), x.std(ddof=1)
    g1 = n / ((n - 1) * (n - 2)) * np.sum(((x - m) / s) ** 3)
    g2 = (n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3)) * np.sum(((x - m) / s) ** 4) - 3 * (n - 1) ** 2 / (
        (n - 2) * (n - 3)
    )
    r = resumo_estatistico(x)
    assert r.assimetria == pytest.approx(g1, rel=1e-9)
    assert r.curtose == pytest.approx(g2, rel=1e-9)


def test_resumo_ic_e_ep_e_faltantes():
    dados = np.array([10.0, 12.0, np.nan, 11.0, 13.0, np.nan])
    r = resumo_estatistico(dados)
    assert r.n == 4
    assert r.n_faltantes == 2
    assert r.ep_media == pytest.approx(np.std([10, 12, 11, 13], ddof=1) / 2)
    tc = stats.t.ppf(0.975, 3)
    assert r.ic_media[0] == pytest.approx(11.5 - tc * r.ep_media)
    assert r.ic_media[1] == pytest.approx(11.5 + tc * r.ep_media)


def test_resumo_quartis_e_mediana():
    r = resumo_estatistico([1.0, 2, 3, 4, 5, 6, 7, 8])
    assert (r.minimo, r.q1, r.mediana, r.q3, r.maximo) == (1.0, 2.75, 4.5, 6.25, 8.0)


def test_resumo_poucos_valores_erro():
    with pytest.raises(ErroDeDados):
        resumo_estatistico([1.0, np.nan, np.nan])


def test_resumo_n_pequeno_assimetria_nan():
    r = resumo_estatistico([1.0, 2.0])
    assert np.isnan(r.assimetria)
    assert np.isnan(r.curtose)
