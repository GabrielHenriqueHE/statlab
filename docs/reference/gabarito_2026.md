# Gabarito — Análise Estatística

*Semente: 2026*

> Valores calculados com SciPy. Pequenas diferenças em relação ao Excel/Minitab podem ocorrer (arredondamento, método dos quartis, teste de normalidade usado).


## Exercício 1 — Correlação e regressão

**1. Pré-requisitos**
- x: Q1 = 25,00; Q3 = 41,00; D = 16,00; sem outliers.
- y: Q1 = 6,00; Q3 = 9,00; D = 3,00; **outlier suave**: 16 (analisar com e sem). 
- Normalidade: x p = 0,605; y p = 0,189 → ambas normais: usar **Pearson**.

**2. Cálculo de r (Pearson)**
- n = 9; Σx = 295,0; Σy = 76,0; Σxy = 2.528,0; Σx² = 11.271,0; Σy² = 736,0
- Numerador = n·Σxy − Σx·Σy = 332,0
- Denominador = √(n·Σx² − (Σx)²) · √(n·Σy² − (Σy)²) = √14.414,0 · √848,0 = 3.496,15
- **r = 0,095**; p = 0,808
- Valores críticos (n = 9): 0,666 (5%) e 0,798 (1%) → |r| = 0,095 → não significativo
- Spearman: r_s = 0,438; p = 0,239 → não significativo

**3. Conclusão**
Não existe correlação linear significativa entre nº de commits na semana e bugs reportados (Pearson: r = 0,095; p = 0,808). A regressão **não** deve ser feita. Olhe o diagrama de dispersão: pode haver relação não linear.

**Análise sem o(s) outlier(s) suave(s)** (n = 8): r = 0,972; p < 0,001 → significativo com 99% de confiança.
A conclusão **muda** com a retirada do outlier. Se ele for erro de medição/digitação, vale a análise sem ele; se for um dado real, relate as duas análises e investigue o caso.


## Exercício 2 — Comparação antes × depois

**1. Tipo de dado**: mesmos indivíduos medidos duas vezes → dados **pareados**. Analisa-se a diferença d = antes − depois.

**2. Pré-requisitos (nas diferenças)**
- d: Q1 = 17,50; Q3 = 98,25; D = 80,75; sem outliers.
- Shapiro-Wilk p = 0,192 → pode-se assumir normalidade
- Igualdade de variâncias **não** é exigida no teste pareado.

**3. Teste t pareado**
- d̄ = 55,00; s_d = 46,78; EP = s_d/√n = 13,50
- t = d̄ / EP = **4,07**; gl = 11
- p bilateral = 0,002; p unilateral (H1: diminuiu) < 0,001
- IC 95% para a diferença média (antes − depois): (25,28; 84,72)

**4. Conclusão**: O valor diminuiu significativamente após a intervenção (t = 4,07; gl = 11; p < 0,001), com 99% de confiança. Diferença média de 55,00, com IC 95% de 25,28 a 84,72.


## Exercício 3 — Comparação de dois grupos

**1. Descritiva**
| Grupo | n | Média | Mediana | Desvio padrão | Variância |
|---|---|---|---|---|---|
| Equipe A | 6 | 36,67 | 36,50 | 7,28 | 53,07 |
| Equipe B | 13 | 31,77 | 30,00 | 6,50 | 42,19 |

**2. Pré-requisitos**
- Equipe A: Q1 = 34,00; Q3 = 42,00; D = 8,00; sem outliers.
- Equipe B: Q1 = 27,00; Q3 = 35,00; D = 8,00; sem outliers.
- Equipe A: Shapiro-Wilk p = 0,692 → pode-se assumir normalidade
- Equipe B: Shapiro-Wilk p = 0,131 → pode-se assumir normalidade
- Teste F: F = 53,07 / 42,19 = 1,258; gl = (5; 12); p = 0,686 (Levene: p = 0,750) → variâncias **iguais** → t com variância combinada.

**3. Teste t independente (variâncias iguais)**
- s_p = 6,737; EP = s_p·√(1/n1 + 1/n2) = 3,325
- t = **1,473**; gl = 17; p = 0,159
- IC 95% para μ(Equipe A) − μ(Equipe B): (-2,12; 11,91)

**4. Conclusão**: Não há diferença significativa entre as médias (t = 1,47; p = 0,159).


## Exercício 4 — Comparação de 3 ou mais grupos

**1. Descritiva**
| Grupo | n | Média | Mediana | Desvio padrão | Variância |
|---|---|---|---|---|---|
| Turma manhã | 32 | 53,25 | 52,50 | 12,89 | 166,26 |
| Turma tarde | 32 | 50,19 | 51,50 | 10,57 | 111,77 |
| Turma noite | 32 | 56,09 | 56,50 | 14,33 | 205,44 |

