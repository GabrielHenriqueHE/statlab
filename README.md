# statlab

Ferramenta de análise estatística didática, em português, para a disciplina de Probabilidade e Estatística. Para cada análise ela:

1. verifica os **pré-requisitos** (outliers, normalidade, igualdade de variâncias) com cards ✓/✗;
2. escolhe o **teste** adequado (paramétrico ou não paramétrico) e explica a escolha;
3. mostra o **cálculo passo a passo**;
4. redige a **conclusão** no padrão da apostila, com nível de confiança e intervalo.

> **Status:** F0 (setup) e F1 (núcleo estatístico com testes de aceitação) concluídas. Próximas: F2 UI de dados → F3 páginas dos testes → F4 assistente "Qual teste usar?" → F5 conclusões e relatório → F6 prática com o gerador.

## Instalação

Requer Python 3.13 e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Uso

```bash
uv run statlab                              # mensagem de status do pacote (temporário)
uv run pytest                               # testes
uv run ruff check .                         # lint
uv run streamlit run src/statlab/ui/app.py  # app (a partir da F2)
```

## Estrutura

```
src/statlab/
  core/        cálculos estatísticos puros (sem Streamlit)
  ui/          páginas Streamlit (só exibição)
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
