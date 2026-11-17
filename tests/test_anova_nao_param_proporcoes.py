"""Aceitação: ANOVA/Tukey/Kruskal-Wallis e proporções, contra o PDF (seções 8 e 9) e o gabarito 2026."""

import numpy as np
import pytest

from statlab.core.anova import anova_um_fator, tukey_hsd, welch_anova
from statlab.core.dados import ErroDeDados
from statlab.core.nao_parametricos import (
    comparacoes_mann_whitney_bonferroni,
    kruskal_wallis,
    mann_whitney,
    wilcoxon_pareado,
)
from statlab.core.proporcoes import fisher_duas_proporcoes, z_duas_proporcoes
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


def test_pdf_ex6_welch_anova_e_comando_proprio():
    """A ANOVA de Welch é uma opção, não uma conferência que o app roda sozinho: F = 13,80."""
    welch_f, welch_p = welch_anova(_forca_grupos())
    aprox(welch_f, 13.80, 2)
    p_menor_que(welch_p)
    res = anova_um_fator(_forca_grupos())
    aprox(res.estatistica, 8.70, 2)
    assert res.comparacoes == []  # o Tukey só sai se for pedido


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


def test_pdf_ex7_kruskal_wallis_resistencia():
    res = kruskal_wallis(_resistencia())
    aprox(res.estatistica, 29.37, 2)
    assert res.gl == (2.0,)
    p_menor_que(res.p)
    assert res.nivel_confianca == 99
    assert res.medianas["G1"] == 283 and res.medianas["G3"] == 459


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
    res = kruskal_wallis(g)
    aprox(res.estatistica, 41.66, 2)
    p_menor_que(res.p)
    aa = anova_um_fator(g)
    aprox(aa.estatistica, 43.00, 2)
    aprox(_cmp(tukey_hsd(g), "G1", "G2").p, 0.074, 3)


# --------------------------------------------------------------------------- gabarito 2026: grupos


def test_gabarito_ex4_anova_nao_significativa():
    g = gabarito()["ex4"]
    res = anova_um_fator({"manhã": g["manha"], "tarde": g["tarde"], "noite": g["noite"]})
    aprox(res.estatistica, 1.732, 3)
    aprox(res.p, 0.183, 3)
    aprox(res.sq_entre, 558.40, 2)
    aprox(res.sq_dentro, 14987.59, 2)
    assert res.gl == (2.0, 93.0)
    assert res.comparacoes == []
    assert res.significativo is False


def test_gabarito_ex5_planilha_ja_sem_extremos_kruskal():
    g = gabarito()["ex5_planilha"]
    grupos = {"manhã": g["manha"], "tarde": g["tarde"], "noite": g["noite"]}
    res = kruskal_wallis(grupos)
    aprox(res.estatistica, 38.537, 3)
    p_menor_que(res.p)
    assert res.comparacoes == []  # as comparações 2 a 2 são um pedido à parte
    comps = comparacoes_mann_whitney_bonferroni(grupos)
    assert _cmp(comps, "manhã", "tarde").p < 0.001
    assert _cmp(comps, "manhã", "noite").p < 0.001
    aprox(_cmp(comps, "tarde", "noite").p, 0.002, 3)


def test_gabarito_ex5_enunciado_bruto_nao_perde_os_extremos():
    """Com o enunciado completo (19 na Turma tarde), os extremos 37 e 38 PERMANECEM: o app não exclui."""
    g = gabarito()
    tarde_bruta = g["enunciado_bruto"]["ex5_tarde"]
    assert 37 in tarde_bruta and 38 in tarde_bruta
    grupos = {
        "manhã": g["ex5_planilha"]["manha"],
        "tarde": tarde_bruta,
        "noite": g["ex5_planilha"]["noite"],
    }
    res = kruskal_wallis(grupos)
    assert res.n == sum(len(v) for v in grupos.values())
    assert res.avisos == []
    # excluindo os extremos na mão, chega-se ao H da planilha do gabarito
    sem = dict(grupos, tarde=[v for v in tarde_bruta if v not in (37, 38)])
    aprox(kruskal_wallis(sem).estatistica, 38.537, 3)


# --------------------------------------------------------------------------- proporções


