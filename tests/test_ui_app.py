"""Interface do pivô: menus, diálogos e janela de sessão.

O teste central é ``test_o_app_nao_decide_nem_altera_os_dados``: com as opções no padrão, o comando
roda exatamente o que foi pedido e não mexe na amostra.
"""

from __future__ import annotations

import pandas as pd
import pytest

from statlab.ui.comandos import COMANDOS, MENUS
from tests.helpers import gabarito, pdf
from tests.ui_util import abrir, app, executar, linhas_da_saida, saida, sem_erros, worksheet


def ws_ex3() -> dict[str, pd.DataFrame]:
    g = gabarito()["ex3"]
    return {"Ex3": worksheet(**{"Equipe A": g["a"], "Equipe B": g["b"]})}


# --------------------------------------------------------------------------- layout


def test_app_abre_sem_worksheet():
    at = app()
    sem_erros(at)
    assert any("Nenhuma worksheet aberta" in i.value for i in at.info)
    assert len(at.button) == len(COMANDOS), "a barra de menus deve listar todos os comandos"


def test_app_mostra_worksheet_e_sessao_vazia():
    at = app(ws_ex3())
    sem_erros(at)
    assert [s.value for s in at.subheader] == ["Worksheet: Ex3", "Sessão"]
    assert len(at.data_editor) == 1
    assert saida(at) == []


def test_todos_os_menus_tem_comandos():
    for menu in MENUS:
        assert [c for c in COMANDOS if c.menu == menu], f"menu {menu} vazio"


@pytest.mark.parametrize("comando", COMANDOS, ids=lambda c: f"{c.menu}-{c.nome}")
def test_todo_comando_abre_sem_quebrar(comando):
    at = abrir(app(ws_ex3()), comando.menu, comando.grupo, comando.nome)
    sem_erros(at, esperando_mensagem=True)


# --------------------------------------------------------------------------- o app não decide


def test_t_de_2_amostras_com_variancias_iguais_reproduz_o_gabarito():
    """Ex. 3: marcando "assumir variâncias iguais", T = 1,473; GL = 17; P = 0,159."""
    at = abrir(app(ws_ex3()), "Estat", "Estatísticas básicas", "t de 2 amostras")
    at.checkbox(key="t2_iguais").set_value(True).run()
    at = executar(at)
    sem_erros(at)
    item = saida(at)[-1]
    assert item.teste == "t independente (variâncias iguais)"
    texto = linhas_da_saida(at)
    assert "t = 1,473" in texto and "gl = 17" in texto and "p = 0,159" in texto


def test_a_mesma_analise_sem_a_opcao_usa_welch_e_a_sessao_acumula():
    at = abrir(app(ws_ex3()), "Estat", "Estatísticas básicas", "t de 2 amostras")
    at = executar(at)  # caixa desmarcada → Welch
    assert saida(at)[-1].teste.startswith("t de Welch")
    assert "gl = 8,8" in linhas_da_saida(at)

    at = abrir(at, "Estat", "Estatísticas básicas", "t de 2 amostras")
    at.checkbox(key="t2_iguais").set_value(True).run()
    at = executar(at)
    sem_erros(at)
    assert len(saida(at)) == 2, "a janela de sessão acumula as duas saídas"
    assert saida(at)[0].teste.startswith("t de Welch")
    assert saida(at)[1].teste.startswith("t independente")


def test_o_app_nao_decide_nem_altera_os_dados():
    """Ex. 5 bruto tem os extremos 37 e 38: sem marcar a opção, eles continuam na conta."""
    g = gabarito()
    tarde = g["enunciado_bruto"]["ex5_tarde"]
    planilha = {"Ex5": worksheet(manha=g["ex5_planilha"]["manha"], tarde=tarde)}
    at = abrir(app(planilha), "Estat", "Estatísticas básicas", "t de 2 amostras")
    at = executar(at)
    sem_erros(at)
    item = saida(at)[-1]
    assert f"n = {len(g['ex5_planilha']['manha']) + len(tarde)}" in linhas_da_saida(at)
    assert not any("excluído" in a for a in item.avisos)


