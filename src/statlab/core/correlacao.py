"""Correlação linear (Pearson) e por postos (Spearman), com decisão automática de método.

Fluxo (padrão da disciplina):
1. pareia x e y (descarta pares com faltantes);
2. diagnostica outliers; exclui os extremos (com aviso);
3. Shapiro-Wilk em x e y, **sem** o atalho n ≥ 30 → Pearson se ambos normais, senão Spearman;
4. calcula r, p, r crítico (tabela A.6) e, se significativo, a força e r²;
5. repete a análise sem os outliers suaves e informa se a conclusão muda.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados, exigir_minimo, exigir_variacao, pares
from statlab.core.descritiva import detectar_outliers, texto_outliers, verificacao_outliers
from statlab.core.formatacao import num, p_valor
from statlab.core.normalidade import shapiro_wilk, verificacao_normalidade
from statlab.core.resultados import ALPHA_PADRAO, Resultado

N_MINIMO_PARES = 3


def pearson(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """r pela fórmula n·Σxy − Σx·Σy / √[(nΣx² − (Σx)²)(nΣy² − (Σy)²)] e p pelo t com n − 2 gl."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    sx, sy = x.sum(), y.sum()
    sxy = (x * y).sum()
    sx2, sy2 = (x * x).sum(), (y * y).sum()
    den = np.sqrt((n * sx2 - sx**2) * (n * sy2 - sy**2))
    if den == 0:
        raise ErroDeDados("Não é possível calcular a correlação: uma das variáveis não varia.")
    r = float(np.clip((n * sxy - sx * sy) / den, -1.0, 1.0))
    if abs(r) >= 1.0:
        return r, 0.0
    t = r * np.sqrt((n - 2) / (1 - r * r))
    return r, float(2 * stats.t.sf(abs(t), n - 2))


def spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Correlação de postos e p (teste bilateral)."""
    rs, p = stats.spearmanr(x, y)
    return float(rs), float(p)


def r_critico(n: int, alpha: float = ALPHA_PADRAO) -> float:
    """Valor crítico de |r| (bilateral), igual à tabela A.6: r = t / √(t² + n − 2), gl = n − 2.

    Para n = 4 e α = 0,01 dá 0,990 (o livro traz 0,999, erro de impressão).
    """
    if n < 3:
        raise ErroDeDados("O valor crítico de r exige n ≥ 3.")
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    return float(t / np.sqrt(t * t + n - 2))


def forca(r: float) -> str:
    """Classificação de |r| pela tabela 3 da apostila. Só use se a correlação for significativa."""
    a = abs(r)
    if a < 0.2:
        return "bem fraca"
    if a < 0.4:
        return "fraca"
    if a < 0.7:
        return "moderada"
    if a < 0.9:
        return "forte"
    return "muito forte"


@dataclass(kw_only=True)
class Correlacao(Resultado):
    metodo: str = ""  # "Pearson" ou "Spearman" (o usado na decisão)
    r: float = 0.0
    r_s: float = 0.0
    p_pearson: float = 1.0
    p_spearman: float = 1.0
    r2: float = 0.0  # r² de Pearson: % da variação de y explicada por x (interpretar se normal)
    r_critico_5: float = 0.0
    r_critico_1: float = 0.0
    forca: str | None = None  # só preenchido quando significativo
    normal_x: bool = False
    normal_y: bool = False
    n_extremos_excluidos: int = 0
    r_sem_suave: float | None = None
    p_sem_suave: float | None = None
    n_sem_suave: int | None = None
    conclusao_muda: bool | None = None
    x_usado: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    y_usado: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))


def analisar_correlacao(
    x: list[object] | np.ndarray,
    y: list[object] | np.ndarray,
    *,
    alpha: float = ALPHA_PADRAO,
    nome_x: str = "x",
    nome_y: str = "y",
) -> Correlacao:
    xs, ys, descartados = pares(x, y, nome_x, nome_y)
    passos: list[str] = []
    avisos: list[str] = []
    prereq: list[str] = []

    if descartados:
        avisos.append(f"{descartados} par(es) com dado faltante foram descartados.")
    exigir_minimo(xs, N_MINIMO_PARES, "Correlação")
    exigir_variacao(xs, nome_x)
    exigir_variacao(ys, nome_y)

    # 1) outliers: extremos saem da análise, suaves ficam (e são testados com e sem)
    ox, oy = detectar_outliers(xs), detectar_outliers(ys)
    prereq.append(texto_outliers(nome_x, xs, ox))
    prereq.append(texto_outliers(nome_y, ys, oy))
    verif = [verificacao_outliers(nome_x, xs, ox), verificacao_outliers(nome_y, ys, oy)]
    extremo = ox.extremo | oy.extremo
    n_extremos = int(extremo.sum())
    if n_extremos:
        n_antes = len(xs)
        xs, ys = xs[~extremo], ys[~extremo]
        avisos.append(
            f"{n_extremos} par(es) com outlier extremo excluído(s): análise com n = {len(xs)} (antes: {n_antes})."
        )
        exigir_minimo(xs, N_MINIMO_PARES, "Correlação")
        exigir_variacao(xs, nome_x)
        exigir_variacao(ys, nome_y)
    n = len(xs)

    # 2) normalidade (sem o atalho n ≥ 30)
    nx = shapiro_wilk(xs, alpha=alpha, tcl=False, nome=nome_x)
    ny = shapiro_wilk(ys, alpha=alpha, tcl=False, nome=nome_y)
    prereq.append(nx.passos[0])
    prereq.append(ny.passos[0])
    verif.append(verificacao_normalidade(nx, nome_x, "Pearson não indicado; decisão por Spearman"))
    verif.append(verificacao_normalidade(ny, nome_y, "Pearson não indicado; decisão por Spearman"))
    normal = nx.normal and ny.normal

    # 3) cálculo
    r, p_p = pearson(xs, ys)
    rs, p_s = spearman(xs, ys)
    rc5, rc1 = r_critico(n, 0.05), r_critico(n, 0.01)
    p_dec = p_p if normal else p_s
    r_dec = r if normal else rs
    metodo = "Pearson" if normal else "Spearman"
    significativo = p_dec <= alpha

    passos.append(f"Pearson: n = {n}; r = {num(r, 3)}; p {p_valor(p_p)}")
    passos.append(f"Valores críticos (n = {n}): {num(rc5, 3)} (5%) e {num(rc1, 3)} (1%) → |r| = {num(abs(r), 3)}")
    passos.append(f"Spearman: rₛ = {num(rs, 3)}; p {p_valor(p_s)}")
    if normal:
        passos.append("Ambas as variáveis normais → usar Pearson.")
    else:
        passos.append("Falta normalidade em pelo menos uma variável → usar Spearman (Pearson só como conferência).")
    resumo = "significativa" if significativo else "não significativa"
    passos.append(f"Decisão: p = {p_valor(p_dec)} ({metodo}) → {resumo}")
    if significativo:
        passos.append(f"Força ({metodo}): |{'r' if normal else 'rₛ'}| = {num(abs(r_dec), 3)} → {forca(r_dec)}")
        if normal:
            passos.append(f"r² = {num(r * r * 100, 1)}%")

    # 4) sem outliers suaves
    ox2, oy2 = detectar_outliers(xs), detectar_outliers(ys)
    suave = ox2.suave | oy2.suave
    r_sem = p_sem = n_sem = muda = None
    if suave.any():
        m = ~suave
        n_sem = int(m.sum())
        if n_sem >= N_MINIMO_PARES:
            r2_, p2_ = pearson(xs[m], ys[m])
            rs2, ps2 = spearman(xs[m], ys[m])
            r_sem, p_sem = (r2_, p2_) if normal else (rs2, ps2)
            muda = bool((p_sem <= alpha) != significativo)
            passos.append(f"Sem o(s) outlier(s) suave(s) (n = {n_sem}): {metodo} = {num(r_sem, 3)}; p {p_valor(p_sem)}")
            avisos.append(
                "A conclusão muda sem o outlier suave. Se for erro de medição, a análise sem ele vale; "
                "se for dado real, relate as duas análises."
                if muda
                else "A conclusão se mantém com ou sem o outlier suave."
            )
        else:
            avisos.append("Poucos pares restam sem o outlier suave; a análise sem ele não foi feita.")

    return Correlacao(
        nome=f"Correlação de {metodo}",
        alpha=alpha,
        estatistica=r_dec,
        rotulo_estatistica="r" if normal else "rₛ",
        gl=(float(n - 2),),
        p=p_dec,
        n=n,
        metodo=metodo,
        r=r,
        r_s=rs,
        p_pearson=p_p,
        p_spearman=p_s,
        r2=r * r,
        r_critico_5=rc5,
        r_critico_1=rc1,
        forca=forca(r_dec) if significativo else None,
        normal_x=nx.normal,
        normal_y=ny.normal,
        n_extremos_excluidos=n_extremos,
        r_sem_suave=r_sem,
        p_sem_suave=p_sem,
        n_sem_suave=n_sem,
        conclusao_muda=muda,
        x_usado=xs,
        y_usado=ys,
        prerequisitos=prereq,
        verificacoes=verif,
        passos=passos,
        avisos=avisos,
    )
