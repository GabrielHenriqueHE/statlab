"""Aceitação: regressão linear simples e testes t (pareado e independente), contra o PDF e o gabarito."""

import numpy as np
import pytest

from statlab.core import variancias as var_mod  # evita o pytest coletar 'teste_f' como teste
from statlab.core.correlacao import correlacao
from statlab.core.dados import ErroDeDados
from statlab.core.normalidade import shapiro_wilk
from statlab.core.regressao import coeficientes, prever
from statlab.core.testes_t import t_independente, t_pareado
from tests.helpers import aprox, gabarito, p_menor_que, pdf

# --------------------------------------------------------------------------- regressão


def _reta(d):
    """a, b e a faixa observada de x, como a apostila calcula."""
    a, b = coeficientes(np.asarray(d["x"], float), np.asarray(d["y"], float))
    return a, b, min(d["x"]), max(d["x"])


def test_pdf_ex1_reta_publicidade():
    """PDF 3: a = 4,70; b = 12,20; ŷ = 4,70x + 12,20; previsão para x = 7 → 45,1."""
    d = pdf()["ex1_publicidade"]
    a, b, xmin, xmax = _reta(d)
    aprox(a, 4.70, 2)
    aprox(b, 12.20, 2)
    yhat, aviso = prever(a, b, 7, x_min=xmin, x_max=xmax)
    aprox(yhat, 45.1, 1)
    assert aviso is None  # 7 está dentro da faixa 2–10
    assert (xmin, xmax) == (2, 10)


def test_pdf_ex1_extrapolacao_gera_aviso():
    d = pdf()["ex1_publicidade"]
    a, b, xmin, xmax = _reta(d)
    yhat, aviso = prever(a, b, 0, x_min=xmin, x_max=xmax)
    aprox(yhat, 12.2, 1)  # PDF: 'sem investimento, R$ 12,2 mil — extrapolação'
    assert aviso is not None and "extrapolação" in aviso


def test_pdf_ex2_reta_treinamento_negativa():
    """PDF 3: a = −0,9219; b = 11,75; previsão para 5 h ≈ 7,1 erros."""
    d = pdf()["ex2_treinamento"]
    a, b, *_ = _reta(d)
    aprox(a, -0.9219, 4)
    aprox(b, 11.75, 2)
    aprox(prever(a, b, 5)[0], 7.1, 1)


def test_coeficientes_formula_direta():
    a, b = coeficientes(np.array([2, 4, 6, 8, 8, 10, 10], float), np.array([10, 8, 6, 4, 5, 2, 3], float))
    aprox(a, -0.9219, 4)
    aprox(b, 11.75, 2)


def test_gabarito_ex9_regressao():
    g = gabarito()["ex9"]
    a, b, *_ = _reta(g)
    aprox(a, 0.1585, 4)
    aprox(b, 1.763, 3)
    aprox(prever(a, b, 32)[0], 6.84, 2)


def test_regressao_nao_depende_da_significancia_da_correlacao():
    """Ex. 1 do gabarito: a correlação não é significativa, mas a reta é calculada mesmo assim."""
    g = gabarito()["ex1"]
    c = correlacao(g["x"], g["y"])
    assert not c.significativo
    a, b = coeficientes(np.asarray(g["x"], float), np.asarray(g["y"], float))
    assert a is not None and b is not None
    aprox(prever(a, b, float(np.mean(g["x"])))[0], float(np.mean(g["y"])), 2)


def test_regressao_usa_todos_os_pares_recebidos():
    """Mesmo com um y extremo, nada é excluído: quem exclui é quem chama."""
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    y = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 500]  # y extremo
    c = correlacao(x, y)
    assert c.n == 12
    a_com, _ = coeficientes(np.asarray(x, float), np.asarray(y, float))
    a_sem, _ = coeficientes(np.asarray(x[:-1], float), np.asarray(y[:-1], float))
    assert a_com != a_sem  # o extremo muda a reta — por isso excluir é decisão explícita


# --------------------------------------------------------------------------- teste t


def test_pdf_ex4_t_pareado_otimizacao():
    """PDF 6.2: d̄ = 1552,6; t = 21,85; gl = 14; p < 0,001; IC 95% (1400,2; 1705,0)."""
    d = pdf()["ex4_antes_depois"]
    t = t_pareado(np.array(d["antes"], float), np.array(d["depois"], float), alternativa="maior")
    aprox(t.media_diferenca, 1552.6, 1)
    aprox(t.estatistica, 21.85, 2)
    assert t.gl == (14.0,)
    p_menor_que(t.p)
    aprox(t.ic[0], 1400.2, 1)
    aprox(t.ic[1], 1705.0, 1)


def test_pdf_ex4_normalidade_das_diferencas_p_0537():
    """A normalidade das diferenças é uma análise própria (p = 0,537), não um pré-passo do t."""
    d = pdf()["ex4_antes_depois"]
    dif = np.array(d["antes"], float) - np.array(d["depois"], float)
    aprox(shapiro_wilk(dif).p, 0.537, 3)
    res = t_pareado(np.array(d["antes"], float), np.array(d["depois"], float), alternativa="maior")
    aprox(res.estatistica, 21.85, 2)
    assert res.nivel_confianca == 99


