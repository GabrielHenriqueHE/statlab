"""F3 (interface): as páginas de testes mostram os mesmos números do gabarito 2026 e do PDF.

Cada página roda no AppTest com uma worksheet montada a partir das fixtures.
"""

import numpy as np
import pytest
from scipy import stats
from streamlit.testing.v1 import AppTest

from statlab.core.formatacao import num
from tests.helpers import gabarito, pdf
from tests.ui_util import UI, app, metrica, sem_erros, worksheet

PAGINAS_DE_TESTE = [
    "normalidade.py",
    "uma_amostra.py",
    "dois_grupos.py",
    "pareado.py",
    "anova.py",
    "proporcoes.py",
    "qui_quadrado.py",
    "correlacao.py",
]


@pytest.mark.parametrize("pagina", PAGINAS_DE_TESTE)
def test_pagina_sem_worksheet_orienta_sem_quebrar(pagina):
    at = app(pagina)
    sem_erros(at)
    assert at.info or at.metric, f"{pagina}: sem orientação nem resultado"


def test_app_completo_abre_com_navegacao_e_alpha():
    at = AppTest.from_file(str(UI / "app.py"), default_timeout=60).run()
    sem_erros(at)
    assert at.sidebar.radio(key="alpha_global").value == 0.05


# --------------------------------------------------------------------------- dois grupos (gabarito Ex. 3)


def test_dois_grupos_gabarito_ex3():
    g = gabarito()["ex3"]
    at = app("dois_grupos.py", {"Ex3": worksheet(**{"Equipe A": g["a"], "Equipe B": g["b"]})})
    sem_erros(at)
    assert metrica(at, "t") == "1,473"
    assert metrica(at, "gl") == "17"
    assert metrica(at, "p") == "0,159"
    assert any("Não significativo" in i.value for i in at.info)
    assert any("✅" in m.value and "Igualdade de variâncias" in m.value for m in at.markdown)


def test_dois_grupos_modo_empilhado_escolhe_dois_niveis():
    g = gabarito()["ex3"]
    import pandas as pd

    longa = pd.DataFrame({"Tempo": g["a"] + g["b"], "Equipe": ["A"] * len(g["a"]) + ["B"] * len(g["b"])})
    at = app("dois_grupos.py", {"Longa": longa})
    at.radio(key="g2_modo").set_value("Resposta em uma coluna e grupo em outra").run()
    sem_erros(at)
    assert metrica(at, "t") == "1,473"


def test_dois_grupos_aba_variancias_teste_f():
    d = pdf()["ex5_apf"]
    at = app("dois_grupos.py", {"APF": worksheet(G1=d["g1"], G2=d["g2"])})
    sem_erros(at)
    assert metrica(at, "F") == "1,277"  # PDF: F = 1,277; p = 0,774
    assert "0,774" in [m.value for m in at.metric]


# --------------------------------------------------------------------------- pareado (gabarito Ex. 2)


def test_pareado_gabarito_ex2_bilateral_e_unilateral():
    g = gabarito()["ex2"]
    at = app("pareado.py", {"Ex2": worksheet(Antes=g["antes"], Depois=g["depois"])})
    sem_erros(at)
    assert metrica(at, "t").startswith("4,07")
    assert metrica(at, "p") == "0,002"
    at.radio(key="par_alt").set_value("Maior (unilateral)").run()
    sem_erros(at)
    assert metrica(at, "p") == "< 0,001"
    assert any("99% de confiança" in s.value for s in at.success)


def test_pareado_mesma_coluna_pede_outra():
    g = gabarito()["ex2"]
    at = app("pareado.py", {"Ex2": worksheet(Antes=g["antes"], Depois=g["depois"])})
    at.selectbox(key="par_depois").set_value("Antes").run()
    sem_erros(at)
    assert any("colunas diferentes" in i.value for i in at.info)


# --------------------------------------------------------------------------- ANOVA (gabarito Ex. 4 e PDF 8.3)


def test_anova_gabarito_ex4_usa_todas_as_colunas_por_padrao():
    g = gabarito()["ex4"]
    at = app("anova.py", {"Ex4": worksheet(manha=g["manha"], tarde=g["tarde"], noite=g["noite"])})
    sem_erros(at)
    assert metrica(at, "F") == "1,732"
    assert metrica(at, "p") == "0,183"
    assert metrica(at, "gl") == "2; 93"
    assert any("comparações 2 a 2 não são necessárias" in c.value for c in at.caption)


