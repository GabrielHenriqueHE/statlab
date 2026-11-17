"""Testes para uma amostra: média (t ou Wilcoxon), média com σ conhecido (Z) e proporção (z ou binomial exata).

Equivalentes a Estat › Estatísticas Básicas › t/Z para 1 amostra e 1 proporção no Minitab. Não estão na
apostila revisada; seguem as mesmas regras de pré-requisitos (outliers, normalidade ou n ≥ 30).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from statlab.core.dados import ErroDeDados, amostra, exigir_minimo, exigir_variacao
from statlab.core.descritiva import detectar_outliers, sem_extremos, texto_outliers, verificacao_outliers
from statlab.core.formatacao import num, p_valor
from statlab.core.nao_parametricos import validar_alternativa
from statlab.core.normalidade import shapiro_wilk, verificacao_normalidade
from statlab.core.resultados import ALPHA_PADRAO, FALHA, OK, Resultado, Verificacao
from statlab.core.testes_t import p_t_student

_DESCR_ALT = {"bilateral": "≠", "maior": ">", "menor": "<"}


@dataclass(kw_only=True)
class UmaAmostra(Resultado):
    media: float | None = None
    mediana: float | None = None
    valor_referencia: float = 0.0
    alternativa: str = "bilateral"


def _p_normal(z: float, alternativa: str) -> float:
    validar_alternativa(alternativa)
    if alternativa == "bilateral":
        return float(2 * stats.norm.sf(abs(z)))
    if alternativa == "maior":
        return float(stats.norm.sf(z))
    return float(stats.norm.cdf(z))


def t_uma_amostra(
    valores: np.ndarray, mu0: float, *, alpha: float = ALPHA_PADRAO, alternativa: str = "bilateral"
) -> UmaAmostra:
    """t = (x̄ − μ0) / (s/√n), gl = n − 1; IC 95% para a média."""
    v = np.asarray(valores, dtype=float)
    exigir_minimo(v, 2, "Teste t para uma amostra")
    exigir_variacao(v, "amostra")
    n = len(v)
    media, dp = float(v.mean()), float(v.std(ddof=1))
    ep = dp / np.sqrt(n)
    t = (media - mu0) / ep
    gl = n - 1
    p = p_t_student(t, gl, alternativa)
    tc = float(stats.t.ppf(0.975, gl))
    ic = (float(media - tc * ep), float(media + tc * ep))
    return UmaAmostra(
        nome="t para uma amostra",
        alpha=alpha,
        estatistica=float(t),
        rotulo_estatistica="t",
        gl=(float(gl),),
        p=p,
        n=n,
        ic=ic,
        ic_descricao="a média (μ)",
        media=media,
        mediana=float(np.median(v)),
        valor_referencia=float(mu0),
        alternativa=alternativa,
        passos=[
            f"H₀: μ = {num(mu0)}; H₁: μ {_DESCR_ALT[alternativa]} {num(mu0)}",
            f"x̄ = {num(media)}; s = {num(dp)}; EP = s/√n = {num(ep, 4)}",
            f"t = (x̄ − μ0)/EP = {num(t, 3)}; gl = {gl}; p {p_valor(p)}",
            f"IC 95% para μ: ({num(ic[0])}; {num(ic[1])})",
        ],
    )


def wilcoxon_uma_amostra(
    valores: np.ndarray, m0: float, *, alpha: float = ALPHA_PADRAO, alternativa: str = "bilateral"
) -> UmaAmostra:
    """Wilcoxon dos postos sinalizados para a mediana (d = x − m0; zeros descartados)."""
    v = np.asarray(valores, dtype=float)
    d = v - m0
    if not np.any(d != 0):
        raise ErroDeDados("Todos os valores são iguais à mediana de referência; o teste de Wilcoxon não se aplica.")
    w = stats.wilcoxon(d, alternative=validar_alternativa(alternativa))
    mediana = float(np.median(v))
    return UmaAmostra(
        nome="Wilcoxon para uma amostra (mediana)",
        alpha=alpha,
        estatistica=float(w.statistic),
        rotulo_estatistica="W",
        p=float(w.pvalue),
        n=len(v),
        media=float(v.mean()),
        mediana=mediana,
        valor_referencia=float(m0),
        alternativa=alternativa,
        passos=[
            f"H₀: mediana = {num(m0)}; H₁: mediana {_DESCR_ALT[alternativa]} {num(m0)}",
            f"Mediana da amostra = {num(mediana)}; W = {num(float(w.statistic), 1)}; p {p_valor(float(w.pvalue))}",
        ],
    )


def z_uma_amostra(
    valores: np.ndarray,
    mu0: float,
    sigma: float,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
) -> UmaAmostra:
    """Z = (x̄ − μ0) / (σ/√n), com σ populacional conhecido; IC 95% = x̄ ± 1,96 σ/√n."""
    if not sigma > 0:
        raise ErroDeDados("O desvio padrão populacional (σ) deve ser maior que zero.")
    v = np.asarray(valores, dtype=float)
    exigir_minimo(v, 1, "Teste Z")
    n = len(v)
    media = float(v.mean())
    ep = sigma / np.sqrt(n)
    z = (media - mu0) / ep
    p = _p_normal(z, alternativa)
    zc = float(stats.norm.ppf(0.975))
    ic = (float(media - zc * ep), float(media + zc * ep))
    return UmaAmostra(
        nome="Z para uma amostra (σ conhecido)",
        alpha=alpha,
        estatistica=float(z),
        rotulo_estatistica="z",
        p=p,
        n=n,
        ic=ic,
        ic_descricao="a média (μ)",
        media=media,
        mediana=float(np.median(v)),
        valor_referencia=float(mu0),
        alternativa=alternativa,
        passos=[
            f"H₀: μ = {num(mu0)}; H₁: μ {_DESCR_ALT[alternativa]} {num(mu0)}",
            f"x̄ = {num(media)}; σ = {num(sigma)}; EP = σ/√n = {num(ep, 4)}",
            f"z = (x̄ − μ0)/EP = {num(z, 3)}; p {p_valor(p)}",
            f"IC 95% para μ: ({num(ic[0])}; {num(ic[1])})",
        ],
    )


def _preparar(valores: object, nome: str) -> tuple[np.ndarray, list[str], list[str], list[Verificacao], np.ndarray]:
    """Faltantes, mínimo, outliers (extremos saem). Devolve (v, avisos, prereq, verificações, máscara de suaves)."""
    v, faltantes = amostra(valores, nome)  # type: ignore[arg-type]
    avisos: list[str] = []
    if faltantes:
        avisos.append(f"{faltantes} valor(es) faltante(s) descartado(s).")
    exigir_minimo(v, 3, nome)
    exigir_variacao(v, nome)
    out = detectar_outliers(v)
    prereq = [texto_outliers(nome, v, out)]
    verif = [verificacao_outliers(nome, v, out)]
    if out.tem_extremo:
        n_antes = len(v)
        v = sem_extremos(v, out)
        avisos.append(f"Outlier extremo excluído: n = {len(v)} (antes: {n_antes}).")
        exigir_minimo(v, 3, nome)
    return v, avisos, prereq, verif, detectar_outliers(v).suave


def analisar_uma_amostra(
    valores: object,
    mu0: float,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome: str = "amostra",
) -> UmaAmostra:
    """Compara a média com μ0: t (normal ou n ≥ 30) ou, se não, Wilcoxon para a mediana."""
    v, avisos, prereq, verif, suave = _preparar(valores, nome)
    norm = shapiro_wilk(v, alpha=alpha, tcl=True, nome=nome)
    prereq.append(norm.passos[0])
    verif.append(verificacao_normalidade(norm, nome, "Wilcoxon para a mediana"))

    def _rodar(x: np.ndarray) -> UmaAmostra:
        if norm.atende:
            return t_uma_amostra(x, mu0, alpha=alpha, alternativa=alternativa)
        return wilcoxon_uma_amostra(x, mu0, alpha=alpha, alternativa=alternativa)

    res = _rodar(v)
    sub = None
    if suave.any() and int((~suave).sum()) >= 3:
        try:
            sub = _rodar(v[~suave])
        except ErroDeDados:
            avisos.append("Sem o(s) outlier(s) suave(s), a amostra fica sem variação; a análise sem ele não foi feita.")
    if sub is not None:
        mudou = sub.significativo != res.significativo
        avisos.append(
            f"Sem o(s) outlier(s) suave(s) (n = {int((~suave).sum())}): p {p_valor(sub.p)} → "
            + ("a conclusão MUDA; relate as duas análises." if mudou else "a conclusão se mantém.")
        )
    res.prerequisitos = prereq
    res.verificacoes = verif
    res.avisos = avisos + res.avisos
    return res


def analisar_z(
    valores: object,
    mu0: float,
    sigma: float,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome: str = "amostra",
) -> UmaAmostra:
    """Teste Z com σ conhecido. A normalidade (ou n ≥ 30) continua sendo pré-requisito e é informada."""
    v, avisos, prereq, verif, _ = _preparar(valores, nome)
    norm = shapiro_wilk(v, alpha=alpha, tcl=True, nome=nome)
    prereq.append(norm.passos[0])
    verif.append(verificacao_normalidade(norm, nome, "o Z pressupõe normalidade; interprete com cautela"))
    res = z_uma_amostra(v, mu0, sigma, alpha=alpha, alternativa=alternativa)
    if not norm.atende:
        avisos.append("Amostra não normal com n < 30: o teste Z não é confiável (considere o Wilcoxon).")
    res.prerequisitos = prereq
    res.verificacoes = verif
    res.avisos = avisos
    return res


# ----------------------------------------------------------------------------- uma proporção


@dataclass(kw_only=True)
class UmaProporcao(Resultado):
    p_amostral: float = 0.0
    p0: float = 0.0
    alternativa: str = "bilateral"


def analisar_uma_proporcao(
    x: int,
    n: int,
    p0: float,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
) -> UmaProporcao:
    """Proporção contra p0: z (aproximação normal) se n·p̂·q̂ ≥ 5 e n·p0 ≥ 5 e n·(1 − p0) ≥ 5; senão binomial exata.

    IC 95%: normal (p̂ ± 1,96 √(p̂q̂/n)) no z; Clopper-Pearson (exato) na binomial.
    """
    x, n = int(x), int(n)
    if n < 1:
        raise ErroDeDados("O total (n) deve ser pelo menos 1.")
    if not 0 <= x <= n:
        raise ErroDeDados(f"Ocorrências ({x}) devem estar entre 0 e o total ({n}).")
    if not 0 < p0 < 1:
        raise ErroDeDados("A proporção de referência p0 deve estar entre 0 e 1 (exclusive).")
    scipy_alt = validar_alternativa(alternativa)
    ph = x / n
    pq = n * ph * (1 - ph)
    pq_ok = pq >= 5
    p0_ok = n * p0 >= 5 and n * (1 - p0) >= 5
    verif = [
        Verificacao(nome="n·p̂·q̂ ≥ 5 (apostila)", status=OK if pq_ok else FALHA, detalhe=f"n·p̂·q̂ = {num(pq)}"),
        Verificacao(
            nome="n·p0 ≥ 5 e n·(1 − p0) ≥ 5",
            status=OK if p0_ok else FALHA,
            detalhe=f"n·p0 = {num(n * p0)}; n·(1 − p0) = {num(n * (1 - p0))}"
            + ("" if (pq_ok and p0_ok) else " → teste binomial exato"),
        ),
    ]
    passos = [
        f"H₀: p = {num(p0, 4)}; H₁: p {_DESCR_ALT[alternativa]} {num(p0, 4)}",
        f"p̂ = {x}/{n} = {num(ph, 4)}",
    ]
    if pq_ok and p0_ok:
        ep0 = np.sqrt(p0 * (1 - p0) / n)
        z = (ph - p0) / ep0
        p = _p_normal(z, alternativa)
        margem = 1.959964 * np.sqrt(ph * (1 - ph) / n)
        ic = (float(max(0.0, ph - margem)), float(min(1.0, ph + margem)))
        passos += [
            f"EP = √(p0·q0/n) = {num(ep0, 4)}; z = (p̂ − p0)/EP = {num(z, 3)}; p {p_valor(p)}",
            f"IC 95% (normal): ({num(ic[0], 4)}; {num(ic[1], 4)})",
        ]
        nome, estat, rot = "Uma proporção (aproximação normal)", float(z), "z"
    else:
        bt = stats.binomtest(x, n, p0, alternative=scipy_alt)
        p = float(bt.pvalue)
        # IC sempre bilateral de 95% (como nos demais testes), mesmo com H₁ unilateral
        ci = stats.binomtest(x, n, p0).proportion_ci(confidence_level=0.95, method="exact")
        ic = (float(ci.low), float(ci.high))
        passos += [
            f"Binomial exata: p {p_valor(p)}",
            f"IC 95% (Clopper-Pearson): ({num(ic[0], 4)}; {num(ic[1], 4)})",
        ]
        nome, estat, rot = "Uma proporção (binomial exata)", None, ""
    return UmaProporcao(
        nome=nome,
        alpha=alpha,
        estatistica=estat,
        rotulo_estatistica=rot,
        p=p,
        n=n,
        ic=ic,
        ic_descricao="a proporção (p)",
        p_amostral=ph,
        p0=float(p0),
        alternativa=alternativa,
        verificacoes=verif,
        passos=passos,
    )


# ----------------------------------------------------------------------------- mediana: teste de sinal


def teste_sinal(
    valores: np.ndarray, m0: float, *, alpha: float = ALPHA_PADRAO, alternativa: str = "bilateral"
) -> UmaAmostra:
    """Teste de sinal para a mediana: conta valores acima e abaixo de m0 (iguais a m0 são descartados).

    Sob H₀, o número de valores acima segue Binomial(n_efetivo; 0,5). p pela binomial exata, como no
    Minitab (Estat › Não paramétricos › Sinal para 1 amostra). Para dados pareados, use a coluna das diferenças.
    """
    v = np.asarray(valores, dtype=float)
    acima = int((v > m0).sum())
    abaixo = int((v < m0).sum())
    iguais = len(v) - acima - abaixo
    n_ef = acima + abaixo
    if n_ef == 0:
        raise ErroDeDados("Todos os valores são iguais à mediana de referência; o teste de sinal não se aplica.")
    p = float(stats.binomtest(acima, n_ef, 0.5, alternative=validar_alternativa(alternativa)).pvalue)
    mediana = float(np.median(v))
    passos = [
        f"H₀: mediana = {num(m0)}; H₁: mediana {_DESCR_ALT[alternativa]} {num(m0)}",
        f"Abaixo de {num(m0)}: {abaixo}; iguais: {iguais} (descartados); acima: {acima}",
        f"Sob H₀, acima ~ Binomial(n = {n_ef}; 0,5) → p {p_valor(p)} (binomial exata)",
        f"Mediana da amostra = {num(mediana)}",
    ]
    return UmaAmostra(
        nome="Teste de sinal (mediana)",
        alpha=alpha,
        p=p,
        n=n_ef,
        media=float(v.mean()),
        mediana=mediana,
        valor_referencia=float(m0),
        alternativa=alternativa,
        passos=passos,
    )


def analisar_sinal(
    valores: object,
    m0: float,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome: str = "amostra",
) -> UmaAmostra:
    """Teste de sinal com a regra de outliers da disciplina (extremos saem; suaves: com e sem).

    Não exige normalidade. É menos poderoso que o Wilcoxon (usa só o sinal, não a distância até m0).
    """
    v, avisos, prereq, verif, suave = _preparar(valores, nome)
    res = teste_sinal(v, m0, alpha=alpha, alternativa=alternativa)
    if suave.any() and int((~suave).sum()) >= 3:
        try:
            sub = teste_sinal(v[~suave], m0, alpha=alpha, alternativa=alternativa)
        except ErroDeDados:
            avisos.append("Sem o(s) outlier(s) suave(s), não sobram valores diferentes de m0; análise sem ele omitida.")
        else:
            mudou = sub.significativo != res.significativo
            avisos.append(
                f"Sem o(s) outlier(s) suave(s) (n = {int((~suave).sum())}): p {p_valor(sub.p)} → "
                + ("a conclusão MUDA; relate as duas análises." if mudou else "a conclusão se mantém.")
            )
    if res.n is not None and res.n < len(v):
        avisos.append(
            f"{len(v) - res.n} valor(es) igual(is) à mediana de referência descartado(s) (n efetivo = {res.n})."
        )
    avisos.append("Teste de sinal: fora da apostila revisada (equivale ao Sinal para 1 amostra do Minitab).")
    res.prerequisitos = prereq
    res.verificacoes = verif
    res.avisos = avisos
    return res


# ----------------------------------------------------------------------------- uma variância (qui-quadrado)


@dataclass(kw_only=True)
class UmaVariancia(Resultado):
    """Teste χ² para uma variância. ``ic`` é o IC 95% para σ; ``ic_variancia`` para σ²."""

    desvio: float = 0.0
    sigma0: float = 0.0
    alternativa: str = "bilateral"
    ic_variancia: tuple[float, float] | None = None
    confiavel: bool = True  # False se a amostra não é normal (o χ² não é robusto)


def qui_quadrado_variancia(
    valores: np.ndarray, sigma0: float, *, alpha: float = ALPHA_PADRAO, alternativa: str = "bilateral"
) -> UmaVariancia:
    """χ² = (n − 1)·s²/σ0², gl = n − 1. IC 95% para σ²: ((n − 1)s²/χ²₀,₉₇₅; (n − 1)s²/χ²₀,₀₂₅)."""
    if not sigma0 > 0:
        raise ErroDeDados("O desvio padrão de referência (σ₀) deve ser maior que zero.")
    validar_alternativa(alternativa)
    v = np.asarray(valores, dtype=float)
    exigir_minimo(v, 2, "Teste de uma variância")
    exigir_variacao(v, "amostra")
    n = len(v)
    gl = n - 1
    s2 = float(v.var(ddof=1))
    chi2 = gl * s2 / sigma0**2
    if alternativa == "maior":
        p = float(stats.chi2.sf(chi2, gl))
    elif alternativa == "menor":
        p = float(stats.chi2.cdf(chi2, gl))
    else:
        p = float(min(1.0, 2 * min(stats.chi2.cdf(chi2, gl), stats.chi2.sf(chi2, gl))))
    ic_var = (gl * s2 / float(stats.chi2.ppf(0.975, gl)), gl * s2 / float(stats.chi2.ppf(0.025, gl)))
    ic_dp = (float(np.sqrt(ic_var[0])), float(np.sqrt(ic_var[1])))
    return UmaVariancia(
        nome="Qui-quadrado para uma variância",
        alpha=alpha,
        estatistica=float(chi2),
        rotulo_estatistica="χ²",
        gl=(float(gl),),
        p=p,
        n=n,
        ic=ic_dp,
        ic_descricao="o desvio padrão (σ)",
        desvio=float(np.sqrt(s2)),
        sigma0=float(sigma0),
        alternativa=alternativa,
        ic_variancia=(float(ic_var[0]), float(ic_var[1])),
        passos=[
            f"H₀: σ = {num(sigma0)}; H₁: σ {_DESCR_ALT[alternativa]} {num(sigma0)}",
            f"s = {num(np.sqrt(s2), 4)}; s² = {num(s2, 4)}; σ₀² = {num(sigma0**2, 4)}",
            f"χ² = (n − 1)·s²/σ₀² = {gl}·{num(s2, 4)}/{num(sigma0**2, 4)} = {num(chi2, 3)}; gl = {gl}; p {p_valor(p)}",
            f"IC 95% para σ²: ({num(ic_var[0], 4)}; {num(ic_var[1], 4)}); para σ: ({num(ic_dp[0], 4)}; "
            f"{num(ic_dp[1], 4)})",
        ],
    )


def analisar_uma_variancia(
    valores: object,
    sigma0: float,
    *,
    alpha: float = ALPHA_PADRAO,
    alternativa: str = "bilateral",
    nome: str = "amostra",
) -> UmaVariancia:
    """Teste χ² para uma variância, com outliers pela regra da disciplina e normalidade SEM o atalho do TCL.

    O χ² para variância não é robusto à falta de normalidade, nem com n grande; por isso o TCL não vale aqui.
    """
    v, avisos, prereq, verif, suave = _preparar(valores, nome)
    norm = shapiro_wilk(v, alpha=alpha, tcl=False, nome=nome)
    prereq.append(norm.passos[0])
    verif.append(
        verificacao_normalidade(
            norm, nome, "o χ² para variância não é confiável (o TCL não vale para variâncias, mesmo com n ≥ 30)"
        )
    )
    res = qui_quadrado_variancia(v, sigma0, alpha=alpha, alternativa=alternativa)
    res.confiavel = norm.normal
    if not norm.normal:
        avisos.append(
            "Amostra não normal: o teste χ² para uma variância pode dar p muito errado. O Minitab oferece, nesse "
            "caso, o método de Bonett (não implementado no statlab); interprete este resultado com cautela."
        )
    if suave.any() and int((~suave).sum()) >= 3:
        try:
            sub = qui_quadrado_variancia(v[~suave], sigma0, alpha=alpha, alternativa=alternativa)
        except ErroDeDados:
            avisos.append("Sem o(s) outlier(s) suave(s), a amostra fica sem variação; a análise sem ele não foi feita.")
        else:
            mudou = sub.significativo != res.significativo
            avisos.append(
                f"Sem o(s) outlier(s) suave(s) (n = {int((~suave).sum())}): p {p_valor(sub.p)} → "
                + ("a conclusão MUDA; relate as duas análises." if mudou else "a conclusão se mantém.")
            )
    avisos.append("Teste de uma variância: fora da apostila revisada (equivale ao Teste de 1 variância do Minitab).")
    res.prerequisitos = prereq
    res.verificacoes = verif
    res.avisos = avisos
    return res
