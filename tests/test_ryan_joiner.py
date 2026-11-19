"""Ryan-Joiner (opção do Minitab): estatística, p pela tabela da apostila, limites e título do gráfico."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from statlab import graficos
from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import (
    anderson_darling,
    coeficientes_ryan_joiner,
    estatistica_ryan_joiner,
    p_ryan_joiner,
    ryan_joiner,
    shapiro_wilk,
)
from statlab.core.resultados import Resultado
from statlab.relatorio.relatorio import resumo_resultado


def _b(n: int) -> np.ndarray:
    i = np.arange(1, n + 1)
    return stats.norm.ppf((i - 0.375) / (n + 0.25))


def test_estatistica_e_a_correlacao_entre_dados_ordenados_e_escores():
    x = np.random.default_rng(1).exponential(size=25)
    esperado = np.corrcoef(np.sort(x), _b(len(x)))[0, 1]  # b tem média zero: a fórmula é essa correlação
    assert estatistica_ryan_joiner(x) == pytest.approx(esperado, rel=1e-12)


def test_dados_nos_escores_normais_dao_rp_um():
    assert estatistica_ryan_joiner(_b(30)) == pytest.approx(1.0, abs=1e-12)


def test_tabela_e_monotona_a_partir_de_9():
    for n in range(9, 301):
        c10, c05, c01 = coeficientes_ryan_joiner(n)
        assert c10 > c05 > c01, n


def test_tabela_continua_na_troca_de_faixa_n_50():
    a = coeficientes_ryan_joiner(49)
    b = coeficientes_ryan_joiner(50)
    assert all(abs(u - v) < 0.002 for u, v in zip(a, b, strict=True))


def test_p_nos_pontos_da_tabela():
    n = 40
    c10, c05, c01 = coeficientes_ryan_joiner(n)
    assert p_ryan_joiner(c05, n)[0] == pytest.approx(0.05, abs=1e-12)
    assert p_ryan_joiner(c10 - 1e-9, n)[0] == pytest.approx(0.10, abs=1e-6)
    assert p_ryan_joiner(c05 + (c10 - c05) / 2, n)[0] == pytest.approx(0.075)


def test_p_como_limite_fora_da_tabela():
    assert p_ryan_joiner(1.0, 50) == (0.10, ">")  # Rp acima de cor10: p > 0,10
    assert p_ryan_joiner(0.5, 50) == (0.01, "<")  # Rp abaixo de cor01: p < 0,01


def test_calibracao_sob_normalidade_com_n_50():
    rng = np.random.default_rng(2026)
    n = 50
    rejeicoes = sum(not ryan_joiner(rng.normal(size=n)).normal for _ in range(2000))
    assert 0.03 <= rejeicoes / 2000 <= 0.07


def test_rejeita_exponencial_e_aceita_normal_grande():
    rng = np.random.default_rng(7)
    assert not ryan_joiner(rng.exponential(size=40)).normal
    assert ryan_joiner(rng.normal(size=60)).normal


def test_resultado_completo_e_passos():
    x = np.random.default_rng(3).normal(size=60)
    r = ryan_joiner(x, alpha=0.05, nome="Peso")
    assert r.nome == "Ryan-Joiner"
    assert r.rotulo_estatistica == "Rp"
    assert r.n == 60
    assert r.p_limite == ""
    assert r.atende is r.normal
    assert any("Rp = " in s for s in r.passos)
    assert r.avisos == []


def test_alpha_fora_da_tabela_e_erro_de_dados():
    x = np.random.default_rng(4).normal(size=20)
    with pytest.raises(ErroDeDados, match="0,01 a 0,10"):
        ryan_joiner(x, alpha=0.2)
    with pytest.raises(ErroDeDados, match="0,01 a 0,10"):
        ryan_joiner(x, alpha=0.005)


def test_menos_de_9_observacoes_e_erro_de_dados():
    with pytest.raises(ErroDeDados):
        ryan_joiner(np.arange(8, dtype=float))


def test_aviso_factual_com_n_pequeno():
    x = np.random.default_rng(5).normal(size=15)
    assert any("n = 15" in a for a in ryan_joiner(x).avisos)


def test_significativo_respeita_o_limite_do_p():
    def res(p, limite, alpha):
        return Resultado(nome="x", p=p, p_limite=limite, alpha=alpha)

    assert res(0.10, ">", 0.05).significativo is False
    assert res(0.10, ">", 0.10).significativo is False  # p > 0,10 ≥ α
    assert res(0.10, ">", 0.20).significativo is None  # o limite não basta para decidir
    assert res(0.01, "<", 0.05).significativo is True
    assert res(0.01, "<", 0.01).significativo is True  # p < 0,01 ≤ α
    assert res(0.05, "", 0.05).significativo is True  # sem limite: regra p ≤ α


def test_resumo_mostra_o_limite_como_no_minitab():
    limite = Resultado(nome="Ryan-Joiner", p=0.10, p_limite=">", alpha=0.05, rotulo_estatistica="Rp", estatistica=0.99)
    assert "p > 0,10" in resumo_resultado(limite)
    exato = Resultado(nome="Ryan-Joiner", p=0.047, alpha=0.05)
    assert "p = 0,047" in resumo_resultado(exato)


def test_titulo_do_grafico_usa_o_teste_escolhido():
    x = np.random.default_rng(8).normal(size=30)
    titulo_sw = graficos.probabilidade_normal(x, teste=shapiro_wilk(x, tcl=False)).layout.title.text
    assert "Shapiro-Wilk W = " in titulo_sw
    assert "Anderson" not in titulo_sw
    titulo_rj = graficos.probabilidade_normal(x, teste=ryan_joiner(x)).layout.title.text
    assert "Ryan-Joiner Rp = " in titulo_rj
    assert ", p " in titulo_rj


def test_grafico_sem_teste_continua_com_anderson_darling():
    x = np.random.default_rng(9).normal(size=30)
    titulo = graficos.probabilidade_normal(x).layout.title.text
    assert titulo == (
        f"Probabilidade normal — Anderson-Darling A² = {num(anderson_darling(x).estatistica, 3)}, "
        f"p {p_valor(anderson_darling(x).p)}"
    )


@pytest.mark.parametrize(
    ("metodo", "trecho"),
    [("Ryan-Joiner (Minitab)", "Ryan-Joiner Rp = "), ("Shapiro-Wilk", "Shapiro-Wilk W = ")],
)
def test_comando_de_normalidade_anexa_o_grafico_do_metodo_escolhido(metodo, trecho):
    import pandas as pd

    from tests.ui_util import abrir, app, definir, executar, saida, sem_erros

    dados = pd.DataFrame({"x": np.random.default_rng(11).normal(size=40)})
    dialogo = abrir(app({"Dados": dados}), "Estat", "Estatísticas básicas", "Teste de normalidade")
    definir(dialogo, "norm_met", metodo)
    executar(dialogo)
    sem_erros(dialogo)
    item = saida()[-1]
    assert len(item.figuras) == 1
    assert trecho in item.figuras[0].layout.title.text
