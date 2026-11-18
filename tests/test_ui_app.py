"""Interface do pivô (Qt): menus, diálogos, grade da worksheet e janela de sessão.

O teste central é ``test_o_app_nao_decide_nem_altera_os_dados``: com as opções no padrão, o comando
roda exatamente o que foi pedido e não mexe na amostra.
"""

from __future__ import annotations

import pandas as pd
import pytest

from statlab.ui import estado
from statlab.ui.comandos import COMANDOS, MENUS
from statlab.ui.comandos._base import MODO_EMPILHADO
from tests.helpers import gabarito, pdf
from tests.ui_util import (
    abrir,
    app,
    definir,
    executar,
    linhas_da_saida,
    saida,
    sem_erros,
    textos,
    worksheet,
)


def ws_ex3() -> dict[str, pd.DataFrame]:
    g = gabarito()["ex3"]
    return {"Ex3": worksheet(**{"Equipe A": g["a"], "Equipe B": g["b"]})}


# --------------------------------------------------------------------------- layout


def test_app_abre_sem_worksheet():
    janela = app()
    painel = janela.painel_worksheet
    assert "Nenhuma worksheet aberta" in painel.aviso_vazio.text()
    assert not painel.aviso_vazio.isHidden()
    assert painel.tabela.isHidden()
    assert len(janela.acoes) == len(COMANDOS), "a barra de menus lista todos os comandos"


def test_app_mostra_worksheet_e_sessao_vazia():
    planilhas = ws_ex3()
    janela = app(planilhas)
    painel = janela.painel_worksheet
    assert painel.titulo.text() == "<b>Worksheet: Ex3</b>"
    assert not painel.tabela.isHidden()
    assert painel.modelo.rowCount() == len(planilhas["Ex3"])
    assert painel.modelo.columnCount() == 2
    assert saida() == []
    assert janela.painel_sessao.abas.count() == 0
    assert not janela.painel_sessao.aviso_vazio.isHidden()


def test_todos_os_menus_tem_comandos():
    for menu in MENUS:
        assert [c for c in COMANDOS if c.menu == menu], f"menu {menu} vazio"


@pytest.mark.parametrize("comando", COMANDOS, ids=lambda c: f"{c.menu}-{c.nome}")
def test_todo_comando_abre_sem_quebrar(comando):
    dialogo = abrir(app(ws_ex3()), comando.menu, comando.grupo, comando.nome)
    assert dialogo.windowTitle() == comando.nome
    sem_erros(dialogo, esperando_mensagem=True)


# --------------------------------------------------------------------------- o diálogo reage


def test_mudar_a_opcao_redesenha_o_dialogo():
    """Trocar a organização dos grupos troca as perguntas, sem fechar o diálogo."""
    dialogo = abrir(app(ws_ex3()), "Estat", "Variâncias", "Teste F (2 variâncias)")
    assert "Colunas (uma por grupo)" in " ".join(textos(dialogo))
    definir(dialogo, "vf_modo", MODO_EMPILHADO)
    depois = " ".join(textos(dialogo))
    assert "Resposta (numérica)" in depois
    assert "Colunas (uma por grupo)" not in depois
    assert not dialogo.encerrado, "mexer numa opção não fecha o diálogo"


def test_cancelar_nao_deixa_nada_na_sessao():
    dialogo = abrir(app(ws_ex3()), "Estat", "Estatísticas básicas", "t de 2 amostras")
    dialogo.reject()
    assert saida() == []


def test_erro_de_dados_aparece_no_dialogo_sem_virar_traceback():
    dialogo = abrir(app(ws_ex3()), "Dados", "", "Recodificar valores")
    definir(dialogo, "rec_dest", "")
    executar(dialogo, "Recodificar")
    assert "Informe o nome da coluna nova" in dialogo.ultimo_erro
    assert not dialogo.aviso_erro.isHidden()
    assert saida() == [], "nada foi para a sessão"


# --------------------------------------------------------------------------- o app não decide


def test_t_de_2_amostras_com_variancias_iguais_reproduz_o_gabarito():
    """Ex. 3: marcando "assumir variâncias iguais", T = 1,473; GL = 17; P = 0,159."""
    dialogo = abrir(app(ws_ex3()), "Estat", "Estatísticas básicas", "t de 2 amostras")
    definir(dialogo, "t2_iguais", True)
    executar(dialogo)
    sem_erros(dialogo)
    assert saida()[-1].teste == "t independente (variâncias iguais)"
    texto = linhas_da_saida()
    assert "t = 1,473" in texto and "gl = 17" in texto and "p = 0,159" in texto


