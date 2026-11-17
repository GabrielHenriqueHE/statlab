"""Regressão linear múltipla (mínimos quadrados), com a saída no formato do Minitab.

Fora da apostila (que cobre só a regressão simples). Saídas: coeficientes (EP, T, p, VIF), sumário do modelo
(S, R², R²(aj), R²(pred) pelo PRESS), ANOVA da regressão, diagnóstico dos resíduos e predição com IC e IP.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import shapiro_wilk
from statlab.core.resultados import ALPHA_PADRAO, ATENCAO, FALHA, OK, Resultado, Verificacao

AVISO_FORA_APOSTILA = "A regressão múltipla não faz parte da apostila revisada (que cobre a simples)."
VIF_ATENCAO = 5.0
VIF_FALHA = 10.0
RESIDUO_GRANDE = 2.0  # |resíduo padronizado| > 2: o Minitab marca com "R"


@dataclass(frozen=True)
class Coeficiente:
    termo: str
    coef: float
    ep: float
    t: float
    p: float
    vif: float | None  # None para a constante


@dataclass(frozen=True)
class Previsao:
    ajuste: float
    ep_ajuste: float
    ic: tuple[float, float]  # IC 95% da resposta média
    ip: tuple[float, float]  # IP 95% de uma observação nova
    aviso: str | None


@dataclass(kw_only=True)
class RegressaoMultipla(Resultado):
    resposta: str = ""
    preditores: list[str] = field(default_factory=list)
    coeficientes: list[Coeficiente] = field(default_factory=list)
    s: float = 0.0
    r2: float = 0.0
    r2_aj: float = 0.0
    r2_pred: float = 0.0
    sq_regressao: float = 0.0
    sq_residuo: float = 0.0
    sq_total: float = 0.0
    gl_regressao: int = 0
    gl_residuo: int = 0
    equacao: str = ""
    faixas: dict[str, tuple[float, float]] = field(default_factory=dict)
    ajustados: np.ndarray = field(default_factory=lambda: np.array([]))
    residuos: np.ndarray = field(default_factory=lambda: np.array([]))
    residuos_padronizados: np.ndarray = field(default_factory=lambda: np.array([]))
    modelo: Any = field(default=None, repr=False)


def _equacao(resposta: str, termos: Sequence[str], coefs: Sequence[float]) -> str:
    partes = [num(coefs[0], 4)]
    for termo, c in zip(termos, coefs[1:], strict=True):
        partes.append(f"{'+' if c >= 0 else '−'} {num(abs(c), 4)}·{termo}")
    return f"{resposta} = " + " ".join(partes)


def analisar_regressao_multipla(
    df: pd.DataFrame,
    resposta: str,
    preditores: Sequence[str],
    *,
    alpha: float = ALPHA_PADRAO,
) -> RegressaoMultipla:
    preditores = list(preditores)
    if not preditores:
        raise ErroDeDados("Escolha pelo menos um preditor (X).")
    if resposta in preditores:
        raise ErroDeDados("A resposta (Y) não pode estar entre os preditores.")
    colunas = [resposta, *preditores]
    for c in colunas:
        if c not in df.columns:
            raise ErroDeDados(f"Coluna {c!r} não existe nesta worksheet.")
        if not pd.api.types.is_numeric_dtype(df[c]):
            raise ErroDeDados(f"A coluna {c!r} não é numérica.")
    dados = df[colunas].dropna()
    descartadas = len(df) - len(dados)
    n, k = len(dados), len(preditores)
    if n <= k + 1:
        raise ErroDeDados(
            f"Observações insuficientes: com {k} preditor(es), são necessárias pelo menos {k + 2} "
            f"linhas completas (há {n})."
        )
    y = dados[resposta].to_numpy(dtype=float)
    x = dados[preditores].astype(float)
    for c in preditores:
        if float(np.ptp(x[c])) == 0.0:
            raise ErroDeDados(f"O preditor {c!r} não varia; retire-o do modelo.")
    if float(np.ptp(y)) == 0.0:
        raise ErroDeDados(f"A resposta {resposta!r} não varia.")
    xc = sm.add_constant(x, has_constant="add")
    if np.linalg.matrix_rank(xc.to_numpy()) < xc.shape[1]:
        raise ErroDeDados("Há preditores perfeitamente correlacionados (um é combinação dos outros); retire um deles.")

    modelo = sm.OLS(y, xc).fit()
    influencia = modelo.get_influence()
    h = influencia.hat_matrix_diag
    residuos = np.asarray(modelo.resid, dtype=float)
    padronizados = np.asarray(influencia.resid_studentized_internal, dtype=float)
    sq_total = float(np.sum((y - y.mean()) ** 2))
    press = float(np.sum((residuos / (1 - h)) ** 2))
    r2_pred = 1 - press / sq_total

    if k >= 2:
        matriz = xc.to_numpy()
        vifs = [float(variance_inflation_factor(matriz, i)) for i in range(1, k + 1)]
    else:
        vifs = [1.0]
    coefs = [
        Coeficiente(
            termo="Constante" if i == 0 else preditores[i - 1],
            coef=float(modelo.params.iloc[i]),
            ep=float(modelo.bse.iloc[i]),
            t=float(modelo.tvalues.iloc[i]),
            p=float(modelo.pvalues.iloc[i]),
            vif=None if i == 0 else vifs[i - 1],
        )
        for i in range(k + 1)
    ]

    verif: list[Verificacao] = []
    norm = shapiro_wilk(residuos, alpha=alpha, tcl=False, nome="resíduos")
    verif.append(
        Verificacao(
            nome="Normalidade dos resíduos",
            status=OK if norm.normal else ATENCAO,
            detalhe=norm.passos[0] + ("" if norm.normal else " → p-valores dos coeficientes são aproximados"),
        )
    )
    grandes = [i + 1 for i, r in enumerate(padronizados) if abs(r) > RESIDUO_GRANDE]
    verif.append(
        Verificacao(
            nome="Resíduos grandes (|padronizado| > 2)",
            status=OK if not grandes else ATENCAO,
            detalhe="nenhum" if not grandes else f"linhas (entre as completas): {', '.join(map(str, grandes))}",
        )
    )
    vif_max = max(vifs)
    verif.append(
        Verificacao(
            nome="Multicolinearidade (VIF)",
            status=OK if vif_max <= VIF_ATENCAO else (ATENCAO if vif_max <= VIF_FALHA else FALHA),
            detalhe=f"maior VIF = {num(vif_max, 2)} (até 5: ok; acima de 10: coeficientes instáveis)",
        )
    )

    termos = preditores
    equacao = _equacao(resposta, termos, [c.coef for c in coefs])
    sq_res = float(modelo.ssr)
    sq_reg = sq_total - sq_res
    gl_reg, gl_res = k, n - k - 1
    passos = [
        f"Equação: {equacao}",
        *[
            f"{c.termo}: coef = {num(c.coef, 4)}; EP = {num(c.ep, 4)}; T = {num(c.t, 2)}; p {p_valor(c.p)}"
            + ("" if c.vif is None else f"; VIF = {num(c.vif, 2)}")
            for c in coefs
        ],
        f"ANOVA: regressão gl = {gl_reg}, SQ = {num(sq_reg, 3)}; erro gl = {gl_res}, SQ = {num(sq_res, 3)}; "
        f"F = {num(float(modelo.fvalue), 3)}; p {p_valor(float(modelo.f_pvalue))}",
        f"S = {num(float(np.sqrt(modelo.mse_resid)), 6)}; R² = {num(modelo.rsquared * 100, 2)}%; "
        f"R²(aj) = {num(modelo.rsquared_adj * 100, 2)}%; R²(pred) = {num(r2_pred * 100, 2)}%",
    ]
    avisos = [AVISO_FORA_APOSTILA]
    if descartadas:
        avisos.insert(0, f"{descartadas} linha(s) com dado faltante foram descartadas.")
    return RegressaoMultipla(
        nome="Regressão linear múltipla" if k > 1 else "Regressão linear",
        alpha=alpha,
        estatistica=float(modelo.fvalue),
        rotulo_estatistica="F",
        gl=(float(gl_reg), float(gl_res)),
        p=float(modelo.f_pvalue),
        n=n,
        resposta=resposta,
        preditores=preditores,
        coeficientes=coefs,
        s=float(np.sqrt(modelo.mse_resid)),
        r2=float(modelo.rsquared),
        r2_aj=float(modelo.rsquared_adj),
        r2_pred=float(r2_pred),
        sq_regressao=sq_reg,
        sq_residuo=sq_res,
        sq_total=sq_total,
        gl_regressao=gl_reg,
        gl_residuo=gl_res,
        equacao=equacao,
        faixas={c: (float(x[c].min()), float(x[c].max())) for c in preditores},
        ajustados=np.asarray(modelo.fittedvalues, dtype=float),
        residuos=residuos,
        residuos_padronizados=padronizados,
        modelo=modelo,
        verificacoes=verif,
        passos=passos,
        avisos=avisos,
    )


def prever_multipla(reg: RegressaoMultipla, valores: Mapping[str, float]) -> Previsao:
    """Ajuste, EP do ajuste, IC 95% (média) e IP 95% (observação nova); avisa se sair da faixa observada."""
    faltando = [c for c in reg.preditores if c not in valores]
    if faltando:
        raise ErroDeDados(f"Informe o valor de: {', '.join(faltando)}.")
    linha = np.array([[1.0, *[float(valores[c]) for c in reg.preditores]]])
    quadro = reg.modelo.get_prediction(linha).summary_frame(alpha=0.05)
    fora = [
        f"{c} = {num(float(valores[c]))} (faixa {num(lo)} a {num(hi)})"
        for c, (lo, hi) in reg.faixas.items()
        if not lo <= float(valores[c]) <= hi
    ]
    aviso = ("Extrapolação, leia com cautela: " + "; ".join(fora)) if fora else None
    return Previsao(
        ajuste=float(quadro["mean"].iloc[0]),
        ep_ajuste=float(quadro["mean_se"].iloc[0]),
        ic=(float(quadro["mean_ci_lower"].iloc[0]), float(quadro["mean_ci_upper"].iloc[0])),
        ip=(float(quadro["obs_ci_lower"].iloc[0]), float(quadro["obs_ci_upper"].iloc[0])),
        aviso=aviso,
    )
