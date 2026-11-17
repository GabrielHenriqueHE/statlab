# statlab

Ferramenta de análise estatística didática, em português, para a disciplina de Probabilidade e Estatística. Para cada análise ela:

1. verifica os **pré-requisitos** (outliers, normalidade, igualdade de variâncias) com cards ✓/✗;
2. escolhe o **teste** adequado (paramétrico ou não paramétrico) e explica a escolha;
3. mostra o **cálculo passo a passo**;
4. redige a **conclusão** no padrão da apostila, com nível de confiança e intervalo.

> **Status:** F0 a F6 concluídas: núcleo estatístico, dados, descritivas, gráficos e as telas de todos os testes (normalidade, uma amostra, dois grupos, pareado, ANOVA, proporções, qui-quadrado, correlação e regressão, regressão múltipla, ANOVA de dois fatores), com cartões ✅/⚠️/❌ de pré-requisitos e α configurável. Inclui o assistente "Qual teste usar?" (F4), conclusões no padrão da apostila e relatório em HTML/Markdown (F5). A página Prática gera listas com o gerador da disciplina, com gabarito e conferência pelo statlab (F6). O comparativo com o Minitab está em [docs/funcionalidades_minitab.md](docs/funcionalidades_minitab.md).

## Instalação

Requer Python 3.13 e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Uso

```bash
uv run statlab                              # abre o app no navegador
uv run pytest                               # testes
uv run ruff check .                         # lint
uv run streamlit run src/statlab/ui/app.py  # mesmo app, com opções do Streamlit
```

## Estrutura

```
src/statlab/
  core/        cálculos estatísticos puros (sem Streamlit)
  graficos/    gráficos Plotly (sem Streamlit) e exportação HTML
  ui/          app Streamlit e páginas (só exibição; a regra estatística fica no core)
  relatorio/   exportação HTML/Markdown
tests/         testes de aceitação e unitários
docs/reference/  material da disciplina (apostila revisada, gerador, gabarito 2026)
```

## Referências de método

- Apostila "Análise Estatística e Testes de Hipótese" (versão revisada, 2026), em `docs/reference/`.
- `docs/reference/gerador_exercicios.py` — gerador de listas com gabarito (semente 2026). Usado como referência de regras e como teste de regressão.
- Quartis pelo método do Excel (`QUARTIL.INC`, equivalente a `numpy.percentile(method="linear")`). Minitab usa outro método (`weibull`); a diferença pode alterar a classificação de outliers e deve ser citada nas conclusões.

## Docker (esboço)

```bash
docker build -t statlab .
docker run -p 8501:8501 statlab
```
