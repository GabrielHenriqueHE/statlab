"""Regressão múltipla e ANOVA de 2 fatores: aceitação contra a saída do Minitab (Getting Started, cap. 5)."""

import numpy as np
import pandas as pd
import pytest

from statlab.core.anova_dois_fatores import analisar_anova_dois_fatores
from statlab.core.dados import ErroDeDados
from statlab.core.regressao_multipla import analisar_regressao_multipla, prever_multipla
from statlab.core.resultados import ATENCAO, FALHA, OK
from tests.helpers import aprox, carregar, p_menor_que, pdf
from tests.ui_util import abrir, app, executar, linhas_da_saida, saida, sem_erros


def _doe() -> pd.DataFrame:
    return pd.DataFrame(carregar("minitab_exemplos.json")["doe_horas"])


ESPERADO = carregar("minitab_exemplos.json")["doe_horas_esperado"]


def _doe_codificado() -> pd.DataFrame:
    """Codificação do Minitab: nível inferior (Novo, A) = −1; superior (Atual, B) = +1."""
    df = _doe()
    df["SP"] = np.where(df["SistemaPedidos"] == "Atual", 1.0, -1.0)
    df["PC"] = np.where(df["Pacote"] == "B", 1.0, -1.0)
    df["SPxPC"] = df["SP"] * df["PC"]
    return df


# --------------------------------------------------------------------------- ANOVA de 2 fatores


def test_anova2_reproduz_tabela_do_minitab():
    r = analisar_anova_dois_fatores(_doe(), "Horas", "SistemaPedidos", "Pacote")
    linhas = {lin.fonte: lin for lin in r.tabela}
    for fonte, chave in (
        ("SistemaPedidos", "sist_pedido"),
        ("Pacote", "pacote"),
        ("SistemaPedidos*Pacote", "interacao"),
    ):
        gl, sq, qm, f, _ = ESPERADO[chave]
        assert linhas[fonte].gl == gl
        aprox(linhas[fonte].sq, sq, 3)
        aprox(linhas[fonte].qm, qm, 4)
        aprox(linhas[fonte].f, f, 2)
    aprox(linhas["SistemaPedidos*Pacote"].p, 0.002, 3)
    p_menor_que(linhas["SistemaPedidos"].p)
    assert linhas["Erro"].gl == 8
    aprox(linhas["Erro"].sq, 3.571, 3)
    aprox(linhas["Total"].sq, 57.464, 3)
    aprox(r.s, ESPERADO["S"], 6)
    aprox(r.r2 * 100, ESPERADO["R2"], 2)
    aprox(r.r2_aj * 100, ESPERADO["R2aj"], 2)
    assert r.balanceado


def test_anova2_medias_para_os_graficos_fatoriais():
    r = analisar_anova_dois_fatores(_doe(), "Horas", "SistemaPedidos", "Pacote")
    # Getting Started p. 46: Novo + B ≈ 9 horas; Atual + A ≈ 14,5 horas
    aprox(r.medias_celulas[("Novo", "B")], 9.0, 0)
    assert r.medias_celulas[("Atual", "A")] == pytest.approx(14.4167, abs=1e-3)
    assert r.medias_a["Atual"] - r.medias_a["Novo"] == pytest.approx(3.097, abs=5e-4)  # efeito (p. 43)


def test_anova2_interacao_significativa_gera_aviso():
    r = analisar_anova_dois_fatores(_doe(), "Horas", "SistemaPedidos", "Pacote")
    assert any("interação é significativa" in a for a in r.avisos)


def test_anova2_sem_interacao_tem_duas_fontes():
    r = analisar_anova_dois_fatores(_doe(), "Horas", "SistemaPedidos", "Pacote", interacao=False)
    assert [lin.fonte for lin in r.tabela] == ["SistemaPedidos", "Pacote", "Erro", "Total"]
    assert r.tabela[2].gl == 9


def test_anova2_sem_replicas_com_interacao_erro_claro():
    df = _doe().drop_duplicates(subset=["SistemaPedidos", "Pacote"])
    with pytest.raises(ErroDeDados, match="réplicas"):
        analisar_anova_dois_fatores(df, "Horas", "SistemaPedidos", "Pacote")


def test_anova2_desbalanceado_avisa():
    df = _doe().drop(index=[0])
    r = analisar_anova_dois_fatores(df, "Horas", "SistemaPedidos", "Pacote")
    assert not r.balanceado
    assert any("desbalanceado" in a for a in r.avisos)


