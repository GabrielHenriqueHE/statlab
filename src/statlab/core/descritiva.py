"""Estatísticas descritivas e diagrama de caixa (quartis e outliers).

Quartis: ``method="linear"`` reproduz QUARTIL.INC do Excel (padrão deste projeto, e o usado nos
gabaritos). ``method="weibull"`` reproduz o Minitab; é uma opção, não o padrão.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

METODO_QUARTIS_PADRAO = "linear"  # = Excel QUARTIL.INC
METODO_QUARTIS_MINITAB = "weibull"


@dataclass(frozen=True)
class Descritiva:
    n: int
    media: float
    mediana: float
    dp: float
    variancia: float
    minimo: float
    maximo: float
    q1: float
    q3: float
    d: float  # amplitude interquartil (Q3 − Q1)


@dataclass(frozen=True)
class Outliers:
    """Classificação pelo diagrama de caixa. As máscaras têm o mesmo tamanho da amostra."""

    q1: float
    q3: float
    d: float
    suave: np.ndarray  # fora de [Q1 − 1,5D; Q3 + 1,5D], mas não extremo
    extremo: np.ndarray  # fora de [Q1 − 3D; Q3 + 3D]

    @property
    def tem_suave(self) -> bool:
        return bool(self.suave.any())

    @property
    def tem_extremo(self) -> bool:
        return bool(self.extremo.any())


def quartis(v: np.ndarray, metodo: str = METODO_QUARTIS_PADRAO) -> tuple[float, float]:
    q1, q3 = np.percentile(np.asarray(v, dtype=float), [25, 75], method=metodo)
    return float(q1), float(q3)


def descrever(v: np.ndarray, metodo: str = METODO_QUARTIS_PADRAO) -> Descritiva:
    """Resumo de uma amostra. Desvio padrão amostral (n − 1). Exige n ≥ 2 para o desvio."""
    v = np.asarray(v, dtype=float)
    if len(v) < 2:
        raise ValueError("descrever() precisa de pelo menos 2 observações.")
    q1, q3 = quartis(v, metodo)
    return Descritiva(
        n=len(v),
        media=float(v.mean()),
        mediana=float(np.median(v)),
        dp=float(v.std(ddof=1)),
        variancia=float(v.var(ddof=1)),
        minimo=float(v.min()),
        maximo=float(v.max()),
        q1=q1,
        q3=q3,
        d=q3 - q1,
    )


def detectar_outliers(v: np.ndarray, metodo: str = METODO_QUARTIS_PADRAO) -> Outliers:
    """Regra do diagrama de caixa: suave (1,5D) e extremo (3D). Extremo nunca é também suave."""
    v = np.asarray(v, dtype=float)
    q1, q3 = quartis(v, metodo)
    d = q3 - q1
    extremo = (v < q1 - 3 * d) | (v > q3 + 3 * d)
    suave = ((v < q1 - 1.5 * d) | (v > q3 + 1.5 * d)) & ~extremo
    return Outliers(q1=q1, q3=q3, d=d, suave=suave, extremo=extremo)


def sem_extremos(v: np.ndarray, out: Outliers) -> np.ndarray:
    """Amostra sem os outliers extremos (suaves permanecem)."""
    return np.asarray(v, dtype=float)[~out.extremo]


def texto_outliers(nome: str, v: np.ndarray, out: Outliers) -> str:
    """Linha de diagnóstico no padrão do gabarito (usada nos passos)."""
    from statlab.core.formatacao import lista, num

    txt = f"{nome}: Q1 = {num(out.q1)}; Q3 = {num(out.q3)}; D = {num(out.d)}; "
    if out.tem_extremo:
        txt += f"outlier extremo: {lista(np.asarray(v)[out.extremo])} (excluído da análise). "
    if out.tem_suave:
        txt += f"outlier suave: {lista(np.asarray(v)[out.suave])} (análise feita com e sem). "
    if not out.tem_extremo and not out.tem_suave:
        txt += "sem outliers."
    return txt.rstrip()
