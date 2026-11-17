"""Aceitação: ANOVA/Tukey/Kruskal-Wallis e proporções, contra o PDF (seções 8 e 9) e o gabarito 2026."""

import numpy as np
import pytest

from statlab.core.anova import analisar_grupos, anova_um_fator, tukey_hsd, welch_anova
from statlab.core.dados import ErroDeDados
from statlab.core.nao_parametricos import (
    comparacoes_mann_whitney_bonferroni,
    kruskal_wallis,
    mann_whitney,
    wilcoxon_pareado,
)
from statlab.core.proporcoes import analisar_proporcoes
from statlab.core.resultados import ParComparacao
from statlab.core.variancias import razao_maior_menor
from tests.helpers import aprox, gabarito, p_menor_que, pdf


def _cmp(comps: list[ParComparacao], a: str, b: str) -> ParComparacao:
    for c in comps:
        if {c.grupo_a, c.grupo_b} == {a, b}:
            return c
    raise AssertionError(f"par {a} × {b} não encontrado")


# --------------------------------------------------------------------------- ANOVA (PDF 8.3)


def _forca_grupos():
    d = pdf()["ex6_forca"]
    return {"G1": np.array(d["g1"], float), "G2": np.array(d["g2"], float), "G3": np.array(d["g3"], float)}


def test_pdf_ex6_anova_tabela():
    """PDF 8.3: SQ entre 4937,97; SQ dentro 23262,43; total 28200,40; F = 8,70; p = 0,0004; R² = 17,5%."""
    res = anova_um_fator(_forca_grupos())
    aprox(res.sq_entre, 4937.97, 2)
    aprox(res.sq_dentro, 23262.43, 2)
    aprox(res.sq_total, 28200.40, 2)
    aprox(res.estatistica, 8.70, 2)
    aprox(res.p, 0.0004, 4)
    assert res.gl == (2.0, 82.0)
    aprox(res.r2, 0.175, 3)


def test_pdf_ex6_pipeline_escolhe_anova_com_tukey_e_welch_conferencia():
    res = analisar_grupos(_forca_grupos())
    assert res.modelo == "ANOVA (1 fator)"
    aprox(res.estatistica, 8.70, 2)
    assert res.metodo_comparacoes == "Tukey HSD"
    assert "13,80" in res.conferencia  # ANOVA de Welch: F = 13,80
    welch_f, welch_p = welch_anova(_forca_grupos())
    aprox(welch_f, 13.80, 2)
    p_menor_que(welch_p)


def test_pdf_ex6_tukey_pares():
    comps = tukey_hsd(_forca_grupos())
    g12 = _cmp(comps, "G1", "G2")
    aprox(g12.diferenca, -12.68, 2)
    aprox(g12.p, 0.017, 3)
    aprox(g12.ic[0], -23.42, 2)
    aprox(g12.ic[1], -1.93, 2)
    g13 = _cmp(comps, "G1", "G3")
    aprox(g13.diferenca, -18.20, 2)
    p_menor_que(g13.p)
    aprox(g13.ic[0], -28.85, 2)
    aprox(g13.ic[1], -7.55, 2)
    g23 = _cmp(comps, "G2", "G3")
    aprox(g23.diferenca, -5.52, 2)
    aprox(g23.p, 0.435, 3)
    aprox(g23.ic[0], -16.17, 2)
    aprox(g23.ic[1], 5.13, 2)


# --------------------------------------------------------------------------- Kruskal-Wallis (PDF 8.4 e 8.5)


def _resistencia():
    d = pdf()["ex7_resistencia"]
    return {"G1": np.array(d["g1"], float), "G2": np.array(d["g2"], float), "G3": np.array(d["g3"], float)}


def test_pdf_ex7_kruskal_wallis_resistencia_escolhido_pelos_pre_requisitos():
    res = analisar_grupos(_resistencia())
    assert res.modelo == "Kruskal-Wallis"
    aprox(res.estatistica, 29.37, 2)
    assert res.gl == (2.0,)
    p_menor_que(res.p)
    assert res.nivel_confianca == 99
    assert res.medianas["G1"] == 283 and res.medianas["G3"] == 459
    assert res.metodo_comparacoes == "Mann-Whitney com Bonferroni"