def test_anova2_verificacoes_presentes():
    r = analisar_anova_dois_fatores(_doe(), "Horas", "SistemaPedidos", "Pacote")
    nomes = [v.nome for v in r.verificacoes]
    assert nomes[0] == "Normalidade — resíduos"
    assert nomes[1].startswith("Variâncias semelhantes")


@pytest.mark.parametrize(
    "args, msg",
    [
        (("Horas", "Pacote", "Pacote"), "três colunas diferentes"),
        (("Pacote", "SistemaPedidos", "Horas"), "numérica"),
        (("Horas", "SistemaPedidos", "Inexiste"), "não existe"),
    ],
)
def test_anova2_entradas_invalidas(args, msg):
    with pytest.raises(ErroDeDados, match=msg):
        analisar_anova_dois_fatores(_doe(), *args)


# --------------------------------------------------------------------------- regressão múltipla


def test_regressao_multipla_reproduz_coeficientes_do_minitab():
    r = analisar_regressao_multipla(_doe_codificado(), "Horas", ["SP", "PC", "SPxPC"])
    coefs = {c.termo: c for c in r.coeficientes}
    for termo, chave in (
        ("Constante", "constante"),
        ("SP", "coef_sist_pedido"),
        ("PC", "coef_pacote"),
        ("SPxPC", "coef_interacao"),
    ):
        coef, ep, t = ESPERADO[chave]
        aprox(coefs[termo].coef, coef, 3)
        aprox(coefs[termo].ep, ep, 3)
        aprox(coefs[termo].t, t, 2)
    for termo in ("SP", "PC", "SPxPC"):
        aprox(coefs[termo].vif, 1.00, 2)
    aprox(r.s, ESPERADO["S"], 6)
    aprox(r.r2 * 100, ESPERADO["R2"], 2)
    aprox(r.r2_aj * 100, ESPERADO["R2aj"], 2)
    aprox(r.r2_pred * 100, ESPERADO["R2pred"], 2)
    assert r.equacao == "Horas = 12,5733 + 1,5483·SP − 1,1600·PC + 0,8650·SPxPC"


def test_regressao_multipla_predicao_do_minitab():
    r = analisar_regressao_multipla(_doe_codificado(), "Horas", ["SP", "PC", "SPxPC"])
    ajuste, ep, ic_lo, ic_hi, ip_lo, ip_hi = ESPERADO["predicao_novo_b"]
    prev = prever_multipla(r, {"SP": -1, "PC": 1, "SPxPC": -1})
    aprox(prev.ajuste, ajuste, 0)
    aprox(prev.ep_ajuste, ep, 6)
    aprox(prev.ic[0], ic_lo, 5)
    aprox(prev.ic[1], ic_hi, 5)
    aprox(prev.ip[0], ip_lo, 5)
    aprox(prev.ip[1], ip_hi, 4)
    assert prev.aviso is None


def test_regressao_multipla_com_um_x_igual_a_simples_da_apostila():
    """PDF exemplo 1: a = 4,70; b = 12,20; r² = 0,951."""
    d = pdf()["ex1_publicidade"]
    df = pd.DataFrame({"x": d["x"], "y": d["y"]})
    r = analisar_regressao_multipla(df, "y", ["x"])
    coefs = {c.termo: c for c in r.coeficientes}
    aprox(coefs["Constante"].coef, 12.20, 2)
    aprox(coefs["x"].coef, 4.70, 2)
    aprox(r.r2, 0.951, 3)
    assert r.nome == "Regressão linear"


def test_regressao_multipla_extrapolacao_avisa():
    r = analisar_regressao_multipla(_doe_codificado(), "Horas", ["SP", "PC", "SPxPC"])
    prev = prever_multipla(r, {"SP": 3, "PC": 1, "SPxPC": 3})
    assert prev.aviso is not None and "SP" in prev.aviso


def test_regressao_multipla_multicolinearidade_vif():
    rng = np.random.default_rng(0)
    x1 = rng.normal(size=40)
    df = pd.DataFrame({"x1": x1, "x2": x1 + rng.normal(scale=0.05, size=40), "y": x1 + rng.normal(size=40)})
    r = analisar_regressao_multipla(df, "y", ["x1", "x2"])
    vif = next(v for v in r.verificacoes if v.nome.startswith("Multicolinearidade"))
    assert vif.status == FALHA


def test_regressao_multipla_independentes_vif_ok():
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"a": rng.normal(size=50), "b": rng.normal(size=50)})
    df["y"] = 2 * df["a"] - df["b"] + rng.normal(scale=0.5, size=50)
    r = analisar_regressao_multipla(df, "y", ["a", "b"])
    assert next(v for v in r.verificacoes if v.nome.startswith("Multicolinearidade")).status == OK
    assert r.significativo


