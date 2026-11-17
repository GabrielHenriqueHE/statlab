"""F4: assistente 'Qual teste usar?' — árvore de decisão e os casos da apostila e do gabarito."""

import numpy as np
import pandas as pd
import pytest

from statlab.core import assistente
from tests.helpers import gabarito, pdf
from tests.ui_util import app, sem_erros, worksheet

# --------------------------------------------------------------------------- árvore (sem dados)


@pytest.mark.parametrize(
    "objetivo, respostas, esperado",
    [
        ("relacao", {"normal": True}, "Correlação de Pearson"),
        ("relacao", {"normal": False, "n_grande": True}, "Correlação de Spearman"),  # sem atalho do TCL
        ("dois_grupos", {"normal": True, "variancias_iguais": True}, "t independente (variância combinada)"),
        ("dois_grupos", {"normal": True, "variancias_iguais": False}, "t de Welch"),
        (
            "dois_grupos",
            {"normal": False, "n_grande": True, "variancias_iguais": True},
            "t independente (variância combinada)",
        ),
        ("dois_grupos", {"normal": False}, "Mann-Whitney"),
        ("pareado", {"normal": True}, "t pareado"),
        ("pareado", {"normal": False}, "Wilcoxon"),
        ("pareado", {"normal": False, "n_grande": True}, "t pareado"),
        ("tres_grupos", {"normal": True, "razao_ate_9": True}, "ANOVA de 1 fator (+ Tukey se significativa)"),
        ("tres_grupos", {"normal": True, "razao_ate_9": False}, "Kruskal-Wallis (+ comparações 2 a 2)"),
        ("tres_grupos", {"normal": False}, "Kruskal-Wallis (+ comparações 2 a 2)"),
        ("proporcoes", {"npq_ok": True}, "Teste de duas proporções (z)"),
        ("proporcoes", {"npq_ok": False}, "Exato de Fisher"),
        ("associacao", {"esperados_ok": True}, "Qui-quadrado de independência"),
        ("associacao", {"esperados_ok": False, "tabela_2x2": True}, "Exato de Fisher (tabela 2 × 2)"),
        ("uma_amostra", {"normal": True}, "t para uma amostra"),
        ("uma_amostra", {"normal": False}, "Wilcoxon para uma amostra"),
    ],
)
def test_arvore_de_decisao(objetivo, respostas, esperado):
    d = assistente.decidir(objetivo, **respostas)
    assert d.teste == esperado
    assert d.pendencias == []
    assert d.caminho[0].startswith("Objetivo:")


@pytest.mark.parametrize(
    "objetivo, respostas, trecho",
    [
        ("relacao", {}, "Normalidade"),
        ("dois_grupos", {}, "Normalidade"),
        ("dois_grupos", {"normal": True}, "variâncias"),
        ("tres_grupos", {"normal": True}, "razão"),
        ("proporcoes", {}, "n·p·q"),
        ("associacao", {}, "esperadas"),
    ],
)
def test_arvore_nao_sei_vira_pendencia(objetivo, respostas, trecho):
    d = assistente.decidir(objetivo, **respostas)
    assert d.teste is None
    assert any(trecho in p for p in d.pendencias)


def test_arvore_tabela_grande_com_esperados_pequenos_pede_agrupar():
    d = assistente.decidir("associacao", esperados_ok=False, tabela_2x2=False)
    assert d.teste is None
    assert "agrupe categorias" in d.caminho[-1]


def test_objetivo_desconhecido():
    with pytest.raises(ValueError):
        assistente.decidir("regressao_logistica")


# --------------------------------------------------------------------------- com os dados: casos da apostila


def _grupos(d: dict, nomes=("g1", "g2", "g3")) -> dict:
    return {n.upper(): d[n] for n in nomes}


