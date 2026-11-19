"""Diferença entre colunas (Dados › Diferença entre colunas).

A coluna de diferenças é o que permite ao usuário rodar o teste de normalidade sobre as diferenças
de um par antes/depois — como manda a premissa do t pareado. O app não faz isso por conta própria:
o usuário cria a coluna e escolhe o comando.
"""

import numpy as np
import pandas as pd

from statlab.core import tabela
from statlab.core.normalidade import shapiro_wilk
from tests.helpers import aprox, pdf


def test_diferenca_linha_a_linha():
    df = pd.DataFrame({"antes": [1249.0, 1293.0, 1357.0], "depois": [1579.0, 1833.0, 1529.0]})
    valores, descartados = tabela.diferenca(df["depois"], df["antes"])
    assert list(valores) == [330.0, 540.0, 172.0]
    assert descartados == 0
    assert list(valores.index) == list(df.index)


def test_diferenca_inverte_com_a_ordem_escolhida():
    """Quem decide a direção é o usuário, nos dois seletores do diálogo."""
    df = pd.DataFrame({"antes": [10.0, 20.0], "depois": [14.0, 17.0]})
    b_menos_a, _ = tabela.diferenca(df["depois"], df["antes"])
    a_menos_b, _ = tabela.diferenca(df["antes"], df["depois"])
    assert list(b_menos_a) == [4.0, -3.0]
    assert list(a_menos_b) == [-4.0, 3.0]


def test_diferenca_faltante_em_qualquer_coluna_fica_faltante_e_e_reportada():
    df = pd.DataFrame({"antes": [1.0, np.nan, 3.0, np.nan], "depois": [2.0, 5.0, np.nan, np.nan]})
    valores, descartados = tabela.diferenca(df["depois"], df["antes"])
    assert valores[0] == 1.0
    assert valores.isna().tolist() == [False, True, True, True]
    assert descartados == 3
    assert len(valores) == len(df)  # a linha continua lá, só a diferença é que falta


def test_pdf_ex4_normalidade_da_coluna_de_diferencas():
    """O caminho completo do usuário: cria a coluna de diferenças e roda a normalidade nela."""
    d = pdf()["ex4_antes_depois"]
    df = pd.DataFrame({"antes": d["antes"], "depois": d["depois"]})
    valores, descartados = tabela.diferenca(df["antes"], df["depois"])
    assert descartados == 0
    aprox(shapiro_wilk(valores.to_numpy()).p, 0.537, 3)