**2. Pré-requisitos**
- Turma manhã: Q1 = 46,00; Q3 = 60,00; D = 14,00; **outlier suave**: 82 (analisar com e sem). 
- Turma tarde: Q1 = 43,00; Q3 = 59,00; D = 16,00; sem outliers.
- Turma noite: Q1 = 44,75; Q3 = 65,00; D = 20,25; sem outliers.
- Turma manhã: Shapiro-Wilk p = 0,714 → pode-se assumir normalidade
- Turma tarde: Shapiro-Wilk p = 0,218 → pode-se assumir normalidade
- Turma noite: Shapiro-Wilk p = 0,981 → pode-se assumir normalidade
- Variâncias: maior/menor = 205,44 / 111,77 = 1,84 → dentro do critério (≤ 9×).

**3. ANOVA (1 fator)**
| Fonte | gl | SQ | QM | F | p |
|---|---|---|---|---|---|
| Entre grupos | 2 | 558,40 | 279,20 | 1,732 | 0,183 |
| Dentro | 93 | 14.987,59 | 161,16 | | |
| Total | 95 | 15.545,99 | | | |

R² = 3,6%

**Conclusão**: Não há diferença significativa entre as médias dos grupos (F = 1,73; p = 0,183).


## Exercício 5 — Comparação de 3 ou mais grupos

**1. Descritiva**
| Grupo | n | Média | Mediana | Desvio padrão | Variância |
|---|---|---|---|---|---|
| Turma manhã | 19 | 91,63 | 91,00 | 7,84 | 61,47 |
| Turma tarde | 17 | 58,18 | 58,00 | 4,35 | 18,90 |
| Turma noite | 19 | 69,53 | 66,00 | 10,87 | 118,15 |

**2. Pré-requisitos**
- Turma manhã: Q1 = 84,50; Q3 = 100,00; D = 15,50; sem outliers.
- Turma tarde: Q1 = 55,50; Q3 = 60,00; D = 4,50; **outlier extremo**: 37; 38 (deve ser excluído). **outlier suave**: 69 (analisar com e sem). 
  → análise de Turma tarde feita **sem** os extremos (n = 17).
- Turma noite: Q1 = 64,50; Q3 = 77,00; D = 12,50; sem outliers.
- Turma manhã: Shapiro-Wilk p = 0,004 → NÃO normal e n = 19 < 30
- Turma tarde: Shapiro-Wilk p = 0,270 → pode-se assumir normalidade
- Turma noite: Shapiro-Wilk p = 0,288 → pode-se assumir normalidade
- Variâncias: maior/menor = 118,15 / 18,90 = 6,25 → dentro do critério (≤ 9×).

**3. Kruskal-Wallis** — pré-requisito da ANOVA violado (falta de normalidade com n < 30)
- Medianas: Turma manhã = 91,00; Turma tarde = 58,00; Turma noite = 66,00
- H = 38,537; gl = 2; p < 0,001

**4. Comparações 2 a 2** (Mann-Whitney com Bonferroni: p × 3)
- Turma manhã × Turma tarde: p < 0,001
- Turma manhã × Turma noite: p < 0,001
- Turma tarde × Turma noite: p = 0,002
- (Conferência: a ANOVA daria F = 77,48; p < 0,001. Alternativa para variâncias diferentes: ANOVA de Welch.)

**Conclusão**: Há diferença significativa entre os grupos (Kruskal-Wallis p < 0,001). Diferenças: Turma manhã > Turma tarde; Turma manhã > Turma noite; Turma noite > Turma tarde.


## Exercício 6 — Comparação de proporções

**1. Proporções amostrais**
- p̂1 = 31/62 = 0,5000; p̂2 = 117/182 = 0,6429; p combinada = 0,6066

**2. Pré-requisito**
- n·p·q (apostila): Turma com monitoria = 15,50; Turma sem monitoria = 41,79 → atendido
- n·p ≥ 5 e n·q ≥ 5 (critério de muitos livros): atendido

**3. Teste de duas proporções (aproximação normal)**
- EP = √(p·q·(1/n1 + 1/n2)) = 0,0718; z = (p̂1 − p̂2)/EP = **-1,989**; p = 0,047
- (Conferência — exato de Fisher: p = 0,052)

**4. Conclusão**: A proporção de aprovação na disciplina é significativamente maior em Turma sem monitoria (p = 0,047), com 95% de confiança.


## Exercício 7 — Comparação de dois grupos

**1. Descritiva**
| Grupo | n | Média | Mediana | Desvio padrão | Variância |
|---|---|---|---|---|---|
| Fornecedor 1 | 15 | 315,07 | 320,00 | 38,12 | 1.452,78 |
| Fornecedor 2 | 10 | 268,10 | 263,00 | 22,47 | 504,77 |

