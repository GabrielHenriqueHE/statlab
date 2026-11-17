"""Aceitação: descritiva, outliers, correlação (Pearson/Spearman) e tabela A.6, contra o PDF e o gabarito."""

import numpy as np
import pytest
from scipy import stats

from statlab.core.correlacao import analisar_correlacao, forca, pearson, r_critico, spearman
from statlab.core.dados import ErroDeDados
from statlab.core.descritiva import METODO_QUARTIS_MINITAB, descrever, detectar_outliers, quartis
from tests.helpers import aprox, gabarito, p_menor_que, pdf

# --------------------------------------------------------------------------- descritiva e quartis


def test_quartis_excel_batem_com_o_gabarito_ex1():
    x = np.array([15, 40, 31, 25, 25, 48, 55, 15, 41], float)
    assert quartis(x) == (25.0, 41.0)  # gabarito: Q1 = 25,00; Q3 = 41,00


def test_quartis_produtividade_do_exemplo_grafico_pdf():
    """PDF 2.7: Q1 = 7116,5; Q3 = 9867,25; D = 2750,75 (produtividade, 40 pares)."""
    prod = np.array([p for p in pdf()["ex3_atendimento"]["y"] if p is not None], float)
    q1, q3 = quartis(prod)
    aprox(q1, 7116.5, 1)
    aprox(q3, 9867.25, 2)
    aprox(q3 - q1, 2750.75, 2)


def test_outlier_suave_da_produtividade_pdf_2_7():
    """PDF: o valor 1.100 (5 min) é outlier suave; limite inferior Q1 − 1,5D = 2990,4; extremo não existe."""
    prod = np.array([p for p in pdf()["ex3_atendimento"]["y"] if p is not None], float)
    out = detectar_outliers(prod)
    assert out.tem_suave
    assert not out.tem_extremo
    assert prod[out.suave].tolist() == [1100.0]
    aprox(out.q1 - 1.5 * out.d, 2990.4, 1)


def test_descritiva_equipe_a_gabarito_ex3():
    d = descrever(np.array(gabarito()["ex3"]["a"], float))
    aprox(d.media, 36.67, 2)
    aprox(d.mediana, 36.5, 1)
    aprox(d.dp, 7.28, 2)
    aprox(d.variancia, 53.07, 2)


def test_quartil_minitab_e_diferente_do_excel_documentado():
    x = np.array([15, 40, 31, 25, 25, 48, 55, 15, 41], float)
    assert quartis(x, METODO_QUARTIS_MINITAB) == (20.0, 44.5)
    assert quartis(x) != quartis(x, METODO_QUARTIS_MINITAB)


def test_gabarito_ex1_y_tem_outlier_suave_16():
    g = gabarito()["ex1"]
    out = detectar_outliers(np.array(g["y"], float))
    assert np.array(g["y"], float)[out.suave].tolist() == [16.0]
    assert not out.tem_extremo


# --------------------------------------------------------------------------- correlação: primitivas


def test_pearson_formula_igual_ao_scipy():
    rng = np.random.default_rng(0)
    x = rng.normal(size=30)
    y = 0.6 * x + rng.normal(size=30)
    r, p = pearson(x, y)
    ref = stats.pearsonr(x, y)
    aprox(r, float(ref.statistic), 10)
    aprox(p, float(ref.pvalue), 8)


def test_spearman_usa_postos():
    rs, p = spearman(np.array([1.0, 2, 3, 4, 5]), np.array([2.0, 1, 4, 3, 5]))
    ref = stats.spearmanr([1, 2, 3, 4, 5], [2, 1, 4, 3, 5])
    aprox(rs, float(ref.statistic), 10)
    aprox(p, float(ref.pvalue), 8)


# --------------------------------------------------------------------------- tabela A.6


# Tabela A.6 do PDF (imagem da apostila): n → (α = 0,05, α = 0,01). n = 4, α = 0,01 corrigido para 0,990.
TABELA_A6 = {
    4: (0.950, 0.990),
    5: (0.878, 0.959),
    6: (0.811, 0.917),
    7: (0.754, 0.875),
    8: (0.707, 0.834),
    9: (0.666, 0.798),
    10: (0.632, 0.765),
    11: (0.602, 0.735),
    12: (0.576, 0.708),
    13: (0.553, 0.684),
    14: (0.532, 0.661),
    15: (0.514, 0.641),
    16: (0.497, 0.623),
    17: (0.482, 0.606),
    18: (0.468, 0.590),
    19: (0.456, 0.575),
    20: (0.444, 0.561),
    25: (0.396, 0.505),
    30: (0.361, 0.463),
    35: (0.335, 0.430),
    40: (0.312, 0.402),
    45: (0.294, 0.378),
    50: (0.279, 0.361),
    60: (0.254, 0.330),
    70: (0.236, 0.305),
    80: (0.220, 0.286),
    90: (0.207, 0.269),
    100: (0.196, 0.256),
}