def test_anova_pdf_forca_mostra_tukey_tabela_e_grafico():
    d = pdf()["ex6_forca"]
    at = app("anova.py", {"Força": worksheet(G1=d["g1"], G2=d["g2"], G3=d["g3"])})
    sem_erros(at)
    assert metrica(at, "F").startswith("8,70")  # PDF 8.3: F = 8,70
    comparacoes = at.dataframe[1].value
    assert list(comparacoes["Par"]) == ["G1 − G2", "G1 − G3", "G2 − G3"]
    assert list(comparacoes["Diferem?"]) == ["sim", "sim", "não"]
    assert len(at.get("plotly_chart")) == 3  # Tukey, intervalos e boxplot


def test_anova_pdf_resistencia_kruskal_mostra_medianas_e_bonferroni():
    d = pdf()["ex7_resistencia"]
    at = app("anova.py", {"Resist": worksheet(G1=d["g1"], G2=d["g2"], G3=d["g3"])})
    sem_erros(at)
    assert metrica(at, "H").startswith("29,3")
    assert any("Bonferroni" in w.value for w in at.warning)
    assert any("❌" in m.value for m in at.markdown)


# --------------------------------------------------------------------------- proporções (gabarito Ex. 6)


def test_proporcoes_gabarito_ex6_valores_padrao():
    at = app("proporcoes.py")
    sem_erros(at)
    assert metrica(at, "p") == "0,047"
    assert metrica(at, "z") == "-1,989"
    assert "0,5000" in [m.value for m in at.metric]


def test_proporcoes_a_partir_de_colunas():
    import pandas as pd

    df = pd.DataFrame(
        {"Resultado": ["sim"] * 31 + ["não"] * 31 + ["sim"] * 117 + ["não"] * 65, "Turma": ["com"] * 62 + ["sem"] * 182}
    )
    at = app("proporcoes.py", {"Turmas": df})
    at.radio(key="pr_modo").set_value("A partir de colunas da worksheet").run()
    sem_erros(at)
    assert metrica(at, "p") == "0,047"


# --------------------------------------------------------------------------- correlação (gabarito Ex. 9 e Ex. 1)


def test_correlacao_gabarito_ex9_e_regressao_com_previsao():
    g = gabarito()["ex9"]
    at = app("correlacao.py", {"Ex9": worksheet(Commits=g["x"], Bugs=g["y"])})
    sem_erros(at)
    assert metrica(at, "r (Pearson)") == "0,960"
    assert metrica(at, "Força") == "muito forte"
    assert any("ŷ = 0,1585·x + 1,763" in m.value for m in at.markdown)
    at.number_input(key="reg_x0").set_value(32.0).run()
    assert metrica(at, "ŷ para Commits = 32,00").startswith("6,8")


def test_correlacao_gabarito_ex1_sem_correlacao_nao_faz_regressao():
    g = gabarito()["ex1"]
    at = app("correlacao.py", {"Ex1": worksheet(Commits=g["x"], Bugs=g["y"])})
    sem_erros(at)
    assert any("não deve ser feita" in i.value for i in at.info)
    assert any("conclusão muda" in w.value.lower() for w in at.warning)
    at.checkbox(key="reg_forcar").check().run()
    assert any("NÃO significativa" in w.value for w in at.warning)


def test_correlacao_extrapolacao_avisa():
    d = pdf()["ex1_publicidade"]
    at = app("correlacao.py", {"Pub": worksheet(Invest=d["x"], Fat=d["y"])})
    at.number_input(key="reg_x0").set_value(0.0).run()
    assert any("extrapolação" in w.value for w in at.warning)


# --------------------------------------------------------------------------- uma amostra, normalidade, qui-quadrado


def test_uma_amostra_t_bate_com_scipy():
    x = np.random.default_rng(5).normal(52, 6, 25)
    at = app("uma_amostra.py", {"Amostra": worksheet(Peso=list(x))})
    at.number_input(key="t1_mu0").set_value(50.0).run()
    sem_erros(at)
    assert metrica(at, "t") == num(float(stats.ttest_1samp(x, 50).statistic), 3)


def test_uma_amostra_proporcao_sem_worksheet():
    at = app("uma_amostra.py")
    sem_erros(at)
    assert any("Uma proporção" in s.value for s in at.subheader)


def test_normalidade_mostra_os_dois_testes():
    g = gabarito()["ex9"]
    at = app("normalidade.py", {"Ex9": worksheet(Commits=g["x"], Bugs=g["y"])})
    at.multiselect(key="norm_vars").set_value(["Commits", "Bugs"]).run()
    sem_erros(at)
    tabela = at.dataframe[0].value
    assert list(tabela["p (Shapiro-Wilk)"]) == ["0,333", "0,419"]  # gabarito Ex. 9
    assert "p (Anderson-Darling)" in tabela.columns


def test_qui_quadrado_tabela_digitada_padrao():
    at = app("qui_quadrado.py")
    sem_erros(at)
    obs = np.array([[10, 30], [20, 40]])
    esperado = stats.chi2_contingency(obs, correction=False)[0]
    assert metrica(at, "χ²") == num(float(esperado), 3)