def test_pdf_ex7_comparacoes_bonferroni():
    comps = comparacoes_mann_whitney_bonferroni(_resistencia())
    aprox(_cmp(comps, "G1", "G2").p, 1.0, 3)
    p_menor_que(_cmp(comps, "G1", "G3").p)
    p_menor_que(_cmp(comps, "G2", "G3").p)


def _grupos_8_5():
    d = pdf()["ex85_grupos_1_3"]
    return {"G1": np.array(d["g1"], float), "G2": np.array(d["g2"], float), "G3": np.array(d["g3"], float)}


def test_pdf_8_5_exercicio_proposto_gabarito():
    """PDF 8.5: médias 26,31; 35,79; 64,41; H = 41,66; ANOVA F = 43,00; Tukey G1×G2 p = 0,074."""
    g = _grupos_8_5()
    aprox(float(g["G1"].mean()), 26.31, 2)
    aprox(float(g["G2"].mean()), 35.79, 2)
    aprox(float(g["G3"].mean()), 64.41, 2)
    assert razao_maior_menor(list(g.values())) == pytest.approx(515.4 / 62.2, rel=2e-3)  # 8,28
    res = analisar_grupos(g)
    assert res.modelo == "Kruskal-Wallis"  # G2 não normal (p = 0,020) com n = 29
    aprox(res.estatistica, 41.66, 2)
    p_menor_que(res.p)
    aa = anova_um_fator(g)
    aprox(aa.estatistica, 43.00, 2)
    aprox(_cmp(tukey_hsd(g), "G1", "G2").p, 0.074, 3)


# --------------------------------------------------------------------------- gabarito 2026: grupos


def test_gabarito_ex4_anova_nao_significativa():
    g = gabarito()["ex4"]
    res = analisar_grupos({"manhã": g["manha"], "tarde": g["tarde"], "noite": g["noite"]})
    assert res.modelo == "ANOVA (1 fator)"
    aprox(res.estatistica, 1.732, 3)
    aprox(res.p, 0.183, 3)
    aprox(res.sq_entre, 558.40, 2)
    aprox(res.sq_dentro, 14987.59, 2)
    assert res.gl == (2.0, 93.0)
    assert res.comparacoes == []
    assert res.significativo is False


def test_gabarito_ex5_planilha_ja_sem_extremos_kruskal():
    g = gabarito()["ex5_planilha"]
    res = analisar_grupos({"manhã": g["manha"], "tarde": g["tarde"], "noite": g["noite"]})
    assert res.modelo == "Kruskal-Wallis"
    aprox(res.estatistica, 38.537, 3)
    p_menor_que(res.p)
    assert _cmp(res.comparacoes, "manhã", "tarde").p < 0.001
    assert _cmp(res.comparacoes, "manhã", "noite").p < 0.001
    aprox(_cmp(res.comparacoes, "tarde", "noite").p, 0.002, 3)


def test_gabarito_ex5_enunciado_bruto_exclui_37_e_38_e_chega_ao_mesmo_h():
    """Com o enunciado completo (19 na Turma tarde), os extremos 37 e 38 são excluídos e H é o mesmo."""
    g = gabarito()
    res = analisar_grupos(
        {
            "manhã": g["ex5_planilha"]["manha"],
            "tarde": g["enunciado_bruto"]["ex5_tarde"],
            "noite": g["ex5_planilha"]["noite"],
        }
    )
    aprox(res.estatistica, 38.537, 3)
    assert any("outlier extremo excluído" in a and "tarde" in a for a in res.avisos)


# --------------------------------------------------------------------------- proporções


def test_gabarito_ex6_z_bilateral_e_conferencia_fisher():
    g = gabarito()["ex6"]
    res = analisar_proporcoes(g["g1"][0], g["g1"][1], g["g2"][0], g["g2"][1], nome_1="com", nome_2="sem")
    assert res.nome == "Teste z de duas proporções"
    aprox(res.p1, 0.5000, 4)
    aprox(res.p2, 0.6429, 4)
    aprox(res.z, -1.989, 3)
    aprox(res.p, 0.047, 3)
    aprox(res.p_fisher, 0.052, 3)