# Entradas do livro que NÃO batem com a fórmula à precisão de impressão (diferença > 0,0005).
# A fórmula é a declarada pelo próprio PDF (r_c = t / √(t² + n − 2)); o livro admite diferenças
# "de até cerca de 0,002, por arredondamento". Ficam registradas aqui, não ajustadas no código.
DIVERGENCIAS_LIVRO_A6 = {
    (35, 0.05): 0.00116,
    (40, 0.01): 0.00064,
    (45, 0.01): 0.00214,
    (70, 0.05): 0.00080,
    (70, 0.01): 0.00096,
    (90, 0.01): 0.00122,
    (100, 0.05): 0.00055,
}


@pytest.mark.parametrize("n", sorted(TABELA_A6))
def test_r_critico_bate_com_tabela_a6(n):
    r05, r01 = TABELA_A6[n]
    for alpha, livro in ((0.05, r05), (0.01, r01)):
        obtido = r_critico(n, alpha)
        if (n, alpha) in DIVERGENCIAS_LIVRO_A6:
            # divergência conhecida do livro: confere o limite declarado pelo PDF (≈ 0,002)
            assert abs(obtido - livro) <= 0.0025, f"n={n}, α={alpha}: {obtido:.5f} vs {livro}"
        else:
            aprox(obtido, livro, 3)


def test_r_critico_n4_alpha01_e_0990_nao_0999():
    """O livro imprime 0,999; o cálculo pela fórmula dá 0,990 (correção documentada no PDF)."""
    aprox(r_critico(4, 0.01), 0.990, 3)


def test_r_critico_exige_n_minimo():
    with pytest.raises(ErroDeDados):
        r_critico(2)


@pytest.mark.parametrize(
    "r, classe",
    [
        (0.0, "bem fraca"),
        (0.19, "bem fraca"),
        (0.2, "fraca"),
        (-0.39, "fraca"),
        (0.4, "moderada"),
        (0.69, "moderada"),
        (0.7, "forte"),
        (-0.89, "forte"),
        (0.9, "muito forte"),
        (-1.0, "muito forte"),
    ],
)
def test_forca_da_correlacao(r, classe):
    assert forca(r) == classe


# --------------------------------------------------------------------------- exemplos resolvidos do PDF


def test_pdf_ex1_publicidade_faturamento():
    """PDF 2.5: r = 0,975; p = 0,0047; r² = 0,951; normalidade x p = 0,967 e y p = 0,606."""
    d = pdf()["ex1_publicidade"]
    c = analisar_correlacao(d["x"], d["y"], nome_x="Investimento", nome_y="Faturamento")
    assert c.metodo == "Pearson"
    aprox(c.r, 0.975, 3)
    aprox(c.p, 0.0047, 4)
    aprox(c.r2, 0.951, 3)
    assert c.n == 5
    assert c.significativo and c.nivel_confianca == 99
    assert c.forca == "muito forte"
    aprox(c.r_critico_5, 0.878, 3)
    aprox(c.r_critico_1, 0.959, 3)


def test_pdf_ex1_normalidade_p_valores():
    d = pdf()["ex1_publicidade"]
    c = analisar_correlacao(d["x"], d["y"])
    assert any("0,967" in t for t in c.prerequisitos), c.prerequisitos
    assert any("0,606" in t for t in c.prerequisitos), c.prerequisitos


def test_pdf_ex2_treinamento_erros_negativa():
    """PDF 2.6: r = −0,988; r² = 0,977; p < 0,001; normalidade x p = 0,432, y p = 0,853."""
    d = pdf()["ex2_treinamento"]
    c = analisar_correlacao(d["x"], d["y"])
    aprox(c.r, -0.988, 3)
    aprox(c.r2, 0.977, 3)
    p_menor_que(c.p)
    assert c.forca == "muito forte"
    assert c.nivel_confianca == 99
    assert any("0,432" in t for t in c.prerequisitos)
    assert any("0,853" in t for t in c.prerequisitos)


