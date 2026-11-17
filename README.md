# statlab

Ferramenta de análise estatística em português, no modelo do Minitab: **você escolhe o comando e as
opções, o app calcula exatamente aquilo e reporta.**

- **menus e janela de sessão** — Dados, Estat, Gráfico e Assistente; a worksheet fica à esquerda e a
  saída de cada comando se acumula à direita, exportável em HTML ou Markdown;
- **opções explícitas** — assumir variâncias iguais, Tukey, método da correlação, z ou Fisher, nível
  de confiança, excluir outliers extremos (desmarcado por padrão);
- **diagnósticos, não decisões** — normalidade, outliers e critérios como n·p·q ≥ 5 aparecem com
  ✅/⚠️/❌ junto da saída: informam, mas nunca trocam o teste nem alteram os dados;
- **cálculo passo a passo** de cada comando, no vocabulário da apostila.

O app não escolhe o teste, não exclui dados e não redige a conclusão — interpretar é de quem analisa.
Quem quiser orientação usa o menu **Assistente**, que pergunta e indica qual comando abrir.

> **Status:** 44 comandos nos menus Dados, Estat, Gráfico, Assistente e Ajuda — descritivas,
> normalidade (Shapiro-Wilk e Anderson-Darling), t de 1 e 2 amostras e pareado, não paramétricos
> (Mann-Whitney, Wilcoxon, Kruskal-Wallis, sinal), variâncias (F, Bartlett, Levene), ANOVA de um e
> dois fatores, proporções, qui-quadrado, correlação, regressão simples e múltipla, e 11 gráficos.
> Os valores são validados contra os exemplos resolvidos da apostila, o gabarito 2026 e a saída do
> Minitab (cap. 5 do guia). O comparativo item a item está em
> [docs/funcionalidades_minitab.md](docs/funcionalidades_minitab.md).
>
> Este é o **pivô** para o modelo Minitab (branch `pivot/minitab`). O app guiado original, que
> escolhia o teste e redigia a conclusão, está na branch `main`; o modo manual passo a passo, na
> `f7-modo-manual`.

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
  ui/          app Streamlit: menu, janela de sessão e um diálogo por comando
               (só exibição; a regra estatística fica no core)
  relatorio/   a saída da sessão e a exportação HTML/Markdown
tests/         testes de aceitação e unitários
docs/reference/  material da disciplina (apostila revisada, gerador, gabarito 2026)
```

## Referências de método

- Apostila "Análise Estatística e Testes de Hipótese" (versão revisada, 2026), em `docs/reference/`.
- Quartis pelo método do Excel (`QUARTIL.INC`, equivalente a `numpy.percentile(method="linear")`). O Minitab usa outro método (`weibull`); a diferença pode alterar a classificação de outliers.
- Normalidade: a decisão usa o Shapiro-Wilk (apostila); o Anderson-Darling (padrão do Minitab) aparece como conferência. O **Ryan-Joiner** do Minitab **não foi implementado**: é semelhante ao Shapiro-Wilk (correlação entre os dados ordenados e os escores normais), mas o cálculo do p depende de aproximações tabeladas de Ryan & Joiner (1976) que não temos como conferir contra uma referência verificável. Quem precisar do mesmo resultado do Minitab deve usar lá o Ryan-Joiner; aqui, o Shapiro-Wilk leva à mesma decisão na grande maioria dos casos.

## Docker

```bash
docker build -t statlab .
docker run --rm -p 8501:8501 statlab   # abra http://localhost:8501
```

A imagem usa Python 3.13 e o uv 0.13.6 (versões fixas), instala só as dependências de produção a partir do `uv.lock` e tem *health check* em `/_stcore/health`.