def test_regressao_multipla_residuo_grande_marcado():
    df = pd.DataFrame({"x": np.arange(12, dtype=float), "y": np.r_[np.arange(11, dtype=float), 40.0]})
    r = analisar_regressao_multipla(df, "y", ["x"])
    assert next(v for v in r.verificacoes if v.nome.startswith("Resíduos grandes")).status == ATENCAO


@pytest.mark.parametrize(
    "preditores, msg",
    [([], "pelo menos um preditor"), (["y"], "não pode estar"), (["x", "x2"], "perfeitamente correlacionados")],
)
def test_regressao_multipla_entradas_invalidas(preditores, msg):
    df = pd.DataFrame({"x": [1.0, 2, 3, 4, 5], "x2": [2.0, 4, 6, 8, 10], "y": [1.0, 3, 2, 5, 4]})
    with pytest.raises(ErroDeDados, match=msg):
        analisar_regressao_multipla(df, "y", preditores)


def test_regressao_multipla_poucas_linhas():
    df = pd.DataFrame({"a": [1.0, 2, 3], "b": [3.0, 1, 2], "y": [1.0, 2, 4]})
    with pytest.raises(ErroDeDados, match="insuficientes"):
        analisar_regressao_multipla(df, "y", ["a", "b"])


# --------------------------------------------------------------------------- telas (comandos)


def test_comando_anova2_com_dados_do_guia():
    at = abrir(app({"DOE": _doe()}), "Estat", "ANOVA", "Dois fatores")
    at.selectbox(key="a2_a").set_value("SistemaPedidos").run()
    at.selectbox(key="a2_b").set_value("Pacote").run()
    at = executar(at)
    sem_erros(at)
    item = saida(at)[-1]
    tabela = dict(item.tabelas)["Análise de variância (SQ ajustadas)"]
    assert list(tabela["Valor F"][:3]) == ["64,46", "36,18", "20,12"]
    assert "R² = 93,79%" in linhas_da_saida(at)


def test_comando_anova2_sem_replicas_mostra_erro():
    df = _doe().drop_duplicates(subset=["SistemaPedidos", "Pacote"])
    at = abrir(app({"DOE": df}), "Estat", "ANOVA", "Dois fatores")
    at.selectbox(key="a2_a").set_value("SistemaPedidos").run()
    at.selectbox(key="a2_b").set_value("Pacote").run()
    at = executar(at)
    sem_erros(at, esperando_mensagem=True)
    assert any("réplicas" in e.value for e in at.error)
    assert saida(at) == [], "nada foi para a sessão"


def test_comando_regressao_multipla_com_dados_do_guia():
    df = _doe_codificado()[["SP", "PC", "SPxPC", "Horas"]]
    at = abrir(app({"DOE": df}), "Estat", "Regressão", "Regressão múltipla")
    at.selectbox(key="rm_y").set_value("Horas").run()
    at.multiselect(key="rm_x").set_value(["SP", "PC", "SPxPC"]).run()
    at.checkbox(key="rm_prev").set_value(True).run()
    at.number_input(key="rm_v_SP").set_value(-1.0)
    at.number_input(key="rm_v_PC").set_value(1.0)
    at.number_input(key="rm_v_SPxPC").set_value(-1.0).run()
    at = executar(at)
    sem_erros(at)
    texto = linhas_da_saida(at)
    assert "R²(pred) = 86,02%" in texto
    assert "Horas = 12,5733" in texto
    assert "IC = (8,11; 9,89)" in texto


def test_comando_regressao_simples_e_a_multipla_com_um_preditor():
    """A regressão simples reproduz a reta da apostila (PDF Ex. 1: a = 4,70; b = 12,20)."""
    d = pdf()["ex1_publicidade"]
    at = abrir(app({"Pub": pd.DataFrame({"x": d["x"], "y": d["y"]})}), "Estat", "Regressão", "Regressão simples")
    at.selectbox(key="rs_y").set_value("y").run()
    at.selectbox(key="rs_x").set_value("x").run()
    at = executar(at)
    sem_erros(at)
    coefs = dict(saida(at)[-1].tabelas)["Coeficientes"]
    assert list(coefs["Termo"]) == ["Constante", "x"]
    assert coefs["Coef"][0].startswith("12,20")
    assert coefs["Coef"][1].startswith("4,70")
