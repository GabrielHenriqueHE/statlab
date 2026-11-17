"""Qui-quadrado: independência (tabela de contingência) e aderência (qualidade do ajuste).

Não está na apostila revisada. Critério das contagens esperadas (Cochran, usado em livros e no Minitab):
nenhuma célula com esperado < 1 e no máximo 20% das células com esperado < 5. Se falhar numa tabela 2 × 2,
usa-se o exato de Fisher; em tabelas maiores, a recomendação é agrupar categorias.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.resultados import ALPHA_PADRAO, ATENCAO, OK, Resultado, Verificacao

AVISO_FORA_APOSTILA = "O qui-quadrado não faz parte da apostila revisada; confirme com o professor se for cobrado."


@dataclass(kw_only=True)
class QuiQuadrado(Resultado):
    observados: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    esperados: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    linhas: list[str] = field(default_factory=list)
    colunas: list[str] = field(default_factory=list)
    razao_verossimilhanca: tuple[float, float] | None = None  # (G², p)
    p_fisher: float | None = None


def tabela_contingencia(df: pd.DataFrame, col_linhas: str, col_colunas: str) -> pd.DataFrame:
    """Contagens cruzadas de duas colunas categóricas (linhas com faltante são ignoradas)."""
    for c in (col_linhas, col_colunas):
        if c not in df.columns:
            raise ErroDeDados(f"Coluna {c!r} não existe nesta worksheet.")
    if col_linhas == col_colunas:
        raise ErroDeDados("Escolha duas colunas diferentes.")
    dados = df[[col_linhas, col_colunas]].dropna().astype(str)
    if dados.empty:
        raise ErroDeDados("Não há linhas com as duas colunas preenchidas.")
    return pd.crosstab(dados[col_linhas], dados[col_colunas])


def _criterio_cochran(esperados: np.ndarray) -> tuple[bool, str]:
    abaixo5 = int((esperados < 5).sum())
    total = esperados.size
    minimo = float(esperados.min())
    ok = minimo >= 1 and abaixo5 <= 0.2 * total
    detalhe = f"{abaixo5} de {total} célula(s) com esperado < 5; menor esperado = {num(minimo)}"
    return ok, detalhe


def _matriz(tabela: Sequence[Sequence[float]] | pd.DataFrame) -> tuple[np.ndarray, list[str], list[str]]:
    if isinstance(tabela, pd.DataFrame):
        obs = tabela.to_numpy(dtype=float)
        linhas = [str(i) for i in tabela.index]
        colunas = [str(c) for c in tabela.columns]
    else:
        obs = np.asarray(tabela, dtype=float)
        linhas = [f"L{i + 1}" for i in range(obs.shape[0])] if obs.ndim == 2 else []
        colunas = [f"C{j + 1}" for j in range(obs.shape[1])] if obs.ndim == 2 else []
    if obs.ndim != 2 or obs.shape[0] < 2 or obs.shape[1] < 2:
        raise ErroDeDados("A tabela de contingência precisa de pelo menos 2 linhas e 2 colunas.")
    if np.isnan(obs).any():
        raise ErroDeDados("A tabela tem células vazias; preencha todas as contagens.")
    if (obs < 0).any() or not np.allclose(obs, np.round(obs)):
        raise ErroDeDados("As contagens devem ser inteiros não negativos.")
    if (obs.sum(axis=0) == 0).any() or (obs.sum(axis=1) == 0).any():
        raise ErroDeDados("Há linha ou coluna com total zero; remova-a da tabela.")
    return obs, linhas, colunas


def independencia(
    tabela: Sequence[Sequence[float]] | pd.DataFrame,
    *,
    metodo: str = "chi2",
    alpha: float = ALPHA_PADRAO,
) -> QuiQuadrado:
    """Associação entre duas variáveis categóricas na tabela de contingência.

    ``metodo="chi2"``: qui-quadrado de Pearson, sem correção de Yates (como o Minitab), com a razão
    de verossimilhança como conferência. ``metodo="fisher"``: teste exato de Fisher (tabela 2 × 2).
    O critério de Cochran é reportado como diagnóstico — não troca o método.
    """
    if metodo not in ("chi2", "fisher"):
        raise ErroDeDados(f"Método desconhecido: {metodo!r}. Use 'chi2' ou 'fisher'.")
    obs, linhas, colunas = _matriz(tabela)
    chi2, p, gl, esperados = stats.chi2_contingency(obs, correction=False)
    g2, p_g2, _, _ = stats.chi2_contingency(obs, correction=False, lambda_="log-likelihood")
    ok, detalhe = _criterio_cochran(esperados)
    verif = [
        Verificacao(
            nome="Contagens esperadas (critério de Cochran)",
            status=OK if ok else ATENCAO,
            detalhe=detalhe,
        )
    ]
    avisos = [AVISO_FORA_APOSTILA]

    if metodo == "fisher":
        if obs.shape != (2, 2):
            raise ErroDeDados(
                f"O exato de Fisher aqui exige uma tabela 2 × 2 (a sua é {obs.shape[0]} × {obs.shape[1]})."
            )
        p_fisher = float(stats.fisher_exact(obs.astype(int)).pvalue)
        nome, estat, rot, p_dec, gl_dec = "Teste exato de Fisher (2 × 2)", None, "", p_fisher, None
        passos = [
            "H₀: as duas variáveis são independentes; H₁: há associação entre elas",
            f"Exato de Fisher (2 × 2): p {p_valor(p_fisher)}",
        ]
    else:
        p_fisher = None
        nome, estat, rot, p_dec, gl_dec = "Qui-quadrado de independência", float(chi2), "χ²", float(p), gl
        passos = [
            "H₀: as duas variáveis são independentes; H₁: há associação entre elas",
            f"χ² de Pearson = {num(float(chi2), 3)}; gl = {int(gl)}; p {p_valor(float(p))}",
            f"Razão de verossimilhança G² = {num(float(g2), 3)}; p {p_valor(float(p_g2))} (conferência)",
        ]
        if not ok:
            avisos.append(
                "Há contagens esperadas pequenas (veja o critério de Cochran): o χ² fica menos confiável. "
                "Numa tabela 2 × 2, o exato de Fisher é uma alternativa; em tabelas maiores, agrupar "
                "categorias é o caminho usual."
            )

    return QuiQuadrado(
        nome=nome,
        alpha=alpha,
        estatistica=estat,
        rotulo_estatistica=rot,
        gl=None if gl_dec is None else (float(gl_dec),),
        p=p_dec,
        n=int(obs.sum()),
        observados=obs,
        esperados=np.asarray(esperados, dtype=float),
        linhas=linhas,
        colunas=colunas,
        razao_verossimilhanca=(float(g2), float(p_g2)),
        p_fisher=p_fisher,
        verificacoes=verif,
        passos=passos,
        avisos=avisos,
    )


def aderencia(
    observados: Sequence[float],
    *,
    categorias: Sequence[str] | None = None,
    proporcoes: Sequence[float] | None = None,
    alpha: float = ALPHA_PADRAO,
) -> QuiQuadrado:
    """Qualidade do ajuste: compara contagens observadas com proporções esperadas (iguais, se omitidas)."""
    obs = np.asarray(observados, dtype=float)
    k = len(obs)
    if k < 2:
        raise ErroDeDados("O teste de aderência precisa de pelo menos 2 categorias.")
    if np.isnan(obs).any() or (obs < 0).any() or not np.allclose(obs, np.round(obs)):
        raise ErroDeDados("As contagens observadas devem ser inteiros não negativos, sem células vazias.")
    total = obs.sum()
    if total <= 0:
        raise ErroDeDados("A soma das contagens observadas deve ser positiva.")
    if proporcoes is None:
        props = np.full(k, 1 / k)
    else:
        props = np.asarray(proporcoes, dtype=float)
        if len(props) != k or np.isnan(props).any() or (props <= 0).any():
            raise ErroDeDados("Informe uma proporção esperada positiva para cada categoria.")
        props = props / props.sum()
    esperados = total * props
    chi2, p = stats.chisquare(obs, f_exp=esperados)
    ok, detalhe = _criterio_cochran(esperados)
    cats = [str(c) for c in categorias] if categorias is not None else [f"C{i + 1}" for i in range(k)]
    return QuiQuadrado(
        nome="Qui-quadrado de aderência",
        alpha=alpha,
        estatistica=float(chi2),
        rotulo_estatistica="χ²",
        gl=(float(k - 1),),
        p=float(p),
        n=int(total),
        observados=obs.reshape(1, -1),
        esperados=esperados.reshape(1, -1),
        linhas=["Contagem"],
        colunas=cats,
        verificacoes=[
            Verificacao(
                nome="Contagens esperadas (critério de Cochran)",
                status=OK if ok else ATENCAO,
                detalhe=detalhe,
            )
        ],
        passos=[
            "H₀: os dados seguem as proporções esperadas; H₁: não seguem",
            "Proporções esperadas: " + "; ".join(f"{c} = {num(q, 4)}" for c, q in zip(cats, props, strict=True)),
            f"χ² = {num(float(chi2), 3)}; gl = {k - 1}; p {p_valor(float(p))}",
        ],
        avisos=[AVISO_FORA_APOSTILA],
    )
