"""Página Como usar: roteiro do app e as regras de decisão da disciplina (só texto; nenhuma regra é calculada aqui)."""

import streamlit as st

st.header("Como usar o statlab")
st.caption("Roteiro rápido e resumo das regras da apostila que o app aplica automaticamente.")

st.subheader("Roteiro")
st.markdown(
    """
1. **Dados** — importe um CSV/Excel (escolha a aba e o intervalo, como no Minitab) ou cole do Excel. Cada
   conjunto vira uma *worksheet*; a ativa é escolhida na barra lateral. Em **Empilhar / desempilhar** você
   troca entre "uma coluna por grupo" e "resposta + coluna de grupo"; em **Recodificar**, troca códigos por
   rótulos (ou o contrário).
2. **Estatísticas descritivas** e **Gráficos** — conheça os dados antes de testar: média, mediana, quartis,
   boxplot (outliers), histograma e gráfico de probabilidade normal.
3. **Qual teste usar?** — responda às perguntas (objetivo, tipo de variável, pareamento, número de grupos). O
   assistente segue a árvore da Tabela 2 da apostila, verifica os pré-requisitos e explica o caminho.
4. **Página do teste** — confira os cartões de pré-requisitos, o resultado, a conclusão redigida e o cálculo
   passo a passo. Use **Adicionar ao relatório** para guardar.
5. **Relatório** — exporte tudo em HTML (com gráficos interativos) ou Markdown.
6. **Prática** — gere listas com o gerador da disciplina e confira suas respostas.
"""
)

st.subheader("Cartões de pré-requisitos")
st.markdown(
    """
| Cartão | Significado |
|---|---|
| ✅ | Pré-requisito atendido. |
| ⚠️ | Atendido com ressalva: outlier suave (análise com e sem), normalidade só pelo TCL (n ≥ 30), Welch. |
| ❌ | Violado: o app troca para o teste não paramétrico (ou avisa que o resultado não é confiável). |
"""
)

st.subheader("Regras de decisão (apostila)")
st.markdown(
    """
- **Significância**: α = 0,05 por padrão (0,01 na barra lateral). p ≤ 0,01 → 99% de confiança;
  p ≤ 0,05 → 95%; acima de α → não significativo. "Não significativo" **não prova** H₀: nunca conclua que
  "as médias são iguais".
- **Outliers** (diagrama de caixa, D = Q3 − Q1): fora de [Q1 − 1,5D; Q3 + 1,5D] é **suave** (a análise é feita
  com e sem ele); fora de [Q1 − 3D; Q3 + 3D] é **extremo** (excluído, com aviso do n antes e depois).
- **Normalidade**: Shapiro-Wilk; p > α → normal. Não normal com n ≥ 30 → requisito atendido pelo TCL (t e
  ANOVA). Na **correlação** não há esse atalho: não normal → Spearman.
- **Dois grupos independentes**: teste F decide entre t com variância combinada e t de Welch; algum grupo não
  normal com n < 30 → Mann-Whitney.
- **Antes × depois**: normalidade das **diferenças**; não normal com n < 30 → Wilcoxon.
- **Três ou mais grupos**: ANOVA se todos normais (ou n ≥ 30) e maior/menor variância ≤ 9; senão
  Kruskal-Wallis. Significativo → Tukey (ANOVA) ou Mann-Whitney com Bonferroni (Kruskal-Wallis).
- **Duas proporções**: n·p·q ≥ 5 em cada grupo → z; senão Fisher exato.
- **Correlação**: Pearson se x e y normais, senão Spearman; força e r² só se significativa. **Regressão** só
  com correlação significativa, e sem extrapolar além da faixa observada de x.
- **Unilateral** só se a direção foi definida **antes** de coletar os dados.
"""
)

st.subheader("Testes fora da apostila")
st.markdown(
    """
Implementados com os critérios de livros e do Minitab, e marcados com aviso na tela: testes de uma amostra
(t, Z, sinal, proporção), variâncias (χ², Bartlett, Levene), qui-quadrado, post hoc do Kruskal-Wallis,
regressão múltipla, ANOVA de dois fatores e Anderson-Darling. Confirme com o professor antes de usá-los numa
avaliação.
"""
)

st.subheader("Diferenças em relação ao Minitab")
st.markdown(
    """
- **Quartis**: o app usa o método do Excel (QUARTIL.INC), como a apostila; o Minitab usa outro, e a diferença
  pode mudar quem é outlier.
- **Normalidade**: o app decide pelo Shapiro-Wilk (apostila); o Minitab usa Anderson-Darling por padrão (também
  mostrado). O Ryan-Joiner do Minitab não foi implementado; é um teste semelhante ao Shapiro-Wilk (correlação dos dados
  com os escores normais).
- **Formato dos números**: vírgula decimal e ponto de milhar (1.452,78); p menor que 0,001 aparece como "< 0,001".
"""
)