def test_pdf_ex4_alternativa_welch_do_mesmo_pareado_t_24_19():
    """PDF 6.2 (E se não fossem o mesmo item?): t de Welch = 24,19."""
    d = pdf()["ex4_antes_depois"]
    t = t_independente(np.array(d["antes"], float), np.array(d["depois"], float), variancias_iguais=False)
    aprox(t.estatistica, 24.19, 2)
    assert t.nome.startswith("t de Welch")


def test_pdf_ex5_variancias_f_e_levene():
    """PDF 5: F = 1,277; gl = 6 e 6; p = 0,774 (Levene p = 0,799)."""
    d = pdf()["ex5_apf"]
    g1, g2 = np.array(d["g1"], float), np.array(d["g2"], float)
    v = var_mod.teste_f(g1, g2)
    aprox(v.estatistica, 1.277, 3)
    aprox(v.p, 0.774, 3)
    aprox(v.p_levene, 0.799, 3)
    assert v.iguais
    aprox(var_mod.levene_mediana(g1, g2), 0.799, 3)


def test_pdf_ex5_t_independente_apf():
    """PDF 6.3: sp = 21,07; t = −7,93; gl = 12; p < 0,001; IC 95% (−113,8; −64,8)."""
    d = pdf()["ex5_apf"]
    t = t_independente(np.array(d["g1"], float), np.array(d["g2"], float), variancias_iguais=True)
    aprox(t.estatistica, -7.93, 2)
    assert t.gl == (12.0,)
    p_menor_que(t.p)
    aprox(t.ic[0], -113.8, 1)
    aprox(t.ic[1], -64.8, 1)
    assert t.variancias_iguais is True
    assert t.nome.startswith("t independente")


def test_pdf_ex5_t_mostra_as_medias_dos_grupos():
    d = pdf()["ex5_apf"]
    res = t_independente(
        np.array(d["g1"], float), np.array(d["g2"], float), variancias_iguais=True, nome_a="G1", nome_b="G2"
    )
    aprox(res.medias["G1"], 121.86, 2)
    aprox(res.medias["G2"], 211.14, 2)
    aprox(res.estatistica, -7.93, 2)


# --------------------------------------------------------------------------- gabarito 2026: t


def test_gabarito_ex2_pareado_unilateral_diminuiu():
    g = gabarito()["ex2"]
    res = t_pareado(np.array(g["antes"], float), np.array(g["depois"], float), alternativa="maior")
    aprox(res.estatistica, 4.07, 2)
    assert res.gl == (11.0,)
    p_menor_que(res.p)  # unilateral < 0,001
    bil = t_pareado(np.array(g["antes"], float), np.array(g["depois"], float))
    aprox(bil.p, 0.002, 3)  # bilateral
    aprox(bil.ic[0], 25.28, 2)
    aprox(bil.ic[1], 84.72, 2)


def test_gabarito_ex3_t_variancia_combinada():
    """Com a opção "variâncias iguais" marcada: gl = 17 (combinada), não o gl de Welch."""
    g = gabarito()["ex3"]
    res = t_independente(g["a"], g["b"], variancias_iguais=True, nome_a="Equipe A", nome_b="Equipe B")
    assert res.nome.startswith("t independente")
    aprox(res.estatistica, 1.473, 3)
    assert res.gl == (17.0,)
    aprox(res.p, 0.159, 3)
    aprox(res.ic[0], -2.12, 2)
    aprox(res.ic[1], 11.91, 2)


def test_gabarito_ex7_t_variancia_combinada_com_todos_os_dados():
    """O outlier suave 316 do Fornecedor 2 permanece: o app não exclui nada sozinho."""
    g = gabarito()["ex7"]
    res = t_independente(g["f1"], g["f2"], variancias_iguais=True, nome_a="Fornecedor 1", nome_b="Fornecedor 2")
    aprox(res.estatistica, 3.498, 3)
    assert res.gl == (23.0,)
    aprox(res.p, 0.002, 3)
    aprox(res.ic[0], 19.19, 2)
    aprox(res.ic[1], 74.74, 2)
    assert res.n == len(g["f1"]) + len(g["f2"])
    assert res.avisos == []
    assert res.nivel_confianca == 99


# --------------------------------------------------------------------------- bordas


def test_t_pareado_diferencas_todas_iguais_erro():
    with pytest.raises(ErroDeDados, match="todos os valores são iguais"):
        t_pareado(np.array([1.0, 2, 3]), np.array([0.0, 1, 2]))


def test_alternativa_invalida_erro_claro():
    with pytest.raises(ValueError, match="alternativa inválida"):
        t_pareado(np.array([1.0, 2, 3]), np.array([2.0, 1, 4]), alternativa="esquerda")


def test_grupo_com_um_valor_erro_de_dados():
    with pytest.raises(ErroDeDados):
        t_independente([1.0], [2.0, 3.0, 4.0], variancias_iguais=True)
