# statlab — instruções para o Claude

Ferramenta de análise estatística em pt-BR, no modelo do Minitab: **o usuário escolhe o comando e as
opções; o app calcula exatamente aquilo e reporta.** Núcleo estatístico puro e testado + UI em Qt
(PySide6).
**Correção estatística vem antes de tudo.**

## A regra que manda em todas as outras

**O app nunca decide pelo usuário.** Nenhuma função, comando ou tela pode:

- trocar o teste escolhido por outro (nem "porque os pré-requisitos falharam");
- excluir, filtrar ou transformar dados sem o usuário ter pedido na opção do diálogo;
- rodar análises alternativas "de conferência" por conta própria;
- encadear um pós-teste (Tukey, Bonferroni) por causa do resultado;
- bloquear um cálculo por julgar que não deveria ser feito;
- redigir a conclusão da análise.

O app **informa**: pré-requisitos são diagnósticos exibidos na saída (e comandos próprios), e notas
factuais (n descartado por faltantes, extrapolação, "fora da apostila") continuam aparecendo. Se a
escolha do usuário for estatisticamente discutível, o app calcula o que foi pedido e anota o fato —
não corrige nem recusa.

Quem quiser orientação usa o menu **Assistente**, que faz perguntas e **indica qual comando abrir**,
sem analisar nada.

## Estrutura
- `src/statlab/core/` — cálculos puros. **Proibido importar `PySide6`** (ou qualquer coisa de `ui/`)
  aqui; o mesmo vale para `relatorio/` e `graficos/` (há teste de guarda em `tests/test_pacote.py`).
  Cada função roda **um** teste com as opções recebidas e devolve um dataclass de `resultados.py`
  (estatística, gl, p, IC, n, `passos`, `avisos`, `verificacoes`). Funções que escolhem o teste ou
  mexem nos dados não existem mais — veja a regra acima.
- `core/resultados.py` — `Resultado` e subclasses. `verificacoes` (`OK` ✅, `ATENCAO` ⚠️, `FALHA` ❌)
  é **diagnóstico informativo**, nunca gatilho de decisão; a UI desenha os cartões só a partir delas,
  nunca lendo texto. `nome` é o comando que o usuário rodou.
- `relatorio/relatorio.py` — o registro da saída da sessão: `ItemRelatorio` é um bloco (título,
  tabelas, linhas de resultado, diagnósticos, notas, cálculo, figuras) e `item_de` monta um a partir
  de um `Resultado`. Também exporta a sessão em Markdown e HTML (autocontido, sem CDN). Puro.
- `src/statlab/ui/` — app Qt (PySide6). `app.py` é a `JanelaPrincipal` (menu + `QSplitter` com a
  janela de sessão em cima e as worksheets embaixo); `ui/menu.py` monta o `QMenuBar` (um submenu por
  grupo); `ui/sessao.py` desenha as abas da sessão (figuras num `QWebEngineView` com cópia local do
  `plotly.min.js`, sem CDN); `ui/worksheet.py` + `ui/grade.py` são a grade (um `QAbstractTableModel`
  sobre o `DataFrame`); `ui/comandos/` tem um módulo por comando. Nenhuma regra estatística aqui.
  Estado em `ui/estado.py`: `Estado(QObject)` com Signals, exposto pelas mesmas funções de módulo
  (`planilhas()`, `ativa()`, `registrar()`, …) — os comandos não sabem que existe um `QObject`.
- `ui/comandos/formulario.py` — o shim que dá aos comandos o mesmo modelo de rerun de antes: cada
  widget é identificado pela `key=`, o valor escolhido fica guardado por `key`, e mexer numa opção
  reconstrói a área do diálogo chamando o corpo do comando de novo. Os comandos o importam como
  `st`, então as chamadas (`st.selectbox`, `st.radio`, …) não mudaram. `_base.py` tem o
  `DialogoComando` (área redesenhável + botões fixos) e os helpers de sempre.
- `src/statlab/graficos/` — figuras Plotly puras (sem interface) e exportação (`exportar.py`):
  **somente HTML interativo**, por decisão do usuário (sem Kaleido/Chrome).
- `core/importacao.py` (CSV/XLSX/texto colado) e `core/tabela.py` (empilhar, desempilhar, recodificar,
  pares completos) — entrada e arrumação de dados, sem regras estatísticas.
- `core/assistente.py` — só a árvore de perguntas (`decidir`), que devolve **o comando e as opções a
  marcar**. Não toca nos dados e não roda análise.
