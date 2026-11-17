"""Interface dos itens do backlog: teste de sinal, página Variâncias, covariância, recodificar e Como usar."""

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from tests.helpers import pdf
from tests.ui_util import UI, app, metrica, sem_erros, worksheet


def test_pagina_variancias_sem_worksheet_orienta():
    at = app("variancias.py")
    sem_erros(at)
    assert at.info


def test_variancias_igualdade_dois_grupos_usa_f_do_pdf():
    d = pdf()["ex5_apf"]
    at = app("variancias.py", {"APF": worksheet(G1=d["g1"], G2=d["g2"])})
    sem_erros(at)
    assert metrica(at, "F") == "1,277"  # PDF: F = 1,277; p = 0,774
    assert "0,774" in [m.value for m in at.metric]
    assert any("Igualdade de variâncias (F)" in s.value for s in at.subheader)


def test_variancias_uma_variancia_mostra_qui_quadrado():
    v = [9.8, 10.1, 10.4, 9.7, 10.0, 10.3, 9.9, 10.2, 10.6, 9.5]
    at = app("variancias.py", {"W": worksheet(Peso=v)})
    at.number_input(key="v1_sigma0").set_value(0.1).run()
    sem_erros(at)
    s2 = np.var(v, ddof=1)
    assert metrica(at, "χ²") == f"{9 * s2 / 0.01:.3f}".replace(".", ",")
    assert metrica(at, "gl") == "9"


def test_uma_amostra_aba_sinal():
    at = app("uma_amostra.py", {"W": worksheet(Tempo=[20, 22, 25, 26, 27, 28, 29, 30, 31, 33, 34, 35])})
    at.number_input(key="s1_m0").set_value(21.0).run()
    sem_erros(at)
    assert any("Teste de sinal" in s.value for s in at.subheader)
    assert any("mediana de Tempo" in m.value for m in at.markdown)


def test_descritiva_mostra_covariancia_com_duas_variaveis():
    d = pdf()["ex1_publicidade"]
    at = app("descritiva.py", {"P": worksheet(x=d["x"], y=d["y"])})
    at.multiselect(key="desc_vars").set_value(["x", "y"]).run()
    sem_erros(at)
    assert any(s.value == "Covariância" for s in at.subheader)


def test_dados_recodificar_sem_novo_valor_mostra_erro_amigavel():
    df = pd.DataFrame({"Turno": [1.0, 2.0, 3.0, 1.0], "Tempo": [5.0, 6.0, 7.0, 8.0]})
    at = app("dados.py", {"T": df})
    at.selectbox(key="rec_coluna").set_value("Turno").run()
    at.button(key="btn_recodificar").click().run()
    sem_erros(at, esperando_mensagem=True)
    assert any("pelo menos um" in e.value for e in at.error)


def test_dados_recodificar_coluna_continua_avisa():
    df = pd.DataFrame({"Medida": np.linspace(0, 1, 80)})
    at = app("dados.py", {"M": df})
    sem_erros(at)
    assert any("valores distintos" in w.value for w in at.warning)


def test_pagina_como_usar_abre():
    at = app("ajuda.py")
    sem_erros(at)
    assert any("Regras de decisão" in s.value for s in at.subheader)


def test_app_tem_as_paginas_novas():
    fonte = (UI / "app.py").read_text(encoding="utf-8")
    assert "paginas/variancias.py" in fonte and "paginas/ajuda.py" in fonte
    at = AppTest.from_file(str(UI / "app.py"), default_timeout=60).run()
    sem_erros(at)