def test_excluir_outliers_e_opcao_explicita_com_o_n_antes_e_depois():
    g = gabarito()
    tarde = g["enunciado_bruto"]["ex5_tarde"]
    planilha = {"Ex5": worksheet(manha=g["ex5_planilha"]["manha"], tarde=tarde)}
    at = abrir(app(planilha), "Estat", "Estatísticas básicas", "t de 2 amostras")
    at.checkbox(key="t2_out").set_value(True).run()
    at = executar(at)
    sem_erros(at)
    avisos = "\n".join(saida(at)[-1].avisos)
    assert "outlier(s) extremo(s) excluído(s)" in avisos
    assert f"(antes: {len(tarde)})" in avisos


def test_anova_nao_aplica_tukey_sozinha():
    d = pdf()["ex6_forca"]
    planilha = {"Força": worksheet(G1=d["g1"], G2=d["g2"], G3=d["g3"])}
    at = abrir(app(planilha), "Estat", "ANOVA", "Um fator")
    at = executar(at)
    sem_erros(at)
    item = saida(at)[-1]
    assert [nome for nome, _ in item.tabelas] == ["Análise de variância"]
    assert "Valor F" in item.tabelas[0][1].columns


def test_anova_com_tukey_marcado_traz_as_comparacoes():
    d = pdf()["ex6_forca"]
    planilha = {"Força": worksheet(G1=d["g1"], G2=d["g2"], G3=d["g3"])}
    at = abrir(app(planilha), "Estat", "ANOVA", "Um fator")
    at.checkbox(key="an_tukey").set_value(True).run()
    at = executar(at)
    sem_erros(at)
    nomes = [nome for nome, _ in saida(at)[-1].tabelas]
    assert any(nome.startswith("Tukey") for nome in nomes), nomes


def test_regressao_nao_trava_em_correlacao_nao_significativa():
    """Ex. 1: a correlação não é significativa e a reta é calculada do mesmo jeito."""
    g = gabarito()["ex1"]
    at = abrir(app({"Ex1": worksheet(x=g["x"], y=g["y"])}), "Estat", "Regressão", "Regressão simples")
    at = executar(at)
    sem_erros(at)
    texto = linhas_da_saida(at)
    assert "Equação:" in texto
    assert "não deve ser feita" not in texto


def test_correlacao_respeita_o_metodo_pedido():
    d = pdf()["ex3_atendimento"]
    pares = [(a, b) for a, b in zip(d["x"], d["y"], strict=True) if b is not None]
    planilha = {"Atend": worksheet(x=[a for a, _ in pares], y=[b for _, b in pares])}
    at = abrir(app(planilha), "Estat", "Estatísticas básicas", "Correlação")
    at.radio(key="cor_met").set_value("Spearman").run()
    at = executar(at)
    sem_erros(at)
    assert saida(at)[-1].teste == "Correlação de Spearman"


def test_sem_conclusao_redigida_na_saida():
    at = abrir(app(ws_ex3()), "Estat", "Estatísticas básicas", "t de 2 amostras")
    at = executar(at)
    texto = linhas_da_saida(at)
    for frase in ("significativamente maior", "significativamente menor", "Não há diferença significativa"):
        assert frase not in texto, f"a conclusão redigida vazou: {frase!r}"


# --------------------------------------------------------------------------- dados e sessão


def test_descritivas_vao_para_a_sessao_como_tabela():
    at = abrir(app(ws_ex3()), "Estat", "Estatísticas básicas", "Exibição de estatísticas descritivas")
    at = executar(at)
    sem_erros(at)
    nome, tabela = saida(at)[-1].tabelas[0]
    assert nome == "Estatísticas"
    assert {"Variável", "N", "Média", "Q1", "Mediana", "Q3"} <= set(tabela.columns)


def test_grafico_vai_para_a_sessao():
    at = abrir(app(ws_ex3()), "Gráfico", "", "Boxplot")
    at = executar(at, "Desenhar")
    sem_erros(at)
    assert len(saida(at)[-1].figuras) == 1


def test_sessao_exporta_html_autocontido():
    """O plotly.js vai embutido: nenhuma tag script aponta para fora (sem CDN)."""
    import re

    from statlab.relatorio import para_html

    at = abrir(app(ws_ex3()), "Gráfico", "", "Boxplot")
    at = executar(at, "Desenhar")
    html = para_html(saida(at))
    assert "<html" in html
    assert re.findall(r'<script[^>]*src="https?://', html) == []


def test_assistente_indica_o_comando_sem_analisar():
    at = abrir(app(ws_ex3()), "Assistente", "", "Qual teste usar?")
    sem_erros(at)
    assert any("Qual é o objetivo?" in r.label for r in at.radio)
    assert saida(at) == [], "o assistente não produz análise"