- `tests/` — pytest. `tests/fixtures/` — dados de referência.
- `docs/reference/` — material da disciplina (PDF revisado, gabarito 2026) e os guias do Minitab.
  Fonte de verdade para valores. `docs/funcionalidades_minitab.md` é o mapa de menus.

## Comandos
- Instalar: `uv sync`
- Testes: `uv run pytest`
- Lint: `uv run ruff check .` (formatar: `uv run ruff format .`)
- App: `uv run statlab` (abre a janela Qt; os testes rodam com `QT_QPA_PLATFORM=offscreen`, ver
  `tests/conftest.py`)

## O que cada comando calcula (implementar exatamente)

Nível de confiança é **opção de cada diálogo** (padrão 95%), não um ajuste global. A regra de
decisão continua sendo reportada: p ≤ 0,01 → 99%; p ≤ 0,05 → 95%; acima de α → não significativo.
Unilateral é escolha do usuário no diálogo; se a diferença observada for na direção oposta,
p = 1 − p/2 (não significativo). Padrão bilateral.

1. **Descritivas**: N, N*, média, EP da média, DP, variância, mínimo, Q1, mediana, Q3, máximo,
   assimetria e curtose ajustadas (G1, G2, como o Minitab) e IC da média. Quartis:
   `numpy.percentile(method="linear")` (= Excel QUARTIL.INC); `method="weibull"` (= Minitab) é opção.
2. **Outliers** (diagrama de caixa): D = Q3 − Q1; suave fora de [Q1 − 1,5D; Q3 + 1,5D], extremo fora
   de [Q1 − 3D; Q3 + 3D]. É **diagnóstico**. Excluir é uma opção do diálogo que o comando aplica
   antes de chamar o núcleo, sempre reportando o n antes e depois.
3. **Normalidade**: Shapiro-Wilk ou Anderson-Darling (escolha do usuário; o padrão do Minitab é
   Anderson-Darling). Reportar estatística, p e n. **Não** aplicar o atalho do TCL (`tcl=False`): o
   n ≥ 30 é informação para o usuário decidir, não um requisito que o app considera atendido.
4. **t de uma amostra, t pareado, t de 2 amostras**: o de 2 amostras exige a opção explícita
   "assumir variâncias iguais" (variância combinada) ou não (Welch). O teste F e o Levene são
   **comandos próprios**, não pré-condição.
5. **Não paramétricos**: Wilcoxon (uma amostra e pareado), Mann-Whitney, Kruskal-Wallis e teste de
   sinal são comandos escolhidos pelo usuário, nunca substitutos automáticos.
6. **ANOVA de 1 fator**: tabela SQ/QM/F/p e R². Tukey e a conferência de Welch são **opções**
   marcáveis, não consequências de p ≤ α. Comparações 2 a 2 do Kruskal (Mann-Whitney com Bonferroni,
   p × k(k−1)/2) também são opção — com a nota de que estão fora da apostila.
7. **Variâncias**: teste F (razão, gl = n1−1, n2−1), Bartlett e Levene (center=median) como comandos
   distintos. Razão maior/menor variância é informação descritiva (o critério ≤ 9 da disciplina
   aparece como nota).
8. **Proporções**: z (EP combinado) e exato de Fisher são comandos distintos para 2 grupos; z e
   binomial exata, para uma proporção — note que o IC acompanha o método (normal vs Clopper-Pearson).
   Os critérios n·p·q ≥ 5 (apostila) e n·p ≥ 5, n·q ≥ 5 ("muitos livros") entram como nota.
9. **Correlação**: Pearson ou Spearman por escolha do usuário. Significância por
   t = r·√(n−2)/√(1−r²), gl = n−2; valor crítico da tabela A.6 (= t_crit/√(t_crit² + n − 2)).
   **Tabela A.6 correta: n = 4, α = 0,01 → 0,990** (a imagem traz 0,999; não usar). Força
   (|r|: <0,2 bem fraca; <0,4 fraca; <0,7 moderada; <0,9 forte; ≥0,9 muito forte) e r² são
   reportados sempre, com a nota de que só fazem sentido se r for significativo.
10. **Regressão**: sempre calculada, sem depender da correlação. Coeficientes com EP, t e p, S, R²,
    R²(aj), R²(pred), tabela ANOVA, resíduos e predição com IC e IP. Avisar extrapolação quando o x
    pedido está fora da faixa observada.