**2. Pré-requisitos**
- Fornecedor 1: Q1 = 282,00; Q3 = 336,50; D = 54,50; sem outliers.
- Fornecedor 2: Q1 = 258,00; Q3 = 279,00; D = 21,00; **outlier suave**: 316 (analisar com e sem). 
- Fornecedor 1: Shapiro-Wilk p = 0,189 → pode-se assumir normalidade
- Fornecedor 2: Shapiro-Wilk p = 0,497 → pode-se assumir normalidade
- Teste F: F = 1.452,78 / 504,77 = 2,878; gl = (14; 9); p = 0,115 (Levene: p = 0,144) → variâncias **iguais** → t com variância combinada.

**3. Teste t independente (variâncias iguais)**
- s_p = 32,891; EP = s_p·√(1/n1 + 1/n2) = 13,428
- t = **3,498**; gl = 23; p = 0,002
- IC 95% para μ(Fornecedor 1) − μ(Fornecedor 2): (19,19; 74,74)

**4. Conclusão**: Fornecedor 1 apresenta média significativamente maior (t = 3,50; p = 0,002), com 99% de confiança.


## Exercício 8 — Comparação de proporções

**1. Proporções amostrais**
- p̂1 = 58/148 = 0,3919; p̂2 = 41/63 = 0,6508; p combinada = 0,4692

**2. Pré-requisito**
- n·p·q (apostila): Página versão A = 35,27; Página versão B = 14,32 → atendido
- n·p ≥ 5 e n·q ≥ 5 (critério de muitos livros): atendido

**3. Teste de duas proporções (aproximação normal)**
- EP = √(p·q·(1/n1 + 1/n2)) = 0,0751; z = (p̂1 − p̂2)/EP = **-3,449**; p < 0,001
- (Conferência — exato de Fisher: p < 0,001)

**4. Conclusão**: A proporção de conversão de visitantes em clientes é significativamente maior em Página versão B (p < 0,001), com 99% de confiança.


## Exercício 9 — Correlação e regressão

**1. Pré-requisitos**
- x: Q1 = 23,25; Q3 = 46,00; D = 22,75; sem outliers.
- y: Q1 = 6,00; Q3 = 9,00; D = 3,00; sem outliers.
- Normalidade: x p = 0,333; y p = 0,419 → ambas normais: usar **Pearson**.

**2. Cálculo de r (Pearson)**
- n = 30; Σx = 991,0; Σy = 210,0; Σxy = 7.948,0; Σx² = 39.113,0; Σy² = 1.644,0
- Numerador = n·Σxy − Σx·Σy = 30.330,0
- Denominador = √(n·Σx² − (Σx)²) · √(n·Σy² − (Σy)²) = √191.309,0 · √5.220,0 = 31.601,15
- **r = 0,960**; p < 0,001
- Valores críticos (n = 30): 0,361 (5%) e 0,463 (1%) → |r| = 0,960 → significativo com 99% de confiança
- Spearman: r_s = 0,942; p < 0,001 → significativo com 99% de confiança

**3. Conclusão**
Existe correlação positiva e muito forte entre nº de commits na semana e bugs reportados, significativa com 99% de confiança (Pearson: r = 0,960; p < 0,001). r² = 92,1%: essa parcela da variação de y é explicada por x; o restante (7,9%) se deve a outros fatores.

**4. Regressão**: a = 30.330,0 / 191.309,0 = **0,1585**; b = ȳ − a·x̄ = 7,000 − 0,1585·33,033 = **1,763**
- ŷ = 0,1585x + 1,763
- A cada unidade a mais de x, y aumenta em média 0,159.
- Para x = 32: ŷ = 6,84 (dentro da faixa observada de x: 6 a 59).


## Exercício 10 — Comparação antes × depois

**1. Tipo de dado**: mesmos indivíduos medidos duas vezes → dados **pareados**. Analisa-se a diferença d = antes − depois.

**2. Pré-requisitos (nas diferenças)**
- d: Q1 = -8,00; Q3 = -2,00; D = 6,00; **outlier extremo**: -42 (deve ser excluído). **outlier suave**: -18; -24 (analisar com e sem). 
  → análise de d feita **sem** os extremos (n = 16).
- Shapiro-Wilk p = 0,003 → NÃO normal e n = 16 < 30
- Igualdade de variâncias **não** é exigida no teste pareado.

**3. Wilcoxon (não paramétrico)** — diferenças não normais com n < 30
- Mediana antes = 55,50; mediana depois = 61,00; mediana das diferenças = -4,00
- W = 0,0; p unilateral < 0,001
- (Conferência: o t pareado daria p < 0,001.)

**4. Conclusão**: Pelo teste de Wilcoxon, o valor aumentou significativamente (p < 0,001), com 99% de confiança.
