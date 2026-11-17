"""F5: conclusões no padrão da apostila (seção 10 e exemplos resolvidos) e relatório Markdown/HTML."""

import numpy as np
import pandas as pd
import pytest

from statlab import graficos
from statlab.core.anova import analisar_grupos
from statlab.core.anova_dois_fatores import analisar_anova_dois_fatores
from statlab.core.conclusoes import concluir
from statlab.core.correlacao import analisar_correlacao
from statlab.core.proporcoes import analisar_proporcoes
from statlab.core.qui_quadrado import independencia
from statlab.core.regressao import analisar_regressao
from statlab.core.regressao_multipla import analisar_regressao_multipla
from statlab.core.testes_t import analisar_antes_depois, analisar_dois_grupos
from statlab.core.uma_amostra import analisar_uma_amostra, analisar_uma_proporcao
from statlab.relatorio import item_de, para_html, para_markdown
from statlab.ui import estado
from tests.helpers import carregar, gabarito, pdf
from tests.ui_util import app, sem_erros, worksheet


def _g(d, nomes=("g1", "g2", "g3")):
    return {n.upper(): d[n] for n in nomes}


# --------------------------------------------------------------------------- conclusões × apostila


def test_pdf_ex1_correlacao_modelo_de_redacao():
    d = pdf()["ex1_publicidade"]
    texto = concluir(analisar_correlacao(d["x"], d["y"], nome_x="investimento", nome_y="faturamento"))
    assert texto.startswith(
        "Existe correlação positiva, significativa e muito forte entre investimento e faturamento "
        "(r = 0,975; p = 0,005), com 99% de confiança: à medida que investimento aumenta, faturamento aumenta."
    )
    assert "explica cerca de 95,1% da variação de faturamento; os 4,9% restantes se devem a outros fatores" in texto


def test_pdf_ex2_correlacao_negativa():
    d = pdf()["ex2_treinamento"]
    texto = concluir(analisar_correlacao(d["x"], d["y"], nome_x="treinamento", nome_y="erros"))
    assert "correlação negativa, significativa e muito forte" in texto
    assert "(r = -0,988; p < 0,001), com 99% de confiança" in texto
    assert "treinamento aumenta, erros diminui" in texto


def test_pdf_ex3_sem_correlacao_spearman():
    d = pdf()["ex3_atendimento"]
    texto = concluir(analisar_correlacao(d["x"], d["y"], nome_x="tempo", nome_y="produtividade"))
    assert texto.startswith("Não existe correlação significativa entre tempo e produtividade")
    assert "(Spearman: rₛ = 0,005; p = 0,977)" in texto
    assert "regressão linear não deve ser aplicada" in texto


def test_pdf_regressao_extrapolacao_no_intercepto():
    """PDF 3: 'Sem investimento (x = 0) o modelo estimaria R$ 12,2 mil, mas esse valor é uma extrapolação'."""
    d = pdf()["ex1_publicidade"]
    texto = concluir(analisar_regressao(d["x"], d["y"], nome_x="investimento", nome_y="faturamento"))
    assert "espera-se aumento de 4,700 unidade(s) em faturamento" in texto
    assert "estimaria faturamento = 12,20, mas isso é extrapolação" in texto


def test_pdf_ex4_pareado_reducao():
    d = pdf()["ex4_antes_depois"]
    texto = concluir(analisar_antes_depois(d["antes"], d["depois"], alternativa="maior"), variavel="o tempo")
    assert "Depois, o tempo é significativamente menor do que antes (t = 21,85; gl = 14; p < 0,001)" in texto
    assert "com 99% de confiança" in texto
    assert "cerca de 59% do valor antes" in texto  # PDF: "cerca de 59%"
    assert "redução média entre 1.400,17 e 1.705,03" in texto  # PDF: entre 1400 e 1705 ms


def test_pdf_ex5_t_independente_com_ic_reorientado():
    d = pdf()["ex5_apf"]
    texto = concluir(analisar_dois_grupos(d["g1"], d["g2"], nome_a="G1", nome_b="G2"), variavel="APF")
    assert texto.startswith(
        "G2 apresentou média de APF significativamente maior que G1 (t = -7,93; gl = 12; p < 0,001), "
        "com 99% de confiança."
    )
    assert "que a média de G2 supere a de G1 entre 64," in texto  # PDF: entre 64,8 e 113,8
    assert "e 113,8" in texto


