"""Teste de sinal, teste de uma variância (χ²) e igualdade de variâncias (F / Bartlett / Levene).

Referências externas: statsmodels (sign_test), scipy (bartlett, levene, chi2) e o exemplo de Montgomery &
Runger ("Estatística aplicada e probabilidade para engenheiros", exemplo do volume de enchimento de garrafas:
n = 20, s² = 0,0153, σ₀² = 0,01 → χ² = 29,07; 0,05 < p < 0,10 unilateral superior).
"""

from math import comb

import numpy as np
import pytest
from scipy import stats
from statsmodels.stats.descriptivestats import sign_test

from statlab.core import uma_amostra, variancias
from statlab.core.conclusoes import concluir
from statlab.core.dados import ErroDeDados
from statlab.core.resultados import FALHA, OK
from statlab.core.uma_amostra import analisar_sinal, analisar_uma_variancia, qui_quadrado_variancia
from statlab.core.variancias import igualdade_variancias
from tests.helpers import aprox, pdf

# --------------------------------------------------------------------------- teste de sinal


def test_sinal_confere_com_binomial_a_mao_e_statsmodels():
    v = np.array([12.1, 9.8, 13.5, 14.0, 11.2, 15.3, 16.1, 10.0, 13.9, 14.4, 12.0, 15.0])
    res = uma_amostra.teste_sinal(v, 12.0)
    # acima de 12: 12,1; 13,5; 14,0; 15,3; 16,1; 13,9; 14,4; 15,0 = 8; abaixo: 9,8; 11,2; 10,0 = 3; igual: 1
    assert res.n == 11
    p_mao = min(1.0, 2 * sum(comb(11, k) for k in range(8, 12)) / 2**11)
    assert res.p == pytest.approx(p_mao)
    _, p_sm = sign_test(v, 12.0)
    assert res.p == pytest.approx(p_sm)
    assert res.mediana == pytest.approx(13.7)


@pytest.mark.parametrize(("alternativa", "cauda"), [("maior", range(8, 12)), ("menor", range(0, 9))])
def test_sinal_unilateral(alternativa, cauda):
    v = np.array([12.1, 9.8, 13.5, 14.0, 11.2, 15.3, 16.1, 10.0, 13.9, 14.4, 12.0, 15.0])
    res = uma_amostra.teste_sinal(v, 12.0, alternativa=alternativa)
    assert res.p == pytest.approx(sum(comb(11, k) for k in cauda) / 2**11)


def test_sinal_tudo_igual_a_m0_vira_erro_de_dominio():
    with pytest.raises(ErroDeDados):
        uma_amostra.teste_sinal(np.array([5.0, 5.0, 5.0]), 5.0)


def test_analisar_sinal_avisa_fora_da_apostila_e_conclusao_cita_mediana():
    v = [20, 22, 25, 26, 27, 28, 29, 30, 31, 33, 34, 35]
    res = analisar_sinal(v, 21, nome="tempo")
    assert res.significativo  # 11 de 12 acima
    assert any("fora da apostila" in a for a in res.avisos)
    texto = concluir(res, variavel="tempo")
    assert "mediana de tempo" in texto and "significativamente maior" in texto
    assert "média" not in texto


def test_analisar_sinal_exclui_extremo_pela_regra_da_disciplina():
    v = [10, 11, 12, 12, 13, 13, 14, 14, 15, 100]
    res = analisar_sinal(v, 11.5)
    assert any("Outlier extremo excluído" in a for a in res.avisos)
    assert res.n == 9  # 9 valores restantes, nenhum igual a 11,5


# --------------------------------------------------------------------------- uma variância


def _com_variancia(n: int, s2: float, media: float = 10.0) -> np.ndarray:
    base = stats.norm.ppf((np.arange(1, n + 1) - 0.375) / (n + 0.25))  # escores normais: amostra "bem normal"
    base = (base - base.mean()) / base.std(ddof=1)
    return media + base * np.sqrt(s2)


def test_uma_variancia_exemplo_montgomery():
    v = _com_variancia(20, 0.0153)
    res = qui_quadrado_variancia(v, 0.1, alternativa="maior")
    aprox(res.estatistica, 29.07, 2)
    assert res.gl == (19.0,)
    assert 0.05 < res.p < 0.10
    assert res.p == pytest.approx(stats.chi2.sf(29.07, 19))
    # IC 95% para σ²: 19·s²/χ²(0,975; 19) a 19·s²/χ²(0,025; 19)
    lo, hi = res.ic_variancia
    assert lo == pytest.approx(19 * 0.0153 / stats.chi2.ppf(0.975, 19))
    assert hi == pytest.approx(19 * 0.0153 / stats.chi2.ppf(0.025, 19))
    assert res.ic == pytest.approx((np.sqrt(lo), np.sqrt(hi)))


def test_uma_variancia_bilateral_e_o_dobro_da_menor_cauda():
    v = _com_variancia(20, 0.0153)
    bi = qui_quadrado_variancia(v, 0.1)
    assert bi.p == pytest.approx(2 * stats.chi2.sf(29.07, 19))
    menor = qui_quadrado_variancia(v, 0.1, alternativa="menor")
    assert menor.p == pytest.approx(stats.chi2.cdf(29.07, 19))