def test_a_mesma_analise_sem_a_opcao_usa_welch_e_a_sessao_acumula():
    janela = app(ws_ex3())
    executar(abrir(janela, "Estat", "Estatísticas básicas", "t de 2 amostras"))  # desmarcada → Welch
    assert saida()[-1].teste.startswith("t de Welch")
    assert "gl = 8,8" in linhas_da_saida()

    dialogo = abrir(janela, "Estat", "Estatísticas básicas", "t de 2 amostras")
    definir(dialogo, "t2_iguais", True)
    executar(dialogo)
    sem_erros(dialogo)
    assert len(saida()) == 2, "a janela de sessão acumula as duas saídas"
    assert saida()[0].teste.startswith("t de Welch")
    assert saida()[1].teste.startswith("t independente")
    assert janela.painel_sessao.abas.count() == 2
    assert janela.painel_sessao.abas.currentIndex() == 1, "a saída nova fica em foco"


def test_o_app_nao_decide_nem_altera_os_dados():
    """Ex. 5 bruto tem os extremos 37 e 38: sem marcar a opção, eles continuam na conta."""
    g = gabarito()
    tarde = g["enunciado_bruto"]["ex5_tarde"]
    planilha = {"Ex5": worksheet(manha=g["ex5_planilha"]["manha"], tarde=tarde)}
    dialogo = abrir(app(planilha), "Estat", "Estatísticas básicas", "t de 2 amostras")
    executar(dialogo)
    sem_erros(dialogo)
    item = saida()[-1]
    assert f"n = {len(g['ex5_planilha']['manha']) + len(tarde)}" in linhas_da_saida()
    assert not any("excluído" in a for a in item.avisos)


def test_excluir_outliers_e_opcao_explicita_com_o_n_antes_e_depois():
    g = gabarito()
    tarde = g["enunciado_bruto"]["ex5_tarde"]
    planilha = {"Ex5": worksheet(manha=g["ex5_planilha"]["manha"], tarde=tarde)}
    dialogo = abrir(app(planilha), "Estat", "Estatísticas básicas", "t de 2 amostras")
    definir(dialogo, "t2_out", True)
    executar(dialogo)
    sem_erros(dialogo)
    avisos = "\n".join(saida()[-1].avisos)
    assert "outlier(s) extremo(s) excluído(s)" in avisos
    assert f"(antes: {len(tarde)})" in avisos


def test_anova_nao_aplica_tukey_sozinha():
    d = pdf()["ex6_forca"]
    planilha = {"Força": worksheet(G1=d["g1"], G2=d["g2"], G3=d["g3"])}
    dialogo = abrir(app(planilha), "Estat", "ANOVA", "Um fator")
    executar(dialogo)
    sem_erros(dialogo)
    item = saida()[-1]
    assert [nome for nome, _ in item.tabelas] == ["Análise de variância"]
    assert "Valor F" in item.tabelas[0][1].columns


def test_anova_com_tukey_marcado_traz_as_comparacoes():
    d = pdf()["ex6_forca"]
    planilha = {"Força": worksheet(G1=d["g1"], G2=d["g2"], G3=d["g3"])}
    dialogo = abrir(app(planilha), "Estat", "ANOVA", "Um fator")
    definir(dialogo, "an_tukey", True)
    executar(dialogo)
    sem_erros(dialogo)
    nomes = [nome for nome, _ in saida()[-1].tabelas]
    assert any(nome.startswith("Tukey") for nome in nomes), nomes


def test_regressao_nao_trava_em_correlacao_nao_significativa():
    """Ex. 1: a correlação não é significativa e a reta é calculada do mesmo jeito."""
    g = gabarito()["ex1"]
    dialogo = abrir(app({"Ex1": worksheet(x=g["x"], y=g["y"])}), "Estat", "Regressão", "Regressão simples")
    executar(dialogo)
    sem_erros(dialogo)
    texto = linhas_da_saida()
    assert "Equação:" in texto
    assert "não deve ser feita" not in texto


def test_correlacao_respeita_o_metodo_pedido():
    d = pdf()["ex3_atendimento"]
    pares = [(a, b) for a, b in zip(d["x"], d["y"], strict=True) if b is not None]
    planilha = {"Atend": worksheet(x=[a for a, _ in pares], y=[b for _, b in pares])}
    dialogo = abrir(app(planilha), "Estat", "Estatísticas básicas", "Correlação")
    definir(dialogo, "cor_met", "Spearman")
    executar(dialogo)
    sem_erros(dialogo)
    assert saida()[-1].teste == "Correlação de Spearman"