def test_pdf_ex6_anova_tukey():
    texto = concluir(analisar_grupos(_g(pdf()["ex6_forca"])), variavel="força")
    assert "Há diferença significativa entre as médias de força dos grupos (ANOVA: F = 8,70; p < 0,001)" in texto
    assert "G2 tem média significativamente maior que G1 (95% de confiança)" in texto
    assert "G3 tem média significativamente maior que G1 (99% de confiança)" in texto
    assert "Não houve diferença significativa entre G2 e G3 (p = 0,435)" in texto


def test_pdf_ex7_kruskal_com_medianas():
    texto = concluir(analisar_grupos(_g(pdf()["ex7_resistencia"])), variavel="resistência")
    assert "(Kruskal-Wallis: H = 29,37; p < 0,001), com 99% de confiança" in texto
    assert "G3 (mediana 459) > G1 (mediana 283)" in texto
    assert "G3 (mediana 459) > G2 (mediana 299)" in texto
    assert "Não houve diferença significativa entre G1 e G2 (p = 1,000)" in texto


def test_gabarito_ex6_proporcoes():
    texto = concluir(
        analisar_proporcoes(31, 62, 117, 182, nome_1="Turma com monitoria", nome_2="Turma sem monitoria"),
        variavel="aprovação na disciplina",
    )
    assert "é significativamente maior em Turma sem monitoria (64,3%) do que em Turma com monitoria (50,0%)" in texto
    assert "p = 0,047), com 95% de confiança" in texto


def test_gabarito_ex3_nao_significativo():
    g = gabarito()["ex3"]
    texto = concluir(analisar_dois_grupos(g["a"], g["b"], nome_a="Equipe A", nome_b="Equipe B"), variavel="tempo")
    assert texto == (
        "Não há diferença significativa entre as médias de tempo de Equipe A e Equipe B (t = 1,47; gl = 17; p = 0,159)."
    )


def test_gabarito_ex10_wilcoxon_com_medianas():
    g = gabarito()["enunciado_bruto"]
    texto = concluir(analisar_antes_depois(g["ex10_antes"], g["ex10_depois"], alternativa="menor"), variavel="a nota")
    assert texto.startswith("Pelo teste de Wilcoxon, a nota é significativamente maior depois do que antes")
    assert "medianas: antes 55,50, depois 61" in texto


def test_welch_identificado():
    d = pdf()["ex4_antes_depois"]
    texto = concluir(analisar_dois_grupos(d["antes"], d["depois"], nome_a="antes", nome_b="depois"))
    assert "(Welch: t = 24,19" in texto


def test_anova2_interacao_e_regressao_multipla():
    doe = pd.DataFrame(carregar("minitab_exemplos.json")["doe_horas"])
    texto = concluir(analisar_anova_dois_fatores(doe, "Horas", "SistemaPedidos", "Pacote"), variavel="horas")
    assert "SistemaPedidos*Pacote: F = 20,12; p = 0,002 (significativo)" in texto
    assert "gráfico de interação" in texto
    doe["SP"] = np.where(doe["SistemaPedidos"] == "Atual", 1.0, -1.0)
    doe["PC"] = np.where(doe["Pacote"] == "B", 1.0, -1.0)
    texto_r = concluir(analisar_regressao_multipla(doe, "Horas", ["SP", "PC"]))
    assert texto_r.startswith("O modelo é significativo")
    assert "SP (+1,548 por unidade" in texto_r


def test_uma_amostra_qui_quadrado_e_proporcao():
    x = np.random.default_rng(5).normal(60, 4, 30)
    assert "significativamente maior que 50" in concluir(analisar_uma_amostra(x, 50), variavel="nota")
    assert "Há associação significativa" in concluir(independencia([[30, 5], [5, 30]]))
    assert "Não há evidência de que a proporção" in concluir(analisar_uma_proporcao(10, 20, 0.5), variavel="acerto")


PROIBIDAS = ("as médias são iguais", "médias iguais", "prova que", "não há correlação entre")


