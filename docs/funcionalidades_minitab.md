# Funcionalidades do Minitab × statlab

Inventário feito a partir do menu do Minitab (lista colada pelo usuário), da brochure
(`Minitab-Brochure_PT.pdf`) e do guia "Introdução ao Minitab" (`MinitabGettingStarted-v032024_PT.pdf`).

O Minitab é um produto amplo (centenas de análises). O statlab cobre o que a disciplina de Probabilidade e
Estatística usa, com as mesmas saídas e nomenclatura do Minitab — e, desde o pivô, com o mesmo contrato: **cada
item abaixo é um comando que o usuário escolhe, com as opções explícitas no diálogo.** O app não troca o teste,
não exclui dados e não redige conclusão (ver `CLAUDE.md`).

## Legenda

| Símbolo | Situação |
|---|---|
| ✅ | Implementado (interface e núcleo) |
| 🟡 | Núcleo pronto e testado; falta a tela (fase indicada) |
| 🔵 | Backlog (proposto; depende de prioridade) |
| ⚪ | Fora do escopo (produto/área que a disciplina não usa) |

## Dados (menu Dados, Arquivo e Calc)

| Item do Minitab | Situação | Observação |
|---|---|---|
| Abrir arquivo Excel (aba e intervalo, ex.: C8:D12) | ✅ F2 | `.xlsx`; aba e intervalo como no Minitab |
| Abrir CSV / texto | ✅ F2 | separador automático (`;`, tab, `,`) e acentos cp1252/UTF-8 |
| Colar dados (do Excel) | ✅ F2 | tab, `;` ou lista de valores |
| Editar a worksheet | ✅ F2 | `st.data_editor`, com linhas dinâmicas |
| Empilhar colunas (Dados › Empilhar) | ✅ F2 | faltantes descartados, com contagem |
| Desempilhar (Dados › Desempilhar) | ✅ F2 | uma coluna por nível, faltantes no fim |
| Subconjuntos / pares completos | ✅ F2 | `pares_completos` (aviso de linhas descartadas) |
| Várias worksheets na sessão | ✅ F2 | seletor lateral "Worksheet ativa" |
| Calculadora (fórmulas em colunas) | 🔵 | atribuir fórmula a coluna; útil, complexidade média |
| Datas/horas como tipo de dado | 🔵 | hoje o eixo temporal aceita rótulos de texto |
| Salvar/abrir projeto `.MPJ` | ⚪ | equivalente seria salvar a sessão; não é prioridade |
| Recodificar valores | ✅ | aba Recodificar (Dados): grava em coluna nova; numérica se todos os novos valores forem números |

## Gráficos (menu Gráficos e Análise gráfica)

| Item do Minitab | Situação | Observação |
|---|---|---|
| Histograma (com ajuste normal) | ✅ F2 | curva normal ajustada por grupo |
| Boxplot | ✅ F2 | outliers pela mesma regra 1,5 D |
| Diagrama de dispersão (com grupos e reta) | ✅ F2 | reta de mínimos quadrados opcional |
| Gráfico de valores individuais | ✅ F2 | média por grupo unida por linha |
| Gráfico de intervalos (IC da média) | ✅ F2 | t de Student, nível de confiança fixo em 95% na tela |
| Gráfico de probabilidade normal | ✅ F2 | título com Anderson-Darling |
| Gráfico de Pareto | ✅ F2 | barras + % acumulada (eixo direito) |
| Gráfico de barras | ✅ F2 | média por categoria |
| Gráfico de séries temporais | ✅ F2 | rótulos opcionais no eixo X |
| Correlograma (mapa de calor de r) | ✅ F2 | Pearson, pares completos por par de colunas |
| Matriz de dispersão | ✅ F2 | pares completos em todas as colunas |
| Gráfico de efeitos principais / interações | ✅ | na ANOVA de 2 fatores |
| Gráfico de Tukey (ICs simultâneos) | ✅ | quando a opção Tukey é marcada |
| Diagrama de pontos, mapa de calor genérico | 🔵 | baixa prioridade |
| Gráficos de resíduos (4 em 1) | ✅ | regressão múltipla e ANOVA de 2 fatores |
| Construtor de gráficos interativo (arrastar variáveis) | 🔵 | hoje uma página por tipo; o Minitab tem uma galeria |
| Layout de vários gráficos / anotações | 🔵 | |
| Gráficos de contorno, 3D, superfície | ⚪ | DOE / superfície de resposta |
| Função "brush" (selecionar pontos) | 🔵 | Plotly tem seleção nativa; falta usar o resultado |
| Atualização automática com os dados | ✅ | gráficos são recalculados a partir da worksheet ativa |
| Exportar HTML interativo | ✅ F2 | plotly.js embutido, sem CDN |
| Exportar PNG/SVG (TIF, JPEG, BMP, GIF, EMF) | ⚪ | decidido: só HTML; PNG pelo botão de câmera do gráfico no navegador |

