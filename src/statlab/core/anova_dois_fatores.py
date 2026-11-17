"""ANOVA de dois fatores (com ou sem interação), no formato do Minitab.

Fora da apostila (que cobre a ANOVA de 1 fator). SQ ajustadas (tipo III, codificação de soma zero), como o
"SQ (Aj.)" do Minitab; em delineamentos balanceados coincidem com as SQ sequenciais.
Pré-requisitos (regra de ANOVA da disciplina, aplicada às caselas): resíduos normais ou n ≥ 30, e maior
variância de casela até 9 vezes a menor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

from statlab.core.dados import ErroDeDados
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import shapiro_wilk, verificacao_normalidade
from statlab.core.resultados import ALPHA_PADRAO, ATENCAO, FALHA, OK, Resultado, Verificacao
from statlab.core.variancias import RAZAO_MAXIMA_ANOVA

AVISO_FORA_APOSTILA = "A ANOVA de dois fatores não faz parte da apostila revisada (que cobre a de 1 fator)."


@dataclass(frozen=True)
class LinhaAnova:
    fonte: str
    gl: int
    sq: float
    qm: float | None
    f: float | None
    p: float | None

    def significativa(self, alpha: float) -> bool | None:
        return None if self.p is None else self.p <= alpha


@dataclass(kw_only=True)
class AnovaDoisFatores(Resultado):
    resposta: str = ""
    fator_a: str = ""
    fator_b: str = ""
    interacao: bool = True
    tabela: list[LinhaAnova] = field(default_factory=list)
    s: float = 0.0
    r2: float = 0.0
    r2_aj: float = 0.0
    balanceado: bool = True
    niveis_a: list[str] = field(default_factory=list)
    niveis_b: list[str] = field(default_factory=list)
    media_geral: float = 0.0
    medias_a: dict[str, float] = field(default_factory=dict)
    medias_b: dict[str, float] = field(default_factory=dict)
    medias_celulas: dict[tuple[str, str], float] = field(default_factory=dict)
    residuos: np.ndarray = field(default_factory=lambda: np.array([]))
    ajustados: np.ndarray = field(default_factory=lambda: np.array([]))


def analisar_anova_dois_fatores(
    df: pd.DataFrame,
    resposta: str,
    fator_a: str,
    fator_b: str,
    *,
    interacao: bool = True,
    alpha: float = ALPHA_PADRAO,
) -> AnovaDoisFatores:
    for c in (resposta, fator_a, fator_b):
        if c not in df.columns:
            raise ErroDeDados(f"Coluna {c!r} não existe nesta worksheet.")
    if len({resposta, fator_a, fator_b}) < 3:
        raise ErroDeDados("Resposta, fator A e fator B devem ser três colunas diferentes.")
    if not pd.api.types.is_numeric_dtype(df[resposta]):
        raise ErroDeDados(f"A resposta {resposta!r} precisa ser numérica.")
    bruto = df[[resposta, fator_a, fator_b]].dropna()
    descartadas = len(df) - len(bruto)
    dados = pd.DataFrame(
        {"Y": bruto[resposta].astype(float), "A": bruto[fator_a].astype(str), "B": bruto[fator_b].astype(str)}
    ).reset_index(drop=True)
    niveis_a = [str(v) for v in pd.unique(dados["A"])]
    niveis_b = [str(v) for v in pd.unique(dados["B"])]
    if len(niveis_a) < 2 or len(niveis_b) < 2:
        raise ErroDeDados("Cada fator precisa de pelo menos 2 níveis.")
    contagem = dados.groupby(["A", "B"]).size()
    if interacao:
        if len(contagem) < len(niveis_a) * len(niveis_b):
            raise ErroDeDados("Há combinações de níveis sem observações; desmarque a interação ou complete os dados.")
        if int(contagem.min()) < 2:
            raise ErroDeDados(
                "Com interação, cada combinação de níveis precisa de pelo menos 2 observações (réplicas). "
                "Sem réplicas, desmarque a interação."
            )
    if float(np.ptp(dados["Y"])) == 0.0:
        raise ErroDeDados("A resposta não varia.")

    formula = "Y ~ C(A, Sum) * C(B, Sum)" if interacao else "Y ~ C(A, Sum) + C(B, Sum)"
    modelo = smf.ols(formula, data=dados).fit()
    if modelo.df_resid <= 0:
        raise ErroDeDados("Não sobram graus de liberdade para o erro; são necessárias mais observações.")
    tab = anova_lm(modelo, typ=3).drop(index="Intercept")
    nomes = {"C(A, Sum)": fator_a, "C(B, Sum)": fator_b, "C(A, Sum):C(B, Sum)": f"{fator_a}*{fator_b}"}
    linhas: list[LinhaAnova] = []
    for fonte, row in tab.iterrows():
        gl = int(row["df"])
        sq = float(row["sum_sq"])
        if fonte == "Residual":
            linhas.append(LinhaAnova("Erro", gl, sq, sq / gl, None, None))
        else:
            linhas.append(LinhaAnova(nomes[str(fonte)], gl, sq, sq / gl, float(row["F"]), float(row["PR(>F)"])))
    sq_total = float(np.sum((dados["Y"] - dados["Y"].mean()) ** 2))
    linhas.append(LinhaAnova("Total", len(dados) - 1, sq_total, None, None, None))
    balanceado = contagem.nunique() == 1 and len(contagem) == len(niveis_a) * len(niveis_b)

    residuos = np.asarray(modelo.resid, dtype=float)
    verif: list[Verificacao] = []
    norm = shapiro_wilk(residuos, alpha=alpha, tcl=True, nome="resíduos")
    verif.append(verificacao_normalidade(norm, "resíduos", "resultados aproximados; considere transformar Y"))
    variancias = dados.groupby(["A", "B"])["Y"].var(ddof=1).dropna()
    variancias = variancias[variancias > 0]
    if len(variancias) >= 2:
        razao = float(variancias.max() / variancias.min())
        var_ok = razao <= RAZAO_MAXIMA_ANOVA
        verif.append(
            Verificacao(
                nome="Variâncias semelhantes entre caselas (razão ≤ 9)",
                status=OK if var_ok else FALHA,
                detalhe=f"maior/menor = {num(razao)}" + ("" if var_ok else " → resultados pouco confiáveis"),
            )
        )
    else:
        verif.append(
            Verificacao(
                nome="Variâncias semelhantes entre caselas",
                status=ATENCAO,
                detalhe="sem réplicas suficientes para comparar variâncias por casela",
            )
        )

    efeitos = [lin for lin in linhas if lin.f is not None]
    passos = [
        f"{lin.fonte}: gl = {lin.gl}; SQ = {num(lin.sq, 3)}; QM = {num(lin.qm, 4)}; F = {num(lin.f, 2)}; "
        f"p {p_valor(lin.p)}"
        for lin in efeitos
    ]
    passos.append(f"Erro: gl = {linhas[-2].gl}; SQ = {num(linhas[-2].sq, 3)}; QM = {num(linhas[-2].qm, 4)}")
    passos.append(f"Total: gl = {linhas[-1].gl}; SQ = {num(sq_total, 3)}")
    passos.append(
        f"S = {num(float(np.sqrt(modelo.mse_resid)), 6)}; R² = {num(modelo.rsquared * 100, 2)}%; "
        f"R²(aj) = {num(modelo.rsquared_adj * 100, 2)}%"
    )
    avisos = [AVISO_FORA_APOSTILA]
    if descartadas:
        avisos.insert(0, f"{descartadas} linha(s) com dado faltante foram descartadas.")
    if not balanceado:
        avisos.append("Delineamento desbalanceado: usadas SQ ajustadas (tipo III), como no Minitab.")
    if interacao and efeitos[-1].p is not None and efeitos[-1].p <= alpha:
        avisos.append(
            "A interação é significativa: o efeito de um fator depende do nível do outro. "
            "Interprete os efeitos principais pelo gráfico de interação."
        )

    return AnovaDoisFatores(
        nome="ANOVA de dois fatores" + (" com interação" if interacao else " (sem interação)"),
        alpha=alpha,
        estatistica=float(modelo.fvalue),
        rotulo_estatistica="F (modelo)",
        gl=(float(modelo.df_model), float(modelo.df_resid)),
        p=float(modelo.f_pvalue),
        n=len(dados),
        resposta=resposta,
        fator_a=fator_a,
        fator_b=fator_b,
        interacao=interacao,
        tabela=linhas,
        s=float(np.sqrt(modelo.mse_resid)),
        r2=float(modelo.rsquared),
        r2_aj=float(modelo.rsquared_adj),
        balanceado=bool(balanceado),
        niveis_a=niveis_a,
        niveis_b=niveis_b,
        media_geral=float(dados["Y"].mean()),
        medias_a={k: float(v) for k, v in dados.groupby("A", sort=False)["Y"].mean().items()},
        medias_b={k: float(v) for k, v in dados.groupby("B", sort=False)["Y"].mean().items()},
        medias_celulas={(str(a), str(b)): float(v) for (a, b), v in dados.groupby(["A", "B"])["Y"].mean().items()},
        residuos=residuos,
        ajustados=np.asarray(modelo.fittedvalues, dtype=float),
        verificacoes=verif,
        passos=passos,
        avisos=avisos,
    )