@pytest.mark.parametrize("caso", ["ex3_atendimento", "ex5_apf", "ex7_resistencia"])
def test_conclusoes_nunca_afirmam_h0(caso):
    d = pdf()[caso]
    if caso == "ex3_atendimento":
        res = analisar_correlacao(d["x"], d["y"])
    elif caso == "ex5_apf":
        res = analisar_dois_grupos(d["g1"], d["g2"])
    else:
        res = analisar_grupos(_g(d))
    texto = concluir(res).lower()
    assert not any(f in texto for f in PROIBIDAS)


# --------------------------------------------------------------------------- relatório


def _itens():
    d = pdf()["ex6_forca"]
    res = analisar_grupos(_g(d))
    fig1 = graficos.boxplot(_g(d))
    fig2 = graficos.tukey_intervalos(res.comparacoes)
    cor = analisar_correlacao(pdf()["ex1_publicidade"]["x"], pdf()["ex1_publicidade"]["y"])
    return [
        item_de(res, titulo="Força <G1, G2, G3>", variavel="força", figuras=[fig1, fig2]),
        item_de(cor, titulo="Publicidade", figuras=[graficos.dispersao([1.0, 2, 3], [2.0, 4, 7])]),
    ]


def test_markdown_tem_secoes_e_conclusao():
    md = para_markdown(_itens(), "Lista 2026")
    assert md.startswith("# Lista 2026")
    assert "## 1. Força <G1, G2, G3>" in md
    assert "**Conclusão:** Há diferença significativa entre as médias de força" in md
    assert "### Pré-requisitos" in md and "✅" in md
    assert "### Resultado" in md and "- F = 8,703" in md
    assert "```text" in md
    assert "2 gráfico(s) disponível(is) na versão HTML" in md


def test_html_escapa_texto_e_embute_plotly_uma_vez():
    pagina = para_html(_itens(), "Relatório <teste>")
    assert "<title>Relatório &lt;teste&gt;</title>" in pagina
    assert "Força &lt;G1, G2, G3&gt;" in pagina
    assert pagina.count("window.PlotlyConfig") == 1  # plotly.js incluído só no primeiro gráfico
    assert pagina.count("Plotly.newPlot") == 3
    assert '<script src="http' not in pagina  # nada carregado de fora
    assert "prefers-color-scheme: dark" in pagina


def test_relatorio_vazio_ainda_gera_arquivos():
    assert "0 análise(s)" in para_markdown([])
    assert "0 análise(s)" in para_html([])


# --------------------------------------------------------------------------- telas


def test_tela_mostra_conclusao_e_adiciona_ao_relatorio():
    g = gabarito()["ex3"]
    at = app("dois_grupos.py", {"Ex3": worksheet(**{"Equipe A": g["a"], "Equipe B": g["b"]})})
    at.text_input(key="g2_nome").input("tempo de deploy").run()
    sem_erros(at)
    assert any("Não há diferença significativa entre as médias de tempo de deploy" in m.value for m in at.markdown)
    at.button(key="rel_g2").click().run()
    itens = at.session_state[estado.RELATORIO]
    assert len(itens) == 1
    assert itens[0].titulo == "Dois grupos: Equipe A × Equipe B"
    assert len(itens[0].figuras) == 1


def test_tela_correlacao_adiciona_correlacao_e_regressao():
    g = gabarito()["ex9"]
    at = app("correlacao.py", {"Ex9": worksheet(Commits=g["x"], Bugs=g["y"])})
    at.button(key="rel_cor").click().run()
    sem_erros(at)
    titulos = [i.titulo for i in at.session_state[estado.RELATORIO]]
    assert titulos == ["Correlação: Commits × Bugs", "Regressão: Bugs em função de Commits"]


def test_pagina_relatorio_vazia_orienta():
    at = app("relatorio.py")
    sem_erros(at)
    assert any("relatório está vazio" in i.value for i in at.info)


def test_pagina_relatorio_lista_baixa_e_remove():
    at = app("relatorio.py")
    at.session_state[estado.RELATORIO] = _itens()
    at.run()
    sem_erros(at)
    rotulos = [b.proto.label for b in at.get("download_button")]
    assert rotulos == ["Baixar HTML (com gráficos)", "Baixar Markdown"]
    assert len(at.expander) == 2
    at.button(key="rel_remover_0").click().run()
    assert [i.titulo for i in at.session_state[estado.RELATORIO]] == ["Publicidade"]
    at.button(key="rel_limpar").click().run()
    assert at.session_state[estado.RELATORIO] == []