def test_uma_variancia_nao_usa_atalho_do_tcl():
    # 40 valores exponenciais: n ≥ 30, mas não normais → FALHA (o TCL não vale para variâncias)
    v = stats.expon.ppf((np.arange(1, 41) - 0.5) / 40)
    res = analisar_uma_variancia(v, 1.0, nome="x")
    norm = next(c for c in res.verificacoes if c.nome.startswith("Normalidade"))
    assert norm.status == FALHA
    assert not res.confiavel
    assert any("Bonett" in a for a in res.avisos)
    assert "não é confiável" in concluir(res, variavel="x")


def test_uma_variancia_normal_tem_cartao_ok_e_conclusao_com_ic():
    v = _com_variancia(25, 4.0)
    res = analisar_uma_variancia(v, 1.0, nome="peso")
    assert next(c for c in res.verificacoes if c.nome.startswith("Normalidade")).status == OK
    assert res.significativo
    texto = concluir(res, variavel="peso")
    assert "desvio padrão de peso" in texto and "significativamente maior" in texto and "IC 95%" in texto


def test_uma_variancia_sigma0_invalido():
    with pytest.raises(ErroDeDados):
        qui_quadrado_variancia(np.array([1.0, 2.0, 3.0]), 0.0)


# --------------------------------------------------------------------------- igualdade de variâncias


def test_dois_grupos_normais_usam_o_teste_f_do_pdf():
    d = pdf()["ex5_apf"]
    res = igualdade_variancias({"G1": d["g1"], "G2": d["g2"]})
    assert res.metodo == "F"
    aprox(res.estatistica, 1.277, 3)  # PDF: F = 1,277; p = 0,774
    aprox(res.p, 0.774, 3)
    assert res.p == pytest.approx(variancias.teste_f(np.array(d["g1"]), np.array(d["g2"])).p)
    assert res.p_bartlett == pytest.approx(stats.bartlett(d["g1"], d["g2"]).pvalue)


def test_tres_grupos_normais_usam_bartlett_igual_ao_scipy():
    d = pdf()["ex6_forca"]
    grupos = {"G1": d["g1"], "G2": d["g2"], "G3": d["g3"]}
    res = igualdade_variancias(grupos)
    if res.metodo != "Bartlett":
        pytest.skip("algum grupo do exemplo não é normal; o caso fica coberto pelo teste sintético abaixo")
    b = stats.bartlett(*grupos.values())
    assert res.estatistica == pytest.approx(b.statistic)
    assert res.p == pytest.approx(b.pvalue)


def test_bartlett_confere_com_a_formula():
    grupos = {"A": _com_variancia(10, 1.0), "B": _com_variancia(12, 2.5, 20), "C": _com_variancia(8, 6.0, 30)}
    res = igualdade_variancias(grupos)
    assert res.metodo == "Bartlett"
    ns = np.array([len(g) for g in grupos.values()])
    s2 = np.array([np.var(g, ddof=1) for g in grupos.values()])
    big_n, k = ns.sum(), len(ns)
    sp2 = ((ns - 1) * s2).sum() / (big_n - k)
    num_ = (big_n - k) * np.log(sp2) - ((ns - 1) * np.log(s2)).sum()
    den = 1 + (1 / (3 * (k - 1))) * ((1 / (ns - 1)).sum() - 1 / (big_n - k))
    assert res.estatistica == pytest.approx(num_ / den)
    assert res.gl == (2.0,)
    assert res.razao == pytest.approx(6.0)
    assert any("fora da apostila" in a or "não estão na apostila" in a for a in res.avisos)


def test_grupo_nao_normal_usa_levene_mediana():
    nao_normal = stats.expon.ppf((np.arange(1, 21) - 0.5) / 20) * 3
    grupos = {"A": _com_variancia(20, 1.0), "B": nao_normal, "C": _com_variancia(20, 2.0)}
    res = igualdade_variancias(grupos)
    assert res.metodo == "Levene"
    lev = stats.levene(*grupos.values(), center="median")
    assert res.p == pytest.approx(lev.pvalue)
    assert res.estatistica == pytest.approx(lev.statistic)
    assert res.gl == (2.0, 57.0)


def test_conclusao_igualdade_nunca_afirma_iguais():
    grupos = {"A": _com_variancia(15, 1.0), "B": _com_variancia(15, 1.2, 5)}
    res = igualdade_variancias(grupos)
    assert not res.significativo
    texto = concluir(res, variavel="tempo")
    assert texto.startswith("Não há evidência de diferença")
    assert "são iguais" not in texto


def test_igualdade_variancias_dados_ruins():
    with pytest.raises(ErroDeDados):
        igualdade_variancias({"A": [1, 2, 3]})
    with pytest.raises(ErroDeDados):
        igualdade_variancias({"A": [1, 2, 3, 4], "B": [5, 5, 5, 5]})
    with pytest.raises(ErroDeDados):
        igualdade_variancias({"A": [1, 2, 3, 4], "B": [1, "x", 3]})