def test_gabarito_ex8_z_muito_significativo():
    g = gabarito()["ex8"]
    res = analisar_proporcoes(g["a"][0], g["a"][1], g["b"][0], g["b"][1])
    aprox(res.z, -3.449, 3)
    p_menor_que(res.p)
    p_menor_que(res.p_fisher)
    assert res.nivel_confianca == 99


def test_proporcoes_pre_requisito_falho_usa_fisher():
    res = analisar_proporcoes(2, 10, 5, 12)  # n·p·q = 1,6 e 2,9 < 5
    assert res.nome == "Teste exato de Fisher"
    assert res.z is None
    assert res.p is not None and 0 < res.p <= 1


def test_proporcoes_ocorrencias_fora_do_total_erro():
    with pytest.raises(ErroDeDados, match="entre 0 e o total"):
        analisar_proporcoes(12, 10, 3, 9)


# --------------------------------------------------------------------------- Mann-Whitney / Wilcoxon (gabarito ex10)


def test_gabarito_ex10_wilcoxon_com_extremo_excluido_e_unilateral_aumentou():
    g = gabarito()
    antes = np.array(g["enunciado_bruto"]["ex10_antes"], float)
    depois = np.array(g["enunciado_bruto"]["ex10_depois"], float)
    from statlab.core.testes_t import analisar_antes_depois

    res = analisar_antes_depois(antes, depois, alternativa="menor")
    assert res.nome == "Wilcoxon (pareado)"
    assert res.n == 16  # o par (58; 100), d = −42, é o outlier extremo
    assert res.estatistica == 0.0  # W = 0
    p_menor_que(res.p)
    assert any("Sem o(s) outlier(s) suave(s)" in a for a in res.avisos)


def test_gabarito_ex10_planilha_mesmo_resultado():
    g = gabarito()["ex10_planilha"]
    from statlab.core.testes_t import analisar_antes_depois

    res = analisar_antes_depois(g["antes"], g["depois"], alternativa="menor")
    assert res.estatistica == 0.0
    p_menor_que(res.p)


def test_wilcoxon_todas_diferencas_zero_erro():
    with pytest.raises(ErroDeDados):
        wilcoxon_pareado(np.array([1.0, 2]), np.array([1.0, 2]))


def test_mann_whitney_direcao_e_mediana():
    res = mann_whitney(np.array([10.0, 11, 12, 13]), np.array([1.0, 2, 3, 4]), alternativa="maior")
    assert res.medianas and res.p is not None
    p_menor_que(res.p, 0.05)


def test_kruskal_gl_e_medianas():
    res = kruskal_wallis({"a": np.array([1.0, 2, 3]), "b": np.array([4.0, 5, 6]), "c": np.array([7.0, 8, 9])})
    assert res.gl == (2.0,)
    assert set(res.medianas) == {"a", "b", "c"}


def test_analisar_grupos_exige_dois_grupos():
    with pytest.raises(ErroDeDados):
        analisar_grupos({"unico": [1, 2, 3, 4]})


# --------------------------------------------------------------------------- bordas (plano: F1)


def test_grupo_vazio_erro_de_dados():
    with pytest.raises(ErroDeDados, match="pelo menos 3"):
        analisar_grupos({"a": [1.0, 2, 3, 4], "vazio": [None, ""]})


def test_grupo_com_valor_textual_invalido_erro_com_nome_do_grupo():
    with pytest.raises(ErroDeDados, match="Grupo B"):
        analisar_grupos({"Grupo A": [1.0, 2, 3], "Grupo B": [1.0, "x", 3]})


def test_grupo_constante_erro_de_dados():
    with pytest.raises(ErroDeDados, match="todos os valores são iguais"):
        analisar_grupos({"a": [5.0, 5, 5, 5], "b": [1.0, 2, 3, 4]})


def test_shapiro_com_menos_de_3_observacoes_erro_de_dados():
    from statlab.core.normalidade import shapiro_wilk

    with pytest.raises(ErroDeDados, match="pelo menos 3"):
        shapiro_wilk(np.array([1.0, 2.0]))


def test_anova_faltantes_viram_aviso_e_nao_quebram():
    res = analisar_grupos({"a": [1.0, 2, None, 4, 3], "b": [5.0, 6, 7, None, 8, 6]})
    assert any("faltante" in a for a in res.avisos)
    assert res.n == 9
