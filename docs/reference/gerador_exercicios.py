#!/usr/bin/env python3
"""
Gerador de exercícios de Análise Estatística (Probabilidade e Estatística).

Gera listas com dados aleatórios e o gabarito resolvido, seguindo os critérios
da apostila da disciplina:
  - correlação de Pearson / Spearman + regressão linear simples
  - teste t pareado / Wilcoxon
  - teste t independente (variâncias iguais ou Welch) / Mann-Whitney
  - ANOVA 1 fator + Tukey / Kruskal-Wallis
  - teste de duas proporções / exato de Fisher

O enunciado NÃO diz qual teste usar: decidir faz parte do exercício.

Uso:
  python gerador_exercicios.py                      # 6 exercícios sortidos
  python gerador_exercicios.py -n 10 --seed 42      # reproduzível
  python gerador_exercicios.py -t corr,anova        # só alguns tipos
  python gerador_exercicios.py --xlsx               # também gera planilha com os dados
  python gerador_exercicios.py --interativo         # pratica no terminal (mostra gabarito ao apertar Enter)

Tipos: corr, t_par, t_ind, anova, prop

Dependências: numpy, scipy (>= 1.11). Opcional: openpyxl (para --xlsx).
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import stats

ALPHA = 0.05
RAZAO_MAX_VAR = 9  # critério da disciplina para a ANOVA


# ----------------------------------------------------------------------------
# utilidades de formatação (padrão brasileiro)
# ----------------------------------------------------------------------------
def br(x: float, d: int = 2) -> str:
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fp(p: float) -> str:
    return "< 0,001" if p < 0.001 else f"= {br(p, 3)}"


def fpv(p: float) -> str:
    return "< 0,001" if p < 0.001 else br(p, 3)


def lista(v) -> str:
    return "; ".join(br(x, 0) if float(x).is_integer() else br(x, 1) for x in v)


def nivel(p: float) -> str:
    if p <= 0.01:
        return "significativo com 99% de confiança"
    if p <= 0.05:
        return "significativo com 95% de confiança"
    return "não significativo"


def forca(r: float) -> str:
    a = abs(r)
    for lim, nome in [(0.2, "bem fraca"), (0.4, "fraca"), (0.7, "moderada"), (0.9, "forte")]:
        if a < lim:
            return nome
    return "muito forte"


def r_critico(n: int, alpha: float) -> float:
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    return t / np.sqrt(t * t + n - 2)


def outliers(v) -> tuple[list, list, float, float, float]:
    """Regra do diagrama de caixa (quartis pelo método do Excel QUARTIL / QUARTIL.INC)."""
    v = np.asarray(v, float)
    q1, q3 = np.percentile(v, [25, 75])
    d = q3 - q1
    ext = [x for x in v if x < q1 - 3 * d or x > q3 + 3 * d]
    suave = [x for x in v if (x < q1 - 1.5 * d or x > q3 + 1.5 * d) and x not in ext]
    return suave, ext, q1, q3, d


def sem_extremos(nome: str, v, g: list[str]) -> np.ndarray:
    """Aplica a regra do diagrama de caixa: escreve no gabarito e devolve os dados sem outliers extremos."""
    v = np.asarray(v, float)
    g.append(bloco_outliers(nome, v))
    _, ext, *_ = outliers(v)
    if ext:
        m = np.ones(len(v), bool)
        for e in ext:
            m &= v != e
        g.append(f"  → análise de {nome} feita **sem** os extremos (n = {m.sum()}).")
        return v[m]
    return v


def shapiro(v) -> float:
    return float(stats.shapiro(v).pvalue)


def normal_ok(v) -> tuple[bool, str]:
    n = len(v)
    p = shapiro(v)
    if p > ALPHA:
        return True, f"Shapiro-Wilk p {fp(p)} → pode-se assumir normalidade"
    if n >= 30:
        return True, f"Shapiro-Wilk p {fp(p)} → não normal, mas n = {n} ≥ 30 (TCL) → requisito atendido"
    return False, f"Shapiro-Wilk p {fp(p)} → NÃO normal e n = {n} < 30"


def desc_linha(nome, v) -> str:
    v = np.asarray(v, float)
    return (f"| {nome} | {len(v)} | {br(v.mean())} | {br(np.median(v))} | "
            f"{br(v.std(ddof=1))} | {br(v.var(ddof=1))} |")


DESC_CAB = "| Grupo | n | Média | Mediana | Desvio padrão | Variância |\n|---|---|---|---|---|---|"


def bloco_outliers(nome, v) -> str:
    s, e, q1, q3, d = outliers(v)
    txt = f"- {nome}: Q1 = {br(q1)}; Q3 = {br(q3)}; D = {br(d)}; "
    if e:
        txt += f"**outlier extremo**: {lista(e)} (deve ser excluído). "
    if s:
        txt += f"**outlier suave**: {lista(s)} (analisar com e sem). "
    if not e and not s:
        txt += "sem outliers."
    return txt


@dataclass
class Exercicio:
    titulo: str
    enunciado: str
    dados: dict[str, list]
    gabarito: str
    tipo: str = ""
    extra: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------
# 1) Correlação + regressão
# ----------------------------------------------------------------------------
TEMAS_CORR = [
    # (x, y, faixa de x, sinal, inclinação, base, casas decimais de y)
    ("Horas de estudo semanais", "Nota na prova", (2, 20), +1, 3.0, 25, 0),
    ("Investimento em marketing (R$ mil)", "Vendas (R$ mil)", (5, 50), +1, 2.5, 30, 1),
    ("Temperatura média (°C)", "Consumo de sorvete (kg)", (15, 35), +1, 4.0, -20, 0),
    ("Horas de treinamento", "Erros por semana", (1, 15), -1, 0.8, 18, 0),
    ("Idade do equipamento (anos)", "Paradas por mês", (1, 12), +1, 0.7, 1, 0),
    ("Tempo de tela diário (h)", "Horas de sono", (1, 10), -1, 0.35, 9, 1),
    ("Nº de commits na semana", "Bugs reportados", (5, 60), +1, 0.15, 2, 0),
]


def gerar_corr(rng: np.random.Generator) -> Exercicio:
    xn, yn, (lo, hi), sinal, inc, base, dec_y = random.choice(TEMAS_CORR)
    cenario = random.choice(["forte", "forte", "moderada", "nula", "outlier", "nao_normal"])
    n = random.choice([random.randint(6, 12), random.randint(15, 30)])

    if cenario == "nao_normal":
        x = lo + rng.exponential((hi - lo) / 5, n)
        x = np.clip(x, lo, hi * 2)
    else:
        x = rng.uniform(lo, hi, n)
    x = np.round(x, 0)

    ruido = {"forte": 0.08, "moderada": 0.25, "nula": 1.0, "outlier": 0.1, "nao_normal": 0.15}[cenario]
    amplitude = inc * (hi - lo)
    if cenario == "nula":
        y = base + inc * (lo + hi) / 2 + rng.normal(0, amplitude * 0.3, n)
    else:
        y = base + sinal * inc * x + rng.normal(0, amplitude * ruido, n)
    if cenario == "outlier":
        # ponto fora da tendência, sempre para cima (evita valores negativos)
        i = int(np.argmin(x)) if sinal > 0 else int(np.argmax(x))
        y[i] = y[i] + amplitude * 1.5
    y = np.round(np.clip(y, 0, None), dec_y)

    enun = (f"Uma empresa registrou, para {n} casos, as variáveis **{xn}** (x) e **{yn}** (y).\n\n"
            f"x: {lista(x)}\n\ny: {lista(y)}\n\n"
            f"a) Existe correlação entre as variáveis ao nível de 5%? E de 1%?\n"
            f"b) Se existir, classifique a força, calcule r² e interprete.\n"
            f"c) Se fizer sentido, obtenha a reta de regressão, interprete os coeficientes e "
            f"estime y para x = {br(np.round((x.min() + x.max()) / 2), 0)}.")

    g = []
    # pré-requisitos
    g.append("**1. Pré-requisitos**")
    g.append(bloco_outliers("x", x))
    g.append(bloco_outliers("y", y))
    ext = set(outliers(x)[1]) | set(outliers(y)[1])
    if ext:
        m = np.array([not (xi in outliers(x)[1] or yi in outliers(y)[1]) for xi, yi in zip(x, y)])
        x, y, n = x[m], y[m], int(m.sum())
        g.append(f"  → pares com outlier extremo excluídos; análise com n = {n} pares.")
    okx, tx = normal_ok(x)
    oky, ty = normal_ok(y)
    # para correlação a apostila não aplica o "n >= 30" — usa a normalidade em si
    px, py = shapiro(x), shapiro(y)
    normal = px > ALPHA and py > ALPHA
    g.append(f"- Normalidade: x p {fp(px)}; y p {fp(py)} → "
             + ("ambas normais: usar **Pearson**." if normal else "falta normalidade: usar **Spearman** (e Pearson só como conferência)."))

    # cálculo
    sx, sy, sxy, sx2, sy2 = x.sum(), y.sum(), (x * y).sum(), (x * x).sum(), (y * y).sum()
    num = n * sxy - sx * sy
    dx, dy = n * sx2 - sx ** 2, n * sy2 - sy ** 2
    r = num / np.sqrt(dx * dy)
    p = stats.pearsonr(x, y).pvalue
    rs = stats.spearmanr(x, y)
    rc5, rc1 = r_critico(n, 0.05), r_critico(n, 0.01)

    g.append("\n**2. Cálculo de r (Pearson)**")
    g.append(f"- n = {n}; Σx = {br(sx, 1)}; Σy = {br(sy, 1)}; Σxy = {br(sxy, 1)}; Σx² = {br(sx2, 1)}; Σy² = {br(sy2, 1)}")
    g.append(f"- Numerador = n·Σxy − Σx·Σy = {br(num, 1)}")
    g.append(f"- Denominador = √(n·Σx² − (Σx)²) · √(n·Σy² − (Σy)²) = √{br(dx, 1)} · √{br(dy, 1)} = {br(np.sqrt(dx * dy), 2)}")
    g.append(f"- **r = {br(r, 3)}**; p {fp(p)}")
    g.append(f"- Valores críticos (n = {n}): {br(rc5, 3)} (5%) e {br(rc1, 3)} (1%) → |r| = {br(abs(r), 3)} → {nivel(p)}")
    g.append(f"- Spearman: r_s = {br(rs.statistic, 3)}; p {fp(rs.pvalue)} → {nivel(rs.pvalue)}")

    p_dec = p if normal else rs.pvalue
    r_dec = r if normal else rs.statistic
    teste = "Pearson" if normal else "Spearman"
    g.append("\n**3. Conclusão**")
    if p_dec <= ALPHA:
        sentido = "positiva" if r_dec > 0 else "negativa"
        conf = "99%" if p_dec <= 0.01 else "95%"
        g.append(f"Existe correlação {sentido} e {forca(r_dec)} entre {xn.lower()} e {yn.lower()}, significativa "
                 f"com {conf} de confiança ({teste}: r = {br(r_dec, 3)}; p {fp(p_dec)}). "
                 + (f"r² = {br(r * r * 100, 1)}%: essa parcela da variação de y é explicada por x; "
                    f"o restante ({br((1 - r * r) * 100, 1)}%) se deve a outros fatores." if normal else
                    "Como os dados não são normais, o r² e a regressão linear devem ser vistos com cautela."))
        a = num / dx
        b = sy / n - a * sx / n
        x0 = np.round((x.min() + x.max()) / 2)
        g.append(f"\n**4. Regressão**: a = {br(num, 1)} / {br(dx, 1)} = **{br(a, 4)}**; "
                 f"b = ȳ − a·x̄ = {br(sy / n, 3)} − {br(a, 4)}·{br(sx / n, 3)} = **{br(b, 3)}**")
        g.append(f"- ŷ = {br(a, 4)}x {'+' if b >= 0 else '−'} {br(abs(b), 3)}")
        g.append(f"- A cada unidade a mais de x, y {'aumenta' if a > 0 else 'diminui'} em média {br(abs(a), 3)}.")
        g.append(f"- Para x = {br(x0, 0)}: ŷ = {br(a * x0 + b, 2)} (dentro da faixa observada de x: "
                 f"{br(x.min(), 0)} a {br(x.max(), 0)}).")
    else:
        g.append(f"Não existe correlação {'linear ' if normal else ''}significativa entre {xn.lower()} e {yn.lower()} "
                 f"({teste}: r = {br(r_dec, 3)}; p {fp(p_dec)}). A regressão **não** deve ser feita. "
                 "Olhe o diagrama de dispersão: pode haver relação não linear.")
    sx_, sy_ = outliers(x)[0], outliers(y)[0]
    if sx_ or sy_:
        m = np.array([not (xi in sx_ or yi in sy_) for xi, yi in zip(x, y)])
        if m.sum() >= 4:
            r2 = stats.pearsonr(x[m], y[m])
            g.append(f"\n**Análise sem o(s) outlier(s) suave(s)** (n = {m.sum()}): r = {br(r2.statistic, 3)}; "
                     f"p {fp(r2.pvalue)} → {nivel(r2.pvalue)}.")
            if (r2.pvalue <= ALPHA) != (p_dec <= ALPHA):
                g.append("A conclusão **muda** com a retirada do outlier. Se ele for erro de medição/digitação, "
                         "vale a análise sem ele; se for um dado real, relate as duas análises e investigue o caso.")
            else:
                g.append("A conclusão se mantém com ou sem o outlier.")

    return Exercicio("Correlação e regressão", enun, {xn: x.tolist(), yn: y.tolist()}, "\n".join(g), "corr",
                     {"cenario": cenario})


# ----------------------------------------------------------------------------
# 2) t pareado / Wilcoxon
# ----------------------------------------------------------------------------
TEMAS_PAR = [
    ("Tempo de resposta da API (ms)", "antes", "depois da otimização", 800, 120, -1),
    ("Pressão arterial sistólica (mmHg)", "antes", "depois do programa de exercícios", 135, 12, -1),
    ("Nota no simulado (0 a 100)", "antes", "depois do curso preparatório", 60, 10, +1),
    ("Peças produzidas por hora", "antes", "depois do novo layout", 48, 6, +1),
]


def gerar_t_par(rng) -> Exercicio:
    var, a_n, d_n, media, dp, sentido = random.choice(TEMAS_PAR)
    cenario = random.choice(["efeito", "efeito", "sem_efeito", "nao_normal"])
    n = random.randint(8, 20)
    antes = rng.normal(media, dp, n)
    efeito = {"efeito": dp * rng.uniform(0.4, 1.2), "sem_efeito": dp * rng.uniform(-0.1, 0.1),
              "nao_normal": dp * 0.6}[cenario]
    if cenario == "nao_normal":
        ruido = rng.exponential(dp * 0.6, n) - dp * 0.6
        ruido[int(rng.integers(n))] += dp * 3
    else:
        ruido = rng.normal(0, dp * 0.5, n)
    depois = antes + sentido * efeito + ruido
    teto = 100 if "0 a 100" in var else None
    antes, depois = (np.round(np.clip(v, 0, teto), 0) for v in (antes, depois))
    d = antes - depois

    h1 = "diminuiu" if sentido < 0 else "aumentou"
    enun = (f"Mediu-se **{var}** em {n} indivíduos/itens, {a_n} e {d_n} (mesmos indivíduos, na mesma ordem).\n\n"
            f"Antes: {lista(antes)}\n\nDepois: {lista(depois)}\n\n"
            f"a) Ao nível de 5%, há evidência de que o valor {h1}? (hipótese unilateral definida antes da coleta)\n"
            f"b) Construa o intervalo de 95% de confiança para a diferença média (se o teste for paramétrico).")

    g = ["**1. Tipo de dado**: mesmos indivíduos medidos duas vezes → dados **pareados**. "
         "Analisa-se a diferença d = antes − depois.",
         "\n**2. Pré-requisitos (nas diferenças)**"]
    d_ok = sem_extremos("d", d, g)
    if len(d_ok) < len(d):
        m = np.isin(d, d_ok)
        antes, depois, d, n = antes[m], depois[m], d[m], int(m.sum())
    ok, t = normal_ok(d)
    g.append(f"- {t}")
    g.append("- Igualdade de variâncias **não** é exigida no teste pareado.")

    alt = "greater" if sentido < 0 else "less"
    if ok:
        res = stats.ttest_rel(antes, depois)
        res_u = stats.ttest_rel(antes, depois, alternative=alt)
        ci = res.confidence_interval(0.95)
        dbar, sd = d.mean(), d.std(ddof=1)
        g.append("\n**3. Teste t pareado**")
        g.append(f"- d̄ = {br(dbar)}; s_d = {br(sd)}; EP = s_d/√n = {br(sd / np.sqrt(n))}")
        g.append(f"- t = d̄ / EP = **{br(res.statistic)}**; gl = {n - 1}")
        g.append(f"- p bilateral {fp(res.pvalue)}; p unilateral (H1: {h1}) {fp(res_u.pvalue)}")
        g.append(f"- IC 95% para a diferença média (antes − depois): ({br(ci.low)}; {br(ci.high)})")
        p_dec = res_u.pvalue
        conc = (f"O valor {h1} significativamente após a intervenção (t = {br(res.statistic)}; gl = {n - 1}; "
                f"p {fp(p_dec)}), {nivel(p_dec).replace('significativo ', '')}. "
                f"Diferença média de {br(abs(dbar))}, com IC 95% de {br(min(abs(ci.low), abs(ci.high)))} a "
                f"{br(max(abs(ci.low), abs(ci.high)))}." if p_dec <= ALPHA else
                f"Não há evidência significativa de que o valor {h1} (t = {br(res.statistic)}; gl = {n - 1}; "
                f"p unilateral {fp(p_dec)}).")
    else:
        w = stats.wilcoxon(antes, depois, alternative=alt)
        g.append("\n**3. Wilcoxon (não paramétrico)** — diferenças não normais com n < 30")
        g.append(f"- Mediana antes = {br(np.median(antes))}; mediana depois = {br(np.median(depois))}; "
                 f"mediana das diferenças = {br(np.median(d))}")
        g.append(f"- W = {br(w.statistic, 1)}; p unilateral {fp(w.pvalue)}")
        p_dec = w.pvalue
        conc = (f"Pelo teste de Wilcoxon, o valor {h1} significativamente (p {fp(p_dec)}), "
                f"{nivel(p_dec).replace('significativo ', '')}." if p_dec <= ALPHA else
                f"Pelo teste de Wilcoxon, não há evidência de que o valor {h1} (p {fp(p_dec)}).")
        tt = stats.ttest_rel(antes, depois, alternative=alt)
        g.append(f"- (Conferência: o t pareado daria p {fp(tt.pvalue)}.)")
    g.append(f"\n**4. Conclusão**: {conc}")
    return Exercicio("Comparação antes × depois", enun, {"Antes": antes.tolist(), "Depois": depois.tolist()},
                     "\n".join(g), "t_par", {"cenario": cenario})


# ----------------------------------------------------------------------------
# 3) t independente / Welch / Mann-Whitney
# ----------------------------------------------------------------------------
TEMAS_IND = [
    ("Tempo de deploy (min)", "Equipe A", "Equipe B", 30, 6),
    ("Pontos de função entregues", "Time Scrum", "Time Kanban", 150, 25),
    ("Salário inicial (R$ mil)", "Curso X", "Curso Y", 4.5, 0.8),
    ("Resistência do material (MPa)", "Fornecedor 1", "Fornecedor 2", 300, 30),
    ("Horas de sono", "Turno diurno", "Turno noturno", 7, 1),
]


def gerar_t_ind(rng) -> Exercicio:
    var, g1n, g2n, media, dp = random.choice(TEMAS_IND)
    cenario = random.choice(["iguais", "iguais", "var_dif", "sem_efeito", "nao_normal", "grande_n"])
    if cenario == "grande_n":
        n1, n2 = random.randint(30, 40), random.randint(30, 40)
    else:
        n1, n2 = random.randint(6, 15), random.randint(6, 15)
    ef = 0 if cenario == "sem_efeito" else dp * rng.uniform(0.8, 1.8) * random.choice([-1, 1])
    dp2 = dp * (rng.uniform(2.5, 4) if cenario == "var_dif" else rng.uniform(0.8, 1.25))
    a = rng.normal(media, dp, n1)
    if cenario in ("nao_normal", "grande_n"):
        b = media + ef - dp2 + rng.exponential(dp2, n2)
    else:
        b = rng.normal(media + ef, dp2, n2)
    dec = 1 if media < 20 else 0
    a, b = np.round(np.clip(a, 0, None), dec), np.round(np.clip(b, 0, None), dec)

    enun = (f"Compare **{var}** entre dois grupos independentes.\n\n"
            f"{g1n} (n = {n1}): {lista(a)}\n\n{g2n} (n = {n2}): {lista(b)}\n\n"
            f"a) Há diferença significativa entre os grupos (α = 5%)? Indique o teste usado e justifique.\n"
            f"b) Se houver, qual grupo é maior e com quanto de confiança?")

    g = ["**1. Descritiva**", DESC_CAB, desc_linha(g1n, a), desc_linha(g2n, b),
         "\n**2. Pré-requisitos**"]
    a = sem_extremos(g1n, a, g)
    b = sem_extremos(g2n, b, g)
    n1, n2 = len(a), len(b)
    g[2:4] = [desc_linha(g1n, a), desc_linha(g2n, b)]  # descritiva já sem extremos
    oka, ta = normal_ok(a)
    okb, tb = normal_ok(b)
    g += [f"- {g1n}: {ta}", f"- {g2n}: {tb}"]

    if oka and okb:
        va, vb = a.var(ddof=1), b.var(ddof=1)
        F = max(va, vb) / min(va, vb)
        num_df = (n1 if va >= vb else n2) - 1
        den_df = (n2 if va >= vb else n1) - 1
        pF = min(1.0, 2 * (1 - stats.f.cdf(F, num_df, den_df)))
        lev = stats.levene(a, b, center="median").pvalue
        iguais = pF > ALPHA
        g.append(f"- Teste F: F = {br(max(va, vb))} / {br(min(va, vb))} = {br(F, 3)}; gl = ({num_df}; {den_df}); "
                 f"p {fp(pF)} (Levene: p {fp(lev)}) → variâncias "
                 + ("**iguais** → t com variância combinada." if iguais else "**diferentes** → t de **Welch**."))
        res = stats.ttest_ind(a, b, equal_var=iguais)
        ci = res.confidence_interval(0.95)
        g.append("\n**3. Teste t independente" + (" (variâncias iguais)**" if iguais else " (Welch)**"))
        if iguais:
            sp = np.sqrt(((n1 - 1) * va + (n2 - 1) * vb) / (n1 + n2 - 2))
            g.append(f"- s_p = {br(sp, 3)}; EP = s_p·√(1/n1 + 1/n2) = {br(sp * np.sqrt(1 / n1 + 1 / n2), 3)}")
        g.append(f"- t = **{br(res.statistic, 3)}**; gl = {br(res.df, 0 if iguais else 1)}; p {fp(res.pvalue)}")
        g.append(f"- IC 95% para μ({g1n}) − μ({g2n}): ({br(ci.low)}; {br(ci.high)})")
        p, maior = res.pvalue, (g1n if a.mean() > b.mean() else g2n)
        conc = (f"{maior} apresenta média significativamente maior (t = {br(res.statistic, 2)}; p {fp(p)}), "
                f"{nivel(p).replace('significativo ', '')}." if p <= ALPHA else
                f"Não há diferença significativa entre as médias (t = {br(res.statistic, 2)}; p {fp(p)}).")
    else:
        mw = stats.mannwhitneyu(a, b)
        g.append("\n**3. Mann-Whitney (não paramétrico)** — algum grupo não normal com n < 30")
        g.append(f"- Medianas: {g1n} = {br(np.median(a))}; {g2n} = {br(np.median(b))}")
        g.append(f"- U = {br(mw.statistic, 1)}; p {fp(mw.pvalue)}")
        p, maior = mw.pvalue, (g1n if np.median(a) > np.median(b) else g2n)
        conc = (f"{maior} apresenta valores significativamente maiores (Mann-Whitney p {fp(p)}), "
                f"{nivel(p).replace('significativo ', '')}." if p <= ALPHA else
                f"Não há diferença significativa entre os grupos (Mann-Whitney p {fp(p)}).")
    g.append(f"\n**4. Conclusão**: {conc}")
    return Exercicio("Comparação de dois grupos", enun, {g1n: a.tolist(), g2n: b.tolist()}, "\n".join(g), "t_ind",
                     {"cenario": cenario})


# ----------------------------------------------------------------------------
# 4) ANOVA / Kruskal-Wallis
# ----------------------------------------------------------------------------
TEMAS_ANOVA = [
    ("Produtividade (peças/h)", ["Máquina A", "Máquina B", "Máquina C"], 50, 8),
    ("Tempo de carregamento (ms)", ["Servidor 1", "Servidor 2", "Servidor 3"], 400, 60),
    ("Nota final (0 a 100)", ["Turma manhã", "Turma tarde", "Turma noite"], 65, 12),
    ("Rendimento (kg/ha)", ["Adubo 1", "Adubo 2", "Adubo 3", "Controle"], 3000, 350),
]


def gerar_anova(rng) -> Exercicio:
    var, nomes, media, dp = random.choice(TEMAS_ANOVA)
    cenario = random.choice(["efeito", "efeito", "sem_efeito", "nao_normal", "var_dif"])
    k = len(nomes)
    n = random.randint(8, 20) if cenario != "efeito" else random.choice([random.randint(8, 20), random.randint(30, 35)])
    medias = media + (0 if cenario == "sem_efeito" else 1) * rng.normal(0, dp * 0.9, k)
    grupos = []
    for i in range(k):
        s = dp * (rng.uniform(3.5, 4.5) if cenario == "var_dif" and i == k - 1 else rng.uniform(0.8, 1.2))
        if cenario == "nao_normal" and i == 0:
            v = medias[i] - s + rng.exponential(s, n)
        else:
            v = rng.normal(medias[i], s, n)
        teto = 100 if "0 a 100" in var else None
        grupos.append(np.round(np.clip(v, 0, teto), 0))

    enun = (f"Deseja-se comparar **{var}** entre {k} grupos ({', '.join(nomes)}), com {n} observações cada.\n\n"
            + "\n\n".join(f"{nm}: {lista(v)}" for nm, v in zip(nomes, grupos))
            + "\n\na) Existe diferença entre os grupos (α = 5%)? Indique o teste e verifique os pré-requisitos.\n"
              "b) Se existir, quais grupos diferem entre si?")

    g = ["**1. Descritiva**", DESC_CAB] + [desc_linha(nm, v) for nm, v in zip(nomes, grupos)]
    g.append("\n**2. Pré-requisitos**")
    grupos = [sem_extremos(nm, v, g) for nm, v in zip(nomes, grupos)]
    g[2:2 + k] = [desc_linha(nm, v) for nm, v in zip(nomes, grupos)]  # descritiva já sem extremos
    oks = []
    for nm, v in zip(nomes, grupos):
        ok, t = normal_ok(v)
        oks.append(ok)
        g.append(f"- {nm}: {t}")
    vars_ = [v.var(ddof=1) for v in grupos]
    razao = max(vars_) / min(vars_)
    var_ok = razao <= RAZAO_MAX_VAR
    g.append(f"- Variâncias: maior/menor = {br(max(vars_))} / {br(min(vars_))} = {br(razao)} → "
             + (f"dentro do critério (≤ {RAZAO_MAX_VAR}×)." if var_ok else f"**acima de {RAZAO_MAX_VAR}×**."))

    if all(oks) and var_ok:
        f = stats.f_oneway(*grupos)
        allv = np.concatenate(grupos)
        gm, N = allv.mean(), len(allv)
        sqe = sum(len(v) * (v.mean() - gm) ** 2 for v in grupos)
        sqd = sum(((v - v.mean()) ** 2).sum() for v in grupos)
        g.append("\n**3. ANOVA (1 fator)**")
        g.append("| Fonte | gl | SQ | QM | F | p |\n|---|---|---|---|---|---|")
        g.append(f"| Entre grupos | {k - 1} | {br(sqe)} | {br(sqe / (k - 1))} | {br(f.statistic, 3)} | {fpv(f.pvalue)} |")
        g.append(f"| Dentro | {N - k} | {br(sqd)} | {br(sqd / (N - k))} | | |")
        g.append(f"| Total | {N - 1} | {br(sqe + sqd)} | | | |")
        g.append(f"\nR² = {br(100 * sqe / (sqe + sqd), 1)}%")
        if f.pvalue <= ALPHA:
            tk = stats.tukey_hsd(*grupos)
            ci = tk.confidence_interval(0.95)
            g.append("\n**4. Tukey**\n\n| Par | Diferença | p | IC 95% |\n|---|---|---|---|")
            difs = []
            for i in range(k):
                for j in range(i + 1, k):
                    dif = grupos[i].mean() - grupos[j].mean()
                    g.append(f"| {nomes[i]} − {nomes[j]} | {br(dif)} | {fpv(tk.pvalue[i, j])} | "
                             f"({br(ci.low[i, j])}; {br(ci.high[i, j])}) |")
                    if tk.pvalue[i, j] <= ALPHA:
                        difs.append(f"{nomes[i] if dif > 0 else nomes[j]} > {nomes[j] if dif > 0 else nomes[i]} "
                                    f"({nivel(tk.pvalue[i, j]).replace('significativo com ', '')})")
            conc = (f"Há diferença significativa entre os grupos (F = {br(f.statistic, 2)}; p {fp(f.pvalue)}). "
                    f"Pelo Tukey: {'; '.join(difs) if difs else 'nenhum par isolado atingiu significância'}. "
                    "Os pares não citados não diferem significativamente.")
        else:
            conc = f"Não há diferença significativa entre as médias dos grupos (F = {br(f.statistic, 2)}; p {fp(f.pvalue)})."
    else:
        motivo = "falta de normalidade com n < 30" if not all(oks) else f"razão de variâncias > {RAZAO_MAX_VAR}"
        kw = stats.kruskal(*grupos)
        g.append(f"\n**3. Kruskal-Wallis** — pré-requisito da ANOVA violado ({motivo})")
        g.append(f"- Medianas: " + "; ".join(f"{nm} = {br(np.median(v))}" for nm, v in zip(nomes, grupos)))
        g.append(f"- H = {br(kw.statistic, 3)}; gl = {k - 1}; p {fp(kw.pvalue)}")
        if kw.pvalue <= ALPHA:
            m = k * (k - 1) // 2
            g.append(f"\n**4. Comparações 2 a 2** (Mann-Whitney com Bonferroni: p × {m})")
            difs = []
            for i in range(k):
                for j in range(i + 1, k):
                    pb = min(1.0, stats.mannwhitneyu(grupos[i], grupos[j]).pvalue * m)
                    g.append(f"- {nomes[i]} × {nomes[j]}: p {fp(pb)}")
                    if pb <= ALPHA:
                        hi_, lo_ = (nomes[i], nomes[j]) if np.median(grupos[i]) > np.median(grupos[j]) else (nomes[j], nomes[i])
                        difs.append(f"{hi_} > {lo_}")
            conc = (f"Há diferença significativa entre os grupos (Kruskal-Wallis p {fp(kw.pvalue)}). "
                    f"Diferenças: {'; '.join(difs) if difs else 'nenhum par isolado atingiu significância após a correção'}.")
        else:
            conc = f"Não há diferença significativa entre os grupos (Kruskal-Wallis p {fp(kw.pvalue)})."
        f = stats.f_oneway(*grupos)
        g.append(f"- (Conferência: a ANOVA daria F = {br(f.statistic, 2)}; p {fp(f.pvalue)}. "
                 "Alternativa para variâncias diferentes: ANOVA de Welch.)")
    g.append(f"\n**Conclusão**: {conc}")
    return Exercicio("Comparação de 3 ou mais grupos", enun, dict(zip(nomes, [v.tolist() for v in grupos])),
                     "\n".join(g), "anova", {"cenario": cenario})


# ----------------------------------------------------------------------------
# 5) Duas proporções / Fisher
# ----------------------------------------------------------------------------
TEMAS_PROP = [
    ("aprovação na disciplina", "Turma com monitoria", "Turma sem monitoria"),
    ("peças defeituosas", "Linha 1", "Linha 2"),
    ("conversão de visitantes em clientes", "Página versão A", "Página versão B"),
    ("falha no build", "Pipeline antigo", "Pipeline novo"),
]


def gerar_prop(rng) -> Exercicio:
    evento, g1n, g2n = random.choice(TEMAS_PROP)
    pequeno = random.random() < 0.3
    n1, n2 = (random.randint(8, 18), random.randint(8, 18)) if pequeno else (random.randint(40, 200), random.randint(40, 200))
    p1 = rng.uniform(0.1, 0.8)
    p2 = np.clip(p1 + random.choice([0, rng.uniform(0.1, 0.3) * random.choice([-1, 1])]), 0.03, 0.97)
    x1, x2 = int(rng.binomial(n1, p1)), int(rng.binomial(n2, p2))

    enun = (f"Avaliou-se a ocorrência de **{evento}** em dois grupos independentes:\n\n"
            f"- {g1n}: {x1} ocorrências em {n1}\n- {g2n}: {x2} ocorrências em {n2}\n\n"
            f"A proporção de {evento} difere entre os grupos (α = 5%)?")

    ph1, ph2 = x1 / n1, x2 / n2
    pc = (x1 + x2) / (n1 + n2)
    g = ["**1. Proporções amostrais**",
         f"- p̂1 = {x1}/{n1} = {br(ph1, 4)}; p̂2 = {x2}/{n2} = {br(ph2, 4)}; p combinada = {br(pc, 4)}",
         "\n**2. Pré-requisito**"]
    ok_apost = all(n * p * (1 - p) >= 5 for n, p in ((n1, ph1), (n2, ph2)))
    ok_livros = all(min(n * p, n * (1 - p)) >= 5 for n, p in ((n1, ph1), (n2, ph2)))
    g.append(f"- n·p·q (apostila): {g1n} = {br(n1 * ph1 * (1 - ph1))}; {g2n} = {br(n2 * ph2 * (1 - ph2))} → "
             + ("atendido" if ok_apost else "**não atendido**"))
    g.append(f"- n·p ≥ 5 e n·q ≥ 5 (critério de muitos livros): " + ("atendido" if ok_livros else "**não atendido**"))
    fisher = stats.fisher_exact([[x1, n1 - x1], [x2, n2 - x2]])
    if ok_apost:
        ep = np.sqrt(pc * (1 - pc) * (1 / n1 + 1 / n2))
        z = (ph1 - ph2) / ep if ep > 0 else 0.0
        p = 2 * (1 - stats.norm.cdf(abs(z)))
        g.append("\n**3. Teste de duas proporções (aproximação normal)**")
        g.append(f"- EP = √(p·q·(1/n1 + 1/n2)) = {br(ep, 4)}; z = (p̂1 − p̂2)/EP = **{br(z, 3)}**; p {fp(p)}")
        g.append(f"- (Conferência — exato de Fisher: p {fp(fisher.pvalue)})")
    else:
        p = fisher.pvalue
        g.append(f"\n**3. Teste exato de Fisher** (pré-requisito não atendido): p {fp(p)}")
    maior = g1n if ph1 > ph2 else g2n
    conc = (f"A proporção de {evento} é significativamente maior em {maior} (p {fp(p)}), "
            f"{nivel(p).replace('significativo ', '')}." if p <= ALPHA else
            f"Não há diferença significativa entre as proporções de {evento} (p {fp(p)}).")
    g.append(f"\n**4. Conclusão**: {conc}")
    return Exercicio("Comparação de proporções", enun,
                     {"Grupo": [g1n, g2n], "Ocorrências": [x1, x2], "Total": [n1, n2]}, "\n".join(g), "prop")


GERADORES = {"corr": gerar_corr, "t_par": gerar_t_par, "t_ind": gerar_t_ind, "anova": gerar_anova, "prop": gerar_prop}


# ----------------------------------------------------------------------------
# saída
# ----------------------------------------------------------------------------
def _gerar_valido(fn, rng, tentativas: int = 30) -> Exercicio:
    """Sorteia de novo se os dados saírem degenerados (ex.: coluna constante)."""
    import warnings
    for _ in range(tentativas):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            try:
                return fn(rng)
            except (Warning, ValueError, ZeroDivisionError, FloatingPointError):
                continue
    return fn(rng)


def gerar_lista(n: int, tipos: list[str], seed: int | None) -> list[Exercicio]:
    if seed is None:
        seed = random.randrange(1_000_000)
    random.seed(seed)
    rng = np.random.default_rng(seed)
    seq = [tipos[i % len(tipos)] for i in range(n)]
    random.shuffle(seq)
    exs = [_gerar_valido(GERADORES[t], rng) for t in seq]
    for e in exs:
        e.extra["seed"] = seed
    return exs


def salvar_md(exs: list[Exercicio], pasta: Path, seed: int) -> tuple[Path, Path]:
    cab = (f"*Semente: {seed} — rode de novo com `--seed {seed}` para obter a mesma lista.*\n\n"
           "Para cada exercício: verifique os pré-requisitos (outliers, normalidade, variâncias), escolha o teste, "
           "calcule e conclua na linguagem do problema. Use α = 5%.\n")
    enun = ["# Lista de exercícios — Análise Estatística\n", cab]
    gab = ["# Gabarito — Análise Estatística\n", f"*Semente: {seed}*\n",
           "> Valores calculados com SciPy. Pequenas diferenças em relação ao Excel/Minitab podem ocorrer "
           "(arredondamento, método dos quartis, teste de normalidade usado).\n"]
    for i, e in enumerate(exs, 1):
        enun.append(f"\n## Exercício {i} — {e.titulo}\n\n{e.enunciado}\n")
        gab.append(f"\n## Exercício {i} — {e.titulo}\n\n{e.gabarito}\n")
    pasta.mkdir(parents=True, exist_ok=True)
    pe, pg = pasta / f"exercicios_{seed}.md", pasta / f"gabarito_{seed}.md"
    pe.write_text("\n".join(enun), encoding="utf-8")
    pg.write_text("\n".join(gab), encoding="utf-8")
    return pe, pg


def salvar_xlsx(exs: list[Exercicio], pasta: Path, seed: int) -> Path | None:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        print("openpyxl não instalado — pulei a planilha (pip install openpyxl).")
        return None
    wb = Workbook()
    wb.remove(wb.active)
    for i, e in enumerate(exs, 1):
        ws = wb.create_sheet(f"Ex{i}")
        ws.append([f"Exercício {i} — {e.titulo}"])
        ws["A1"].font = Font(bold=True)
        ws.append([])
        cols = list(e.dados.keys())
        ws.append(cols)
        for c in ws[3]:
            c.font = Font(bold=True)
        for r in range(max(len(v) for v in e.dados.values())):
            ws.append([e.dados[c][r] if r < len(e.dados[c]) else None for c in cols])
        for j in range(len(cols)):
            ws.column_dimensions[chr(65 + j)].width = max(14, len(cols[j]) + 2)
    p = pasta / f"dados_{seed}.xlsx"
    wb.save(p)
    return p


def interativo(exs: list[Exercicio]) -> None:
    for i, e in enumerate(exs, 1):
        print("\n" + "=" * 70 + f"\nExercício {i}/{len(exs)} — {e.titulo}\n" + "=" * 70)
        print(e.enunciado)
        input("\n[Enter] para ver o gabarito...")
        print("\n" + e.gabarito)
        if i < len(exs) and input("\n[Enter] próximo  |  q + Enter para sair: ").strip().lower() == "q":
            break


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera exercícios aleatórios de análise estatística com gabarito.")
    ap.add_argument("-n", type=int, default=6, help="quantidade de exercícios (padrão 6)")
    ap.add_argument("-t", "--tipos", default=",".join(GERADORES), help=f"tipos separados por vírgula: {','.join(GERADORES)}")
    ap.add_argument("--seed", type=int, default=None, help="semente para reproduzir a lista")
    ap.add_argument("-o", "--saida", default="exercicios_gerados", help="pasta de saída")
    ap.add_argument("--xlsx", action="store_true", help="também salva os dados em .xlsx (uma aba por exercício)")
    ap.add_argument("--interativo", action="store_true", help="pratica no terminal em vez de salvar arquivos")
    a = ap.parse_args()

    tipos = [t.strip() for t in a.tipos.split(",") if t.strip()]
    inval = [t for t in tipos if t not in GERADORES]
    if inval:
        ap.error(f"tipos inválidos: {inval}. Use: {', '.join(GERADORES)}")
    exs = gerar_lista(a.n, tipos, a.seed)
    seed = exs[0].extra["seed"]

    if a.interativo:
        print(f"Semente: {seed}")
        interativo(exs)
        return
    pasta = Path(a.saida)
    pe, pg = salvar_md(exs, pasta, seed)
    print(f"Exercícios: {pe}\nGabarito:   {pg}")
    if a.xlsx and (px := salvar_xlsx(exs, pasta, seed)):
        print(f"Dados:      {px}")


if __name__ == "__main__":
    main()
