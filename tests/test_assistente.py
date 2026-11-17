"""F4: assistente 'Qual teste usar?' — árvore de decisão e os casos da apostila e do gabarito."""

import pytest

from statlab.core import assistente

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
        ("relacao", {}, "Teste de normalidade"),
        ("dois_grupos", {}, "Teste de normalidade"),
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
