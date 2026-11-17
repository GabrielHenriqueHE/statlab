# statlab — instruções para o Claude

App de análise estatística didática em pt-BR (disciplina Probabilidade e Estatística). Núcleo estatístico puro e testado + UI Streamlit. **Correção estatística vem antes de tudo.**

## Estrutura
- `src/statlab/core/` — cálculos puros. **Proibido importar `streamlit`** aqui. Cada função devolve um dataclass de `resultados.py` com estatística, gl, p, IC, n, `avisos`, `passos` (cálculo) e `verificacoes` (pré-requisitos estruturados: `OK` ✅, `ATENCAO` ⚠️, `FALHA` ❌ — a UI desenha os cartões só a partir delas, nunca lendo texto).
- `src/statlab/ui/` — app Streamlit (`app.py`) e páginas em `ui/paginas/` (Dados, Estatísticas descritivas, Gráficos). Só formatam e exibem; nenhuma regra estatística mora aqui. Estado da sessão em `ui/estado.py` (worksheets como no Minitab).
- `src/statlab/graficos/` — figuras Plotly puras (sem Streamlit) e exportação (`exportar.py`): **somente HTML interativo**, por decisão do usuário (sem Kaleido/Chrome).
- `core/importacao.py` (CSV/XLSX/texto colado) e `core/tabela.py` (empilhar, desempilhar, pares completos) — entrada de dados, sem regras estatísticas.
- `core/uma_amostra.py` (t/Wilcoxon, Z, uma proporção) e `core/qui_quadrado.py` (independência, aderência) — fora da apostila; avisam isso. IC exibido é sempre o bilateral de 95%, mesmo com H₁ unilateral.
- `core/regressao_multipla.py` e `core/anova_dois_fatores.py` — fora da apostila; aceitação contra o exemplo fatorial do guia do Minitab (`tests/fixtures/minitab_exemplos.json`). ANOVA de 2 fatores usa SQ ajustadas (tipo III, soma zero), como o Minitab.
- `core/assistente.py` — F4: árvore da Tabela 2 (`decidir`) e análise com explicação do caminho (`analisar` + `caminho`). Testado com os casos da apostila e do gabarito (cada um chega ao teste que o material escolheu).
- `core/conclusoes.py` — F5: `concluir(res, variavel=...)` escreve a conclusão no padrão da seção 10 da apostila (texto conferido contra os exemplos resolvidos). Nunca afirmar H₀ ("as médias são iguais").
- `relatorio/relatorio.py` — itens do relatório (análise, pré-requisitos, resultado, conclusão, avisos, cálculo, gráficos) e exportação Markdown/HTML (HTML autocontido, sem CDN).
- `pratica/` — F6: `gerador.py` é cópia de `docs/reference/gerador_exercicios.py` com mudanças mínimas (registra `extra["teste"]`, `extra["brutos"]`, `extra["alternativa"]`; o sorteio é idêntico). `conferir` compara a escolha do gerador com a do statlab; testes garantem concordância (semente 2026 e outras).
- `ui/componentes.py` — peças comuns das páginas de teste (hipótese alternativa, cartões, resultado, cálculo, escolha de grupos em colunas ou empilhados). α global em `estado.alpha()` (barra lateral: 0,05 ou 0,01).
- `src/statlab/relatorio/` — exportação HTML/Markdown (fase F5).
- `tests/` — pytest. `tests/fixtures/` — dados de referência.
- `docs/reference/` — material da disciplina (PDF revisado, gerador, gabarito 2026). Fonte de verdade para regras e valores.

## Comandos
- Instalar: `uv sync`
- Testes: `uv run pytest`
- Lint: `uv run ruff check .` (formatar: `uv run ruff format .`)
- App: `uv run statlab` (ou `uv run streamlit run src/statlab/ui/app.py`)

## Regras estatísticas (implementar exatamente)
1. **α** = 0,05 padrão; opção 0,01 na sidebar. Regra de decisão: p ≤ 0,01 → 99%; p ≤ 0,05 → 95%; senão "não significativo".
2. **Outliers** (diagrama de caixa): D = Q3 − Q1. Suave: fora de [Q1 − 1,5D; Q3 + 1,5D] → rodar com e sem. Extremo: fora de [Q1 − 3D; Q3 + 3D] → excluir, com aviso de n antes/depois. Quartis: `numpy.percentile(method="linear")` (= Excel QUARTIL.INC). Opção `method="weibull"` (= Minitab) só se o usuário escolher.
3. **Normalidade**: Shapiro-Wilk. p > α → normal. Se p ≤ α e n ≥ 30 → "requisito atendido pelo TCL" para t e ANOVA. **Exceção:** na correlação não há o atalho n ≥ 30 — se não normal, usar Spearman.
4. **t pareado**: exige normalidade das **diferenças** (não de cada coluna). Sem igualdade de variâncias. Não normal com n < 30 → Wilcoxon.
5. **t independente**: teste F (razão de variâncias, gl = n1−1, n2−1) e Levene (center=median) como conferência. Variâncias iguais (p_F > α) → t com variância combinada; senão Welch. Não normal com n < 30 em algum grupo → Mann-Whitney.
6. **ANOVA (1 fator)**: exige normalidade por grupo (ou n ≥ 30) e razão maior/menor variância ≤ 9 (critério da disciplina). Falhou → Kruskal-Wallis. ANOVA significativa (p ≤ α) ⇒ **Tukey HSD** obrigatório. Kruskal significativo ⇒ Mann-Whitney 2 a 2 com **Bonferroni** (p × k(k−1)/2) — aviso: fora da apostila. Welch só como conferência.
7. **Proporções** (2 grupos): checar n·p·q ≥ 5 (critério da apostila) e também n·p ≥ 5 e n·q ≥ 5 (critério "muitos livros") — se qualquer falhar → **Fisher exato**. Caso contrário, z com EP pooled; Fisher como conferência.
8. **Unilateral** só se a direção foi definida antes da coleta (informado pelo usuário). Se a diferença observada for na direção oposta → p_unilateral = 1 − p/2 (não significativo). Padrão: bilateral.
9. **Correlação**: Pearson se x e y normais (Shapiro), senão Spearman. Significância por t = r·√(n−2)/√(1−r²), gl = n−2; valor crítico da tabela A.6 (= t_crit/√(t_crit²+n−2)). **Tabela A.6 correta: n=4, α=0,01 → 0,990** (a imagem traz 0,999; não usar). Classificar força (|r|: <0,2 bem fraca; <0,4 fraca; <0,7 moderada; <0,9 forte; ≥0,9 muito forte) **só** se significativo. r² sempre que r for significativo.
10. **Regressão** (y = a·x + b; a = (n·Σxy − Σx·Σy)/(n·Σx² − (Σx)²); b = ȳ − a·x̄): só se a correlação for significativa (permitir forçar com aviso). Sempre avisar extrapolação se x fora da faixa observada.
11. **Outlier suave em correlação/regressão**: rodar com e sem; se a conclusão mudar, dizer explicitamente.
12. Pares com dados faltantes: usar só pares completos e avisar n efetivo.