def test_sem_conclusao_redigida_na_saida():
    dialogo = abrir(app(ws_ex3()), "Estat", "Estatísticas básicas", "t de 2 amostras")
    executar(dialogo)
    texto = linhas_da_saida()
    for frase in ("significativamente maior", "significativamente menor", "Não há diferença significativa"):
        assert frase not in texto, f"a conclusão redigida vazou: {frase!r}"


# --------------------------------------------------------------------------- grade da worksheet


def test_editar_celula_grava_na_worksheet():
    janela = app(ws_ex3())
    modelo = janela.painel_worksheet.modelo
    assert modelo.setData(modelo.index(0, 0), "42,5"), "vírgula decimal é aceita"
    assert estado.planilhas()["Ex3"].iat[0, 0] == 42.5


def test_celula_numerica_recusa_texto_e_mantem_o_valor():
    janela = app(ws_ex3())
    modelo = janela.painel_worksheet.modelo
    antes = estado.planilhas()["Ex3"].iat[0, 0]
    assert not modelo.setData(modelo.index(0, 0), "mais ou menos")
    assert estado.planilhas()["Ex3"].iat[0, 0] == antes


def test_adicionar_e_remover_linha_na_grade():
    janela = app(ws_ex3())
    painel = janela.painel_worksheet
    antes = painel.modelo.rowCount()
    painel.modelo.insertRows(antes, 1)
    assert len(estado.planilhas()["Ex3"]) == antes + 1
    painel.modelo.removeRows(antes, 1)
    assert len(estado.planilhas()["Ex3"]) == antes


def test_mais_cria_worksheet_em_branco():
    janela = app()
    janela.painel_worksheet.nova_worksheet()
    assert list(estado.planilhas()) == ["Worksheet"]
    assert list(estado.planilhas()["Worksheet"].columns) == ["C1", "C2", "C3"]
    assert janela.painel_worksheet.titulo.text() == "<b>Worksheet: Worksheet</b>"


def test_trocar_de_worksheet_preserva_os_dados():
    janela = app({"A": worksheet(x=[1.0, 2.0]), "B": worksheet(y=[9.0])})
    modelo = janela.painel_worksheet.modelo
    assert modelo.columnCount() == 1
    modelo.setData(modelo.index(0, 0), "7")
    estado.ativa_set("B")
    assert janela.painel_worksheet.titulo.text() == "<b>Worksheet: B</b>"
    estado.ativa_set("A")
    assert estado.planilhas()["A"].iat[0, 0] == 7.0
    assert janela.painel_worksheet.modelo.df().iat[0, 0] == 7.0


# --------------------------------------------------------------------------- dados e sessão


def test_descritivas_vao_para_a_sessao_como_tabela():
    dialogo = abrir(app(ws_ex3()), "Estat", "Estatísticas básicas", "Exibição de estatísticas descritivas")
    executar(dialogo)
    sem_erros(dialogo)
    nome, tabela = saida()[-1].tabelas[0]
    assert nome == "Estatísticas"
    assert {"Variável", "N", "Média", "Q1", "Mediana", "Q3"} <= set(tabela.columns)


def test_grafico_vai_para_a_sessao():
    dialogo = abrir(app(ws_ex3()), "Gráfico", "", "Boxplot")
    executar(dialogo, "Desenhar")
    sem_erros(dialogo)
    assert len(saida()[-1].figuras) == 1


def test_fechar_a_aba_remove_o_bloco_da_sessao():
    janela = app(ws_ex3())
    executar(abrir(janela, "Estat", "Estatísticas básicas", "Exibição de estatísticas descritivas"))
    executar(abrir(janela, "Gráfico", "", "Boxplot"), "Desenhar")
    abas = janela.painel_sessao.abas
    assert abas.count() == 2
    abas.tabCloseRequested.emit(0)
    assert len(saida()) == 1 and abas.count() == 1
    janela.painel_sessao.botao_limpar.click()
    assert saida() == [] and abas.count() == 0


def test_sessao_exporta_html_autocontido():
    """O plotly.js vai embutido: nenhuma tag script aponta para fora (sem CDN)."""
    import re

    from statlab.relatorio import para_html

    dialogo = abrir(app(ws_ex3()), "Gráfico", "", "Boxplot")
    executar(dialogo, "Desenhar")
    html = para_html(saida())
    assert "<html" in html
    assert re.findall(r'<script[^>]*src="https?://', html) == []


def test_assistente_indica_o_comando_sem_analisar():
    dialogo = abrir(app(ws_ex3()), "Assistente", "", "Qual teste usar?")
    sem_erros(dialogo)
    assert any("Qual é o objetivo?" in t for t in textos(dialogo))
    assert saida() == [], "o assistente não produz análise"
