"""Operações sobre worksheets (DataFrames): empilhar, desempilhar e pares completos.

Equivalentes ao menu Dados do Minitab (Empilhamento, Desempilhamento e subconjuntos de colunas).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from statlab.core.dados import ErroDeDados


def colunas_numericas(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def colunas_texto(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]


def faltantes_por_coluna(df: pd.DataFrame) -> pd.DataFrame:
    """Resumo por coluna: quantos valores estão preenchidos e quantos faltam."""
    return pd.DataFrame(
        {
            "coluna": list(df.columns),
            "tipo": ["numérico" if pd.api.types.is_numeric_dtype(df[c]) else "texto" for c in df.columns],
            "preenchidos": [int(df[c].notna().sum()) for c in df.columns],
            "faltantes": [int(df[c].isna().sum()) for c in df.columns],
        }
    )


def empilhar(
    df: pd.DataFrame,
    colunas: Sequence[str],
    *,
    nome_resposta: str = "Dados",
    nome_subscritos: str = "Subscritos",
) -> tuple[pd.DataFrame, int]:
    """Empilha colunas em uma só (resposta + subscrito com o nome da coluna de origem).

    Faltantes são descartados. Devolve ``(tabela, faltantes_descartados)``.
    """
    colunas = list(colunas)
    if len(colunas) < 2:
        raise ErroDeDados("Para empilhar, escolha pelo menos 2 colunas.")
    if nome_resposta == nome_subscritos:
        raise ErroDeDados("Os nomes da coluna de resposta e do subscrito devem ser diferentes.")
    partes = []
    descartados = 0
    for c in colunas:
        if c not in df.columns:
            raise ErroDeDados(f"Coluna {c!r} não existe nesta worksheet.")
        s = df[c]
        descartados += int(s.isna().sum())
        valores = s.dropna().to_numpy()
        partes.append(pd.DataFrame({nome_resposta: valores, nome_subscritos: np.repeat(c, len(valores))}))
    return pd.concat(partes, ignore_index=True), descartados


def desempilhar(
    df: pd.DataFrame,
    resposta: str,
    subscritos: str,
) -> tuple[pd.DataFrame, list[str]]:
    """Separa a resposta em uma coluna por nível do subscrito (colunas mais curtas ficam com faltantes).

    Devolve ``(tabela, níveis)``, na ordem em que aparecem.
    """
    for c in (resposta, subscritos):
        if c not in df.columns:
            raise ErroDeDados(f"Coluna {c!r} não existe nesta worksheet.")
    if resposta == subscritos:
        raise ErroDeDados("A resposta e o subscrito precisam ser colunas diferentes.")
    dados = df[[resposta, subscritos]].dropna(subset=[subscritos])
    if dados.empty:
        raise ErroDeDados("Não há níveis de subscrito preenchidos para desempilhar.")
    grupos: dict[str, pd.Series] = {}
    for nivel, sub in dados.groupby(subscritos, sort=False):
        grupos[str(nivel)] = sub[resposta].dropna().reset_index(drop=True)
    tabela = pd.DataFrame(grupos)
    return tabela, list(grupos)


def pares_completos(df: pd.DataFrame, colunas: Sequence[str]) -> tuple[pd.DataFrame, int]:
    """Mantém só as linhas em que todas as colunas escolhidas estão preenchidas.

    Devolve ``(tabela, linhas_descartadas)``.
    """
    colunas = list(colunas)
    if not colunas:
        raise ErroDeDados("Escolha ao menos uma coluna.")
    completo = df.dropna(subset=colunas)
    return completo.reset_index(drop=True), int(len(df) - len(completo))