@pytest.mark.parametrize(
    "caso, objetivo, argumentos, teste",
    [
        (
            "PDF 2.5 publicidade",
            "relacao",
            lambda: dict(x=pdf()["ex1_publicidade"]["x"], y=pdf()["ex1_publicidade"]["y"]),
            "Correlação de Pearson",
        ),
        (
            "PDF 2.7 atendimento",
            "relacao",
            lambda: dict(x=pdf()["ex3_atendimento"]["x"], y=pdf()["ex3_atendimento"]["y"]),
            "Correlação de Spearman",
        ),
        (
            "PDF 6.2 otimização",
            "pareado",
            lambda: dict(antes=pdf()["ex4_antes_depois"]["antes"], depois=pdf()["ex4_antes_depois"]["depois"]),
            "t pareado",
        ),
        (
            "PDF 6.3 APF",
            "dois_grupos",
            lambda: dict(a=pdf()["ex5_apf"]["g1"], b=pdf()["ex5_apf"]["g2"]),
            "t independente (variâncias iguais)",
        ),
        (
            "PDF 6.2 como independentes",
            "dois_grupos",
            lambda: dict(a=pdf()["ex4_antes_depois"]["antes"], b=pdf()["ex4_antes_depois"]["depois"]),
            "t de Welch (variâncias diferentes)",
        ),
        ("PDF 8.3 força", "tres_grupos", lambda: dict(grupos=_grupos(pdf()["ex6_forca"])), "ANOVA (1 fator)"),
        (
            "PDF 8.4 resistência",
            "tres_grupos",
            lambda: dict(grupos=_grupos(pdf()["ex7_resistencia"])),
            "Kruskal-Wallis",
        ),
        (
            "PDF 8.5 grupos 1 a 3",
            "tres_grupos",
            lambda: dict(grupos=_grupos(pdf()["ex85_grupos_1_3"])),
            "Kruskal-Wallis",
        ),
        (
            "gabarito Ex. 3",
            "dois_grupos",
            lambda: dict(a=gabarito()["ex3"]["a"], b=gabarito()["ex3"]["b"]),
            "t independente (variâncias iguais)",
        ),
        (
            "gabarito Ex. 4",
            "tres_grupos",
            lambda: dict(grupos={k: gabarito()["ex4"][k] for k in ("manha", "tarde", "noite")}),
            "ANOVA (1 fator)",
        ),
        (
            "gabarito Ex. 5",
            "tres_grupos",
            lambda: dict(grupos={k: gabarito()["ex5_planilha"][k] for k in ("manha", "tarde", "noite")}),
            "Kruskal-Wallis",
        ),
        ("gabarito Ex. 6", "proporcoes", lambda: dict(x1=31, n1=62, x2=117, n2=182), "Teste z de duas proporções"),
        (
            "gabarito Ex. 10",
            "pareado",
            lambda: dict(
                antes=gabarito()["enunciado_bruto"]["ex10_antes"], depois=gabarito()["enunciado_bruto"]["ex10_depois"]
            ),
            "Wilcoxon (pareado)",
        ),
        ("proporções pequenas", "proporcoes", lambda: dict(x1=2, n1=10, x2=5, n2=12), "Teste exato de Fisher"),
        (
            "2 × 2 com esperados pequenos",
            "associacao",
            lambda: dict(tabela=[[1, 9], [6, 4]]),
            "Teste exato de Fisher (2 × 2)",
        ),
    ],
)
def test_assistente_com_dados_chega_ao_teste_da_apostila(caso, objetivo, argumentos, teste):
    res = assistente.analisar(objetivo, **argumentos())
    assert res.nome == teste, caso
    passos = assistente.caminho(objetivo, res)
    assert passos[-1].startswith(f"Teste escolhido: {teste}")


def test_caminho_explica_o_pre_requisito_violado_resistencia():
    res = assistente.analisar("tres_grupos", grupos=_grupos(pdf()["ex7_resistencia"]))
    passos = assistente.caminho("tres_grupos", res)
    assert "pré-requisito violado: Normalidade — G1; Normalidade — G3" in passos[-1]
    assert any(p.startswith("❌ Normalidade — G1") for p in passos)


def test_caminho_parametrico_com_ressalva():
    d = pdf()["ex3_atendimento"]
    res = assistente.analisar("relacao", x=d["x"], y=d["y"])  # Spearman: tempo não normal
    assert "violado" in assistente.caminho("relacao", res)[-1]
    res2 = assistente.analisar("tres_grupos", grupos={k: gabarito()["ex4"][k] for k in ("manha", "tarde", "noite")})
    assert "com ressalvas" in assistente.caminho("tres_grupos", res2)[-1]  # outlier suave em manhã (82)


def test_uma_amostra_e_associacao_normal():
    x = np.random.default_rng(5).normal(52, 6, 25)
    assert assistente.analisar("uma_amostra", valores=x, mu0=50).nome == "t para uma amostra"
    assert assistente.analisar("associacao", tabela=[[31, 31], [117, 65]]).nome == "Qui-quadrado de independência"


# --------------------------------------------------------------------------- tela


def test_tela_perguntas_padrao_nao_sei_mostra_pendencia():
    at = app("assistente.py")
    sem_erros(at)
    assert any("Normalidade" in i.value for i in at.info)


def test_tela_perguntas_dois_grupos_welch():
    at = app("assistente.py")
    at.radio(key="as_obj").set_value("dois_grupos").run()
    at.radio(key="as_normal").set_value("Sim").run()
    at.radio(key="as_var").set_value("Não").run()
    sem_erros(at)
    assert any("t de Welch" in s.value for s in at.success)


def test_tela_dados_resistencia_chega_ao_kruskal():
    d = pdf()["ex7_resistencia"]
    at = app("assistente.py", {"Resist": worksheet(G1=d["g1"], G2=d["g2"], G3=d["g3"])})
    at.selectbox(key="as_obj_dados").set_value("tres_grupos").run()
    sem_erros(at)
    assert any("Teste escolhido: Kruskal-Wallis" in m.value for m in at.markdown)


def test_tela_dados_associacao_por_colunas():
    df = pd.DataFrame(
        {"Turma": ["A"] * 30 + ["B"] * 30, "Aprov": (["s"] * 20 + ["n"] * 10) + (["s"] * 10 + ["n"] * 20)}
    )
    at = app("assistente.py", {"T": df})
    at.selectbox(key="as_obj_dados").set_value("associacao").run()
    sem_erros(at)
    assert any("Qui-quadrado de independência" in m.value for m in at.markdown)


def test_tela_tabela_de_referencia_tem_os_sete_objetivos():
    at = app("assistente.py")
    tabela = at.dataframe[0].value
    assert len(tabela) == 7
    assert "Kruskal-Wallis (+ comparações 2 a 2)" in list(tabela["Não paramétrico"])