## Estatísticas básicas

| Item do Minitab | Situação | Observação |
|---|---|---|
| Estatísticas descritivas (N, N*, média, EP, DP, quartis, IC) | ✅ F2 | formato do relatório do Minitab, por grupo |
| Assimetria e curtose | ✅ F2 | G1 e G2 ajustadas, como no Minitab |
| Teste de normalidade Anderson-Darling | ✅ F2 | padrão do Minitab; p por Stephens (validado pela brochure) |
| Teste de normalidade Shapiro-Wilk | ✅ | **opção** de método no comando Normalidade (sem o atalho do TCL) |
| Teste de normalidade Ryan-Joiner | ⚪ | não implementado: sem referência verificável para o p (nota no README) |
| Correlação (Pearson e Spearman) | ✅ | **opção** do diálogo: o usuário escolhe o método |
| Covariância | ✅ | Estatísticas descritivas, com 2+ variáveis (n − 1; pares completos por par) |
| Teste de outlier (Grubbs) | 🔵 | a disciplina usa a regra do diagrama de caixa (já implementada) |
| Teste Z para uma amostra | ✅ F3 | σ conhecido; avisa se a amostra não é normal com n < 30 |
| Teste t para uma amostra | ✅ | comando próprio; o Wilcoxon de uma amostra é outro comando |
| Teste t para duas amostras / pareado | ✅ | 2 amostras tem a **opção** "assumir variâncias iguais" (combinada ou Welch) |
| Testes de uma e duas proporções | ✅ | **opção** do método: z ou binomial exata (uma); z ou Fisher (duas) |
| Taxa de Poisson (uma e duas amostras) | 🔵 | |
| Teste para uma e duas variâncias | ✅ | página Variâncias: uma variância (χ², sem atalho do TCL; Bonett não implementado); duas também na página Dois grupos |
| Teste de igualdade de variâncias (Levene/Bartlett) | ✅ | F, Bartlett e Levene (mediana) são **comandos distintos** |
| Testes de equivalência | 🔵 | |

## Testes não paramétricos

| Item do Minitab | Situação | Observação |
|---|---|---|
| Wilcoxon (pareado e uma amostra) | ✅ | comando escolhido pelo usuário |
| Mann-Whitney | ✅ | comando escolhido pelo usuário |
| Kruskal-Wallis + comparações | ✅ | comparações 2 a 2 (Mann-Whitney com Bonferroni) são **opção**; nota: fora da apostila |
| Teste de sinal | ✅ | binomial exata; para pareado, aplicar à coluna das diferenças |
| Friedman, mediana de Mood | 🔵 | |

## Tabelas e qui-quadrado

| Item do Minitab | Situação | Observação |
|---|---|---|
| Teste exato de Fisher (2 × 2) | ✅ | comando próprio; também **opção** de método em Duas proporções |
| Qui-quadrado (independência e ajuste) | ✅ | Pearson (sem Yates) + razão de verossimilhança; Cochran como nota |
| Tabulação de contagens / cruzadas | ✅ F3 (parcial) | tabela de contingência a partir de duas colunas |
| Estatísticas tabuladas (Construtor de tabelas) | 🔵 | média/contagem por grupo |

## Regressão

| Item do Minitab | Situação | Observação |
|---|---|---|
| Regressão linear simples (com R², coeficientes, previsão) | ✅ | **sempre calculada** (é a múltipla com um preditor); nota de extrapolação |
| Regressão linear múltipla | ✅ | coeficientes com VIF, S, R², R²(aj), R²(pred), ANOVA, predição com IC e IP; validada contra o guia do Minitab |
| Regressão polinomial | 🔵 | |
| Regressão não linear, ortogonal, PLS, Poisson, logística, Cox | ⚪ | fora da disciplina |
| Stepwise, melhores subconjuntos | ⚪ | depois da múltipla, se houver demanda |

## Análise de variância

| Item do Minitab | Situação | Observação |
|---|---|---|
| ANOVA de 1 fator (tabela SQ/QM/F/p/R²) | ✅ | comando próprio; Kruskal-Wallis é outro comando |
| Tukey (comparações múltiplas) | ✅ | **opção** do diálogo (nunca automático); tabela + gráfico de ICs simultâneos |
| ANOVA de Welch | ✅ | **opção** do diálogo da ANOVA de 1 fator |
| ANOVA de 2 fatores / modelo linear geral | ✅ / 🔵 | 2 fatores com ou sem interação (SQ ajustadas, validada contra o guia); modelo linear geral 🔵 |
| Modelos mistos, MANOVA | ⚪ | |

## Qualidade (Cartas de controle, capacidade, medição, ferramentas)