def test_pdf_ex3_atendimento_quando_o_r_engana():
    """PDF 2.7: n = 40 pares; r = −0,029 (p = 0,857); Spearman rs = 0,005 (p = 0,977); sem outlier r = −0,210."""
    d = pdf()["ex3_atendimento"]
    c = analisar_correlacao(d["x"], d["y"], nome_x="Tempo", nome_y="Produtividade")
    assert c.n == 40
    assert c.n_extremos_excluidos == 0
    assert c.metodo == "Spearman"  # tempo não é normal (p = 0,015)
    aprox(c.r, -0.029, 3)
    aprox(c.p_pearson, 0.857, 3)
    aprox(c.r_s, 0.005, 3)
    aprox(c.p_spearman, 0.977, 3)
    assert not c.significativo
    assert c.forca is None  # força só se significativo
    # sem o outlier suave (n = 39): a análise usa o mesmo método da principal (Spearman) → PDF tabela 4
    assert c.n_sem_suave == 39
    aprox(c.r_sem_suave, -0.073, 3)
    aprox(c.p_sem_suave, 0.657, 3)
    assert c.conclusao_muda is False


def test_pdf_ex3_pearson_sem_outlier_r_menos_0210():
    """PDF tabela 4: sem o outlier (n = 39), Pearson r = −0,210 e p = 0,200."""
    d = pdf()["ex3_atendimento"]
    pares_ok = [(a, b) for a, b in zip(d["x"], d["y"], strict=True) if b is not None and b != 1100.0]
    x = np.array([a for a, _ in pares_ok], float)
    y = np.array([b for _, b in pares_ok], float)
    r, p = pearson(x, y)
    aprox(r, -0.210, 3)
    aprox(p, 0.200, 3)


def test_pdf_ex3_normalidade_com_e_sem_outlier():
    from statlab.core.normalidade import shapiro_wilk

    d = pdf()["ex3_atendimento"]
    # o PDF calcula a normalidade sobre os 40 pares (não sobre os 46 tempos): p = 0,015
    pares_ok = [(a, b) for a, b in zip(d["x"], d["y"], strict=True) if b is not None]
    x = np.array([a for a, _ in pares_ok], float)
    y = np.array([b for _, b in pares_ok], float)
    aprox(shapiro_wilk(x, tcl=False).p, 0.015, 3)
    aprox(shapiro_wilk(y, tcl=False).p, 0.007, 3)
    m = y != 1100.0
    aprox(shapiro_wilk(y[m], tcl=False).p, 0.105, 3)


# --------------------------------------------------------------------------- gabarito 2026: correlação


def test_gabarito_ex1_pearson_nao_significativo_e_com_outlier_muda():
    g = gabarito()["ex1"]
    c = analisar_correlacao(g["x"], g["y"])
    assert c.metodo == "Pearson"
    aprox(c.r, 0.095, 3)
    aprox(c.p, 0.808, 3)
    assert not c.significativo
    aprox(c.r_s, 0.438, 3)
    aprox(c.p_spearman, 0.239, 3)
    # sem o outlier suave (y = 16): n = 8, r = 0,972, p < 0,001 → conclusão muda
    assert c.n_sem_suave == 8
    aprox(c.r_sem_suave, 0.972, 3)
    p_menor_que(c.p_sem_suave)
    assert c.conclusao_muda is True


def test_gabarito_ex9_correlacao_forte():
    g = gabarito()["ex9"]
    c = analisar_correlacao(g["x"], g["y"])
    assert c.metodo == "Pearson"
    aprox(c.r, 0.960, 3)
    aprox(c.r_s, 0.942, 3)
    aprox(c.r2 * 100, 92.1, 1)
    assert c.nivel_confianca == 99
    assert c.forca == "muito forte"


# --------------------------------------------------------------------------- bordas


def test_correlacao_com_coluna_constante_erro_de_dados():
    with pytest.raises(ErroDeDados, match="todos os valores são iguais"):
        analisar_correlacao([1, 1, 1, 1], [1, 2, 3, 4])


def test_correlacao_com_menos_de_3_pares_erro_de_dados():
    with pytest.raises(ErroDeDados, match="pelo menos 3"):
        analisar_correlacao([1, 2], [3, 4])


def test_correlacao_faltantes_viram_aviso():
    c = analisar_correlacao([1, 2, None, 4, 5, 6, 7], [2, 4, 6, 8, 10, 12, None])
    assert c.n == 5
    assert any("descartados" in a for a in c.avisos)