11. **Qui-quadrado**: independência (Pearson sem Yates, como o Minitab) e aderência; o exato de
    Fisher é comando próprio. O critério de Cochran (nenhum esperado < 1, no máximo 20% < 5) é nota.
12. Pares com dados faltantes: usar só pares completos e **reportar** o n efetivo.

## Saída da sessão
Cada comando acrescenta um bloco à janela de sessão, no formato do Minitab: título do comando, as
variáveis usadas, a tabela de resultados e as notas. Sem conclusão redigida — interpretar é do
usuário. A sessão é exportável em HTML (autocontido, com os gráficos) e Markdown.

## Formatação pt-BR
Vírgula decimal, ponto de milhar (`1.452,78`); p: `p < 0,001` ou `p = 0,047`; nunca mostrar
`nan`/`inf` sem explicação.

## Robustez
- Dados ruins (coluna constante, n < 3, faltantes, grupo vazio, texto em coluna numérica) devolvem
  erro de domínio legível (`ErroDeDados` em `core/`), nunca traceback na UI.
- Uma opção impossível para os dados dados (ex.: Tukey com 2 grupos) é recusada com mensagem clara —
  isso é validação de entrada, não o app decidindo a análise.
- Divergência entre o código e os valores do PDF/gabarito/Minitab ⇒ **parar e reportar**. Nunca
  ajustar o teste para bater com um número.

## Dependências
Base: numpy, scipy, pandas, statsmodels, PySide6, plotly, openpyxl. Dev: pytest, pytest-qt, ruff.
Nada além disso sem perguntar ao usuário. Antes de usar uma API nova, confirmar que existe na versão
instalada. O `QWebEngineView` (gráficos) vem do PySide6-Addons e embute um Chromium: precisa ser
importado **antes** da `QApplication` (é o que `sessao.preparar_webengine()` faz) e pode exigir libs
de sistema; sem ele, cada figura ganha um botão que abre o gráfico no navegador.

## Git
Não commitar sem pedido explícito do usuário. Mensagens de commit terminam com as linhas de
atribuição pedidas pelo harness (Co-Authored-By e Claude-Session).
O pivô para o modelo Minitab vive na branch `pivot/minitab` (worktree `../statlab-minitab`). A
`main` guarda o app guiado original e a `f7-modo-manual`, o modo manual — nenhuma das duas deve ser
alterada por este trabalho.

## Dados de referência e divergências conhecidas
- **Tabela A.6**: a fórmula `r = t/√(t² + n − 2)` é a referência. Sete entradas impressas no livro
  diferem da fórmula além do arredondamento (até 0,0021, em n = 45, α = 0,01). O próprio PDF admite
  diferenças "de até cerca de 0,002". As divergências estão em `DIVERGENCIAS_LIVRO_A6`
  (tests/test_descritiva_correlacao.py). Não ajustar o código para o livro.
- **`dados_2026.xlsx`**: a aba Ex5 (Turma tarde) já está **sem** os extremos 37 e 38, e a aba Ex10
  está **sem** o par (58; 100) (diferença −42, outlier extremo). O enunciado bruto está em
  `tests/fixtures/gabarito_2026.json` (`enunciado_bruto`) — é com ele que se testa que o app **não**
  exclui nada por conta própria.
- **Exemplo gráfico (atendimento × produtividade)**: 46 tempos, 40 produtividades. A normalidade do
  PDF (tempo p = 0,015) é calculada sobre os **40 pares**, não sobre os 46 tempos (com 46, p = 0,0046).
- **Quartis**: `linear` (Excel QUARTIL.INC). Os valores do PDF (ex. produtividade Q1 = 7116,5;
  Q3 = 9867,25) conferem.
- **Anderson-Darling**: `p_anderson_darling` usa a aproximação de Stephens (D'Agostino & Stephens,
  1986), validada contra `statsmodels.normal_ad` e contra a brochure (A² ≈ 0,2524, n = 50, p ≈ 0,724).
- **ANOVA de 2 fatores e regressão múltipla**: aceitação contra o exemplo fatorial do cap. 5 do guia
  do Minitab (`tests/fixtures/minitab_exemplos.json`). A de 2 fatores usa SQ ajustadas (tipo III,
  soma zero), como o Minitab. A regressão simples é a múltipla com um preditor.
- **Fixtures** (`tests/fixtures/*.json`) são cópias das planilhas de `docs/reference/`. Regerar a
  partir de lá se as planilhas mudarem.
- **Exportação**: decidido **só HTML** (16/11/2026). PNG pelo botão de câmera do próprio Plotly.
