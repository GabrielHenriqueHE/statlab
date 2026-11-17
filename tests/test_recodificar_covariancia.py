"""Recodificar valores (Dados › Recodificar) e matriz de covariância (Estat › Covariância)."""

import numpy as np
import pandas as pd
import pytest

from statlab.core import tabela
from statlab.core.dados import ErroDeDados
from statlab.core.descritiva import matriz_covariancia
from tests.helpers import pdf

# --------------------------------------------------------------------------- recodificar


def test_recodificar_texto_para_numero_com_virgula():
    s = pd.Series(["A", "B", None, "A", "C"])
    nova, trocados = tabela.recodificar(s, {"A": "1", "B": "2,5", "C": ""})
    # C sem novo valor fica "C" → a coluna não pode ser numérica
    assert nova.tolist() == ["1", "2,5", None, "1", "C"]
    nova, trocados = tabela.recodificar(s, {"A": "1", "B": "2,5", "C": "3"})
    assert pd.api.types.is_float_dtype(nova)
    assert nova.tolist()[:2] == [1.0, 2.5] and np.isnan(nova.iloc[2])
    assert trocados == 4


def test_recodificar_codigo_numerico_para_rotulo():
    s = pd.Series([1.0, 2.0, 3.0, np.nan, 2.0])
    assert tabela.valores_distintos(s) == ["1", "2", "3"]
    nova, trocados = tabela.recodificar(s, {"1": "Manhã", "2": "Tarde", "3": "Noite"})
    assert nova.tolist() == ["Manhã", "Tarde", "Noite", None, "Tarde"]
    assert trocados == 4


def test_recodificar_sem_nenhum_novo_valor_e_erro():
    with pytest.raises(ErroDeDados):
        tabela.recodificar(pd.Series(["a", "b"]), {"a": " ", "b": ""})


# --------------------------------------------------------------------------- covariância


def test_covariancia_confere_com_numpy_e_com_a_correlacao():
    d = pdf()["ex1_publicidade"]
    df = pd.DataFrame({"x": d["x"], "y": d["y"]})
    cov, n = matriz_covariancia(df, ["x", "y"])
    esperado = np.cov(df["x"], df["y"], ddof=1)
    assert cov.to_numpy() == pytest.approx(esperado)
    r = cov.loc["x", "y"] / np.sqrt(cov.loc["x", "x"] * cov.loc["y", "y"])
    assert r == pytest.approx(np.corrcoef(df["x"], df["y"])[0, 1])
    assert (n.to_numpy() == len(df)).all()


def test_covariancia_usa_pares_completos_por_par():
    df = pd.DataFrame({"a": [1, 2, 3, 4, np.nan], "b": [2.0, 4, 5, 9, 1], "c": [1.0, 0, 1, 0, 1]})
    cov, n = matriz_covariancia(df, ["a", "b", "c"])
    assert n.loc["a", "b"] == 4 and n.loc["b", "c"] == 5
    assert cov.loc["a", "b"] == pytest.approx(np.cov([1, 2, 3, 4], [2, 4, 5, 9])[0, 1])
    assert cov.loc["b", "b"] == pytest.approx(np.var([2, 4, 5, 9, 1], ddof=1))


def test_covariancia_exige_duas_colunas():
    with pytest.raises(ErroDeDados):
        matriz_covariancia(pd.DataFrame({"a": [1, 2, 3]}), ["a"])
