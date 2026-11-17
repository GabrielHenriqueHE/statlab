"""F6: prática com o gerador da disciplina, conferência pelo statlab e regressões encontradas no caminho."""

import re
from pathlib import Path

import pytest

from statlab import pratica
from statlab.core.correlacao import analisar_correlacao
from statlab.core.testes_t import analisar_antes_depois, analisar_dois_grupos
from statlab.core.uma_amostra import analisar_uma_amostra
from statlab.pratica.gerador import GERADORES, gerar_lista
from statlab.ui import estado
from tests.ui_util import app, sem_erros

REF = Path(__file__).resolve().parents[1] / "docs" / "reference"


def _secoes(arquivo: str) -> list[str]:
    texto = (REF / arquivo).read_text(encoding="utf-8")
    return [s.strip() for s in re.split(r"\n## Exercício \d+ — [^\n]+\n\n", texto)[1:]]


@pytest.fixture(scope="module")
def lista_2026():
    return gerar_lista(10, list(GERADORES), 2026)


def test_copia_do_gerador_reproduz_enunciados_2026(lista_2026):
    assert [e.enunciado.strip() for e in lista_2026] == _secoes("exercicios_2026.md")


def test_copia_do_gerador_reproduz_gabarito_2026(lista_2026):
    assert [e.gabarito.strip() for e in lista_2026] == _secoes("gabarito_2026.md")


def test_statlab_concorda_com_o_gabarito_2026(lista_2026):
    for i, e in enumerate(lista_2026, 1):
        conf = pratica.conferir(e)
        assert conf.concorda, f"Ex. {i}: gerador {conf.teste_gerador} × statlab {conf.teste_statlab}"


@pytest.mark.parametrize("semente", range(20))
def test_statlab_concorda_com_o_gerador_em_outras_sementes(semente):
    for e in gerar_lista(10, list(GERADORES), semente):
        conf = pratica.conferir(e)
        assert conf.concorda, f"semente {semente}, {e.tipo}: {conf.teste_gerador} × {conf.teste_statlab}"


def test_worksheet_bruta_tem_os_extremos_do_enunciado(lista_2026):
    ex10 = pratica.worksheet_bruta(lista_2026[9])
    assert len(ex10) == 17  # o enunciado tem 17 pares (a planilha do gerador trazia 16)
    ex5 = pratica.worksheet_bruta(lista_2026[4])
    assert ex5["Turma tarde"].notna().sum() == 19  # inclui 37 e 38


def test_markdown_da_lista_e_do_gabarito(lista_2026):
    lista = pratica.lista_markdown(lista_2026, 2026)
    gab = pratica.gabarito_markdown(lista_2026, 2026)
    assert "*Semente: 2026.*" in lista and lista.count("## Exercício") == 10
    assert gab.startswith("# Gabarito") and "W = 0,0; p unilateral < 0,001" in gab


def test_gerar_valida_tipos():
    with pytest.raises(ValueError):
        pratica.gerar(3, ["inexistente"], 1)
    with pytest.raises(ValueError):
        pratica.gerar(3, [], 1)
    exs, semente = pratica.gerar(4, ["corr"], 7)
    assert semente == 7 and {e.tipo for e in exs} == {"corr"}


# --------------------------------------------------------------------------- regressões: sub-análise sem suave


def test_correlacao_sem_suave_constante_nao_derruba_a_analise():
    """Semente 11 do gerador: sem extremos e sem o suave, x fica [8, 8, 8]. Antes, a análise inteira caía."""
    x = [8.0, 14.0, 8.0, 4.0, 8.0, 9.0]
    y = [51.0, 55.0, 41.0, 122.0, 46.0, 55.0]
    r = analisar_correlacao(x, y)
    assert r.n == 4
    assert r.n_sem_suave is None
    assert any("fica sem variação" in a for a in r.avisos)


def test_pareado_sem_suave_constante_vira_aviso():
    r = analisar_antes_depois([18.0, 18.0, 18.0, 19.0], [10.0, 10.0, 10.0, 10.0])  # d = 8, 8, 8, 9
    assert r.n == 4
    assert any("sem variação" in a for a in r.avisos)


def test_dois_grupos_sem_suave_constante_vira_aviso():
    r = analisar_dois_grupos([8.0, 8.0, 8.0, 9.0], [1.0, 2.0, 3.0, 4.0, 5.0])
    assert r.p is not None
    assert any("sem variação" in a for a in r.avisos)


def test_uma_amostra_sem_suave_constante_nao_quebra():
    """Aqui o fluxo usa Wilcoxon (não normal), que roda sem o suave mesmo com [8, 8, 8]; o importante é não cair."""
    r = analisar_uma_amostra([8.0, 8.0, 8.0, 9.0], 7.0)
    assert r.p is not None
    assert any("Sem o(s) outlier(s) suave(s)" in a or "sem variação" in a for a in r.avisos)


# --------------------------------------------------------------------------- tela


def test_tela_pratica_inicial_orienta():
    at = app("pratica.py")
    sem_erros(at)
    assert any("Gerar lista" in i.value for i in at.info)


def test_tela_pratica_lista_2026_carrega_dados_e_confere():
    at = app("pratica.py")
    at.number_input(key="pr_n_ex").set_value(10)
    at.text_input(key="pr_semente").input("2026")
    at.button(key="pr_gerar").click().run()
    sem_erros(at)
    assert len(at.expander) == 10
    assert any("semente 2026" in s.value for s in at.subheader)
    at.button(key="pr_carregar_10").click().run()
    planilhas = at.session_state[estado.PLANILHAS]
    assert len(planilhas["Ex10 (semente 2026)"]) == 17
    at.toggle(key="pr_gab_10").set_value(True).run()
    sem_erros(at)
    assert any("o statlab também escolheu **Wilcoxon**" in s.value for s in at.success)


def test_tela_pratica_semente_invalida():
    at = app("pratica.py")
    at.text_input(key="pr_semente").input("abc")
    at.button(key="pr_gerar").click().run()
    sem_erros(at, esperando_mensagem=True)
    assert any("número inteiro" in e.value for e in at.error)