## Redação das conclusões (padrão da apostila, seção 10)
- Significativo: "… apresentou média significativamente maior/menor … (p = …), com 95/99% de confiança. Espera-se uma diferença entre [IC inf] e [IC sup] com 95% de confiança."
- Não significativo: "Não há diferença significativa …" / "Não há evidência de …" — **nunca** "as médias são iguais" ou "não há correlação" como prova.
- Não paramétrico: citar o teste e as **medianas**, não médias.
- Correlação: "… (r = …; p = …) … r² = …% da variação … explicada …".
- Sempre informar qual teste foi usado e por quê (pré-requisitos).

## Formatação pt-BR
Vírgula decimal, ponto de milhar (`1.452,78`); p: `p < 0,001` ou `p = 0,047`; nunca mostrar `nan`/`inf` sem explicação.

## Robustez
- A análise "sem outliers suaves" é complementar: se não puder ser calculada (ex.: variável fica constante), vira aviso — nunca derruba a análise principal (bug encontrado na F6, semente 11 do gerador).
- Dados ruins (coluna constante, n < 3, faltantes, grupo vazio, texto em coluna numérica) devolvem erro de domínio legível (`ErroDeDados` em `core/`), nunca traceback na UI.
- Divergência entre o código e os valores do PDF/gabarito ⇒ **parar e reportar**. Nunca ajustar o teste para bater com um número.

## Dependências
Base: numpy, scipy, pandas, statsmodels, streamlit, plotly, openpyxl. Dev: pytest, ruff. Nada além disso sem perguntar ao usuário.
Antes de usar uma API nova, confirmar que existe na versão instalada.

## Git
Não commitar sem pedido explícito do usuário. Mensagens de commit terminam com as linhas de atribuição pedidas pelo harness (Co-Authored-By e Claude-Session).

## Dados de referência e divergências conhecidas (F1)
- **Tabela A.6**: a fórmula `r = t/√(t² + n − 2)` é a referência. Sete entradas impressas no livro diferem da fórmula
  além do arredondamento (até 0,0021, em n = 45, α = 0,01). O próprio PDF admite diferenças "de até cerca de 0,002".
  As divergências estão em `DIVERGENCIAS_LIVRO_A6` (tests/test_descritiva_correlacao.py). Não ajustar o código para o livro.
- **`dados_2026.xlsx`**: a aba Ex5 (Turma tarde) já está **sem** os extremos 37 e 38, e a aba Ex10 está **sem** o par (58; 100)
  (diferença −42, outlier extremo). O gabarito é consistente com a planilha. O enunciado bruto está em
  `tests/fixtures/gabarito_2026.json` (`enunciado_bruto`).
- **Exemplo gráfico (atendimento × produtividade)**: 46 tempos, 40 produtividades. A normalidade do PDF (tempo p = 0,015)
  é calculada sobre os **40 pares**, não sobre os 46 tempos (com 46, p = 0,0046).
- **Quartis**: `linear` (Excel QUARTIL.INC). Os valores do PDF (ex. produtividade Q1 = 7116,5; Q3 = 9867,25) conferem.
- **Fixtures** (`tests/fixtures/*.json`) são cópias das planilhas de `docs/reference/`. Regerar a partir de lá se as planilhas mudarem.

## Anderson-Darling e Minitab (F2)
- O teste de normalidade padrão do Minitab é Anderson-Darling. `p_anderson_darling` usa a aproximação de Stephens (D'Agostino & Stephens, 1986), validada contra `statsmodels.normal_ad` e contra o relatório da brochure (A² ≈ 0,2524, n = 50, p ≈ 0,724).
- Assimetria e curtose são as ajustadas (G1, G2) do Minitab.
- Exportação: decidido **só HTML** (16/11/2026). PNG fica pelo botão de câmera do próprio Plotly no navegador.