def test_gabarito_ex6_z_bilateral_e_conferencia_fisher():
    g = gabarito()["ex6"]
    res = z_duas_proporcoes(g["g1"][0], g["g1"][1], g["g2"][0], g["g2"][1], nome_1="com", nome_2="sem")
    assert res.nome == "Teste z de duas proporções"
    aprox(res.p1, 0.5000, 4)
    aprox(res.p2, 0.6429, 4)
    aprox(res.z, -1.989, 3)
    aprox(res.p, 0.047, 3)
    fisher = fisher_duas_proporcoes(g["g1"][0], g["g1"][1], g["g2"][0], g["g2"][1])
    aprox(fisher.p, 0.052, 3)


def test_gabarito_ex8_z_muito_significativo():
    g = gabarito()["ex8"]
    res = z_duas_proporcoes(g["a"][0], g["a"][1], g["b"][0], g["b"][1])
    aprox(res.z, -3.449, 3)
    p_menor_que(res.p)
    p_menor_que(fisher_duas_proporcoes(g["a"][0], g["a"][1], g["b"][0], g["b"][1]).p)
    assert res.nivel_confianca == 99


def test_proporcoes_criterio_falho_vira_diagnostico_nao_troca_de_teste():
    """n·p·q = 1,6 e 2,9 < 5: o z ainda roda se for pedido, com o diagnóstico em ⚠️."""
    z = z_duas_proporcoes(2, 10, 5, 12)
    assert z.nome == "Teste z de duas proporções"
    assert [v.status for v in z.verificacoes] == ["atencao", "atencao"]
    f = fisher_duas_proporcoes(2, 10, 5, 12)
    assert f.nome == "Teste exato de Fisher"
    assert f.p is not None and 0 < f.p <= 1


def test_proporcoes_ocorrencias_fora_do_total_erro():
    with pytest.raises(ErroDeDados, match="entre 0 e o total"):
        z_duas_proporcoes(12, 10, 3, 9)


# --------------------------------------------------------------------------- Mann-Whitney / Wilcoxon (gabarito ex10)


def test_gabarito_ex10_enunciado_bruto_mantem_o_par_extremo():
    """O par (58; 100), d = −42, é outlier extremo — e continua na análise, porque ninguém o excluiu."""
    g = gabarito()
    antes = np.array(g["enunciado_bruto"]["ex10_antes"], float)
    depois = np.array(g["enunciado_bruto"]["ex10_depois"], float)
    res = wilcoxon_pareado(antes, depois, alternativa="menor")
    assert res.n == len(antes) == 17
    assert res.avisos == []


def test_gabarito_ex10_planilha_sem_o_extremo_da_w_zero():
    """A planilha do gabarito já vem sem o par extremo: W = 0 e p < 0,001 (unilateral)."""
    g = gabarito()["ex10_planilha"]
    res = wilcoxon_pareado(np.array(g["antes"], float), np.array(g["depois"], float), alternativa="menor")
    assert res.n == 16
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


def test_anova_exige_dois_grupos():
    with pytest.raises(ErroDeDados):
        anova_um_fator({"unico": [1, 2, 3, 4]})


# --------------------------------------------------------------------------- bordas (plano: F1)


def test_grupo_vazio_erro_de_dados():
    with pytest.raises(ErroDeDados, match="pelo menos 2 observações"):
        anova_um_fator({"a": [1.0, 2, 3, 4], "vazio": [None, ""]})


def test_grupo_com_valor_textual_invalido_erro_com_nome_do_grupo():
    with pytest.raises(ErroDeDados, match="Grupo B"):
        anova_um_fator({"Grupo A": [1.0, 2, 3], "Grupo B": [1.0, "x", 3]})


def test_grupo_constante_e_valido_se_houver_variacao_dentro():
    """Um grupo sem variação não impede a ANOVA; o que impede é não haver variação em nenhum."""
    res = anova_um_fator({"a": [5.0, 5, 5, 5], "b": [1.0, 2, 3, 4]})
    assert res.p is not None
    with pytest.raises(ErroDeDados, match="Não há variação dentro dos grupos"):
        anova_um_fator({"a": [5.0, 5, 5], "b": [1.0, 1, 1]})


def test_shapiro_com_menos_de_3_observacoes_erro_de_dados():
    from statlab.core.normalidade import shapiro_wilk

    with pytest.raises(ErroDeDados, match="pelo menos 3"):
        shapiro_wilk(np.array([1.0, 2.0]))


def test_anova_faltantes_viram_aviso_e_nao_quebram():
    res = anova_um_fator({"a": [1.0, 2, None, 4, 3], "b": [5.0, 6, 7, None, 8, 6]})
    assert any("faltante" in a for a in res.avisos)
    assert res.n == 9