| Item do Minitab | Situação | Observação |
|---|---|---|
| Gráfico de Pareto | ✅ F2 | |
| Diagrama de causa e efeito | 🔵 | |
| Cartas de controle de variáveis (Xbarra-S, I-AM, etc.) | 🔵 | Getting Started, cap. 4; grande |
| Cartas de atributos (P, NP, C, U) | 🔵 | |
| Cartas EWMA, CUSUM, multivariadas, eventos raros | ⚪ | |
| Análise de capacidade (normal, não normal) | 🔵 | Getting Started, cap. 4 |
| Process Capability Sixpack, intervalos de tolerância | ⚪ | |
| Estudos de medição (R&R cruzado/aninhado, EMP, atributos) | ⚪ | grande; fora do escopo didático |
| Amostragem de aceitação, curvas OC | ⚪ | |
| Análise de sobrevivência e confiabilidade (Weibull, censura) | ⚪ | |

## Planejamento de experimentos (DOE)

| Item do Minitab | Situação | Observação |
|---|---|---|
| Experimento fatorial de 2 níveis (criar, analisar, Pareto, efeitos) | 🔵 | Getting Started, cap. 5 — exemplo completo no guia |
| Gráficos de efeitos principais e de interação | ✅ | na ANOVA de 2 fatores; criar o experimento ainda é 🔵 |
| Plackett-Burman, triagem, superfície de resposta, mistura, Taguchi | ⚪ | |

## Séries temporais

| Item do Minitab | Situação | Observação |
|---|---|---|
| Gráfico de série temporal | ✅ F2 | |
| Média móvel, suavização exponencial, decomposição | 🔵 | |
| Autocorrelação (ACF/PACF), ARIMA, Dickey-Fuller | ⚪ | |

## Multivariado e aprendizado de máquina

| Item do Minitab | Situação | Observação |
|---|---|---|
| Análise de componentes principais, fatorial, discriminante, conglomerados | ⚪ | |
| CART, Random Forests, TreeNet, MARS, aprendizado de máquina automatizado | ⚪ | a brochure destaca, mas não é a disciplina |

## Ferramentas próprias do statlab

| Item | Situação | Observação |
|---|---|---|
| Assistente "Qual teste usar?" | ✅ | menu Assistente: responde perguntas e **indica o comando e as opções**; não analisa nada |
| Janela de sessão | ✅ | a saída de cada comando acumula, como no Minitab |
| Exportar a sessão (HTML/Markdown) | ✅ | HTML com gráficos, sem CDN |
| Conclusões redigidas em pt-BR | ⚪ | **removido no pivô**: interpretar é do usuário (está na branch `main`) |
| Gerador de listas com gabarito (prática) | ⚪ | **removido no pivô**: dependia da escolha automática do teste (está na branch `main`) |
| Poder e tamanho de amostra | 🔵 | |

## Ferramentas gerais (brochure e guia)

| Item | Situação | Observação |
|---|---|---|
| Interface em português (pt-BR) com formatação brasileira | ✅ | vírgula decimal, `p < 0,001` |
| Ajuda contextual / Quick Start | 🔵 | a página de ajuda vem depois das telas da F3 |
| Macros, scripts, integração R/Python | ⚪ | a integração do statlab é o próprio código Python |
| Execução de comandos de sessão (repetir análise) | 🔵 | equivalente: a página de descritivas com parâmetros; `exec` seria novo |

## Decisões tomadas

1. **Exportação:** só HTML interativo (16/11/2026). PNG pelo botão de câmera do Plotly no navegador.
2. **Ordem do backlog:** F3 (telas dos testes) → testes simples que faltavam (Z, t e proporção de uma amostra,
   qui-quadrado) → regressão múltipla e ANOVA de 2 fatores → F4/F5 → DOE e cartas de controle sob demanda.
3. **Andamento (16/11/2026):** F3 concluída junto com os testes simples (t, Z e proporção de uma amostra,
   qui-quadrado). Próximo: regressão múltipla e ANOVA de 2 fatores; depois F4 e F5.
4. **Andamento (16/11/2026):** regressão múltipla e ANOVA de 2 fatores concluídas (validadas contra a saída do
   Minitab no exemplo do cap. 5 do guia). Próximo: F4 (assistente) e F5 (conclusões e relatório).
5. **Andamento (16/11/2026):** F4 concluída (assistente). Próximo: F5 (conclusões e relatório).
6. **Andamento (16/11/2026):** F5 concluída (conclusões e relatório). Próximo: F6 (prática com o gerador de listas).
7. **Andamento (16/11/2026):** F6 concluída. Todas as fases do plano original estão prontas; o backlog 🔵 acima continua disponível.
8. **Pivô para o modelo Minitab (17/11/2026):** o app deixou de decidir pelo usuário. A troca automática de
   teste, a exclusão automática de outliers, a análise "com e sem" suaves, o Tukey obrigatório, a trava da
   regressão e as conclusões redigidas saíram; cada escolha virou opção de diálogo ou comando próprio. A
   interface passou a ser menus + janela de sessão. O app guiado anterior está na branch `main`, e o modo
   manual (F7) na `f7-modo-manual`.
