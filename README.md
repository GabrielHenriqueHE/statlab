# statlab

Ferramenta de análise estatística em português, no modelo do Minitab: **você escolhe o comando e as
opções, o app calcula exatamente aquilo e reporta.**

- **menus e janela de sessão** — Dados, Estat, Gráfico e Assistente numa barra de menus nativa; a
  saída de cada comando se acumula em abas na janela de sessão (em cima) e a worksheet fica na grade
  (embaixo), com divisor arrastável; a sessão é exportável em HTML ou Markdown;
- **opções explícitas** — assumir variâncias iguais, Tukey, método da correlação, z ou Fisher, nível
  de confiança, excluir outliers extremos (desmarcado por padrão);
- **diagnósticos, não decisões** — normalidade, outliers e critérios como n·p·q ≥ 5 aparecem com
  ✅/⚠️/❌ junto da saída: informam, mas nunca trocam o teste nem alteram os dados;
- **cálculo passo a passo** de cada comando, no vocabulário da apostila.

O app não escolhe o teste, não exclui dados e não redige a conclusão — interpretar é de quem analisa.
Quem quiser orientação usa o menu **Assistente**, que pergunta e indica qual comando abrir.

> **Status:** 44 comandos nos menus Dados, Estat, Gráfico, Assistente e Ajuda — descritivas,
> normalidade (Anderson-Darling, Ryan-Joiner e Shapiro-Wilk), t de 1 e 2 amostras e pareado, não paramétricos
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
uv run statlab         # abre a janela do app
uv run pytest          # testes
uv run ruff check .    # lint
```

## Estrutura

```
src/statlab/
  core/        cálculos estatísticos puros (sem interface)
  graficos/    gráficos Plotly (sem interface) e exportação HTML
  ui/          app Qt (PySide6): barra de menus, janela de sessão, grade da worksheet
               e um diálogo por comando (só exibição; a regra estatística fica no core)
  relatorio/   a saída da sessão e a exportação HTML/Markdown
tests/         testes de aceitação e unitários
docs/reference/  material da disciplina (apostila revisada, gerador, gabarito 2026)
```

## Referências de método

- Apostila "Análise Estatística e Testes de Hipótese" (versão revisada, 2026), em `docs/reference/`.
- Quartis pelo método do Excel (`QUARTIL.INC`, equivalente a `numpy.percentile(method="linear")`). O Minitab usa outro método (`weibull`); a diferença pode alterar a classificação de outliers.
- Normalidade: o usuário escolhe o teste no comando — Anderson-Darling (padrão do Minitab), **Ryan-Joiner** (do Minitab) ou Shapiro-Wilk (apostila). O p do Ryan-Joiner vem da tabela da apostila (fórmula e fatores de correção de Ryan & Joiner, 1976), que cobre α de 0,01 a 0,10 e exige n ≥ 9. Em n pequeno o p tende a rejeitar mais do que α mesmo com dados normais (medido por simulação; a saída traz um aviso para n < 25). Cada teste de normalidade vem com o gráfico de probabilidade normal, com a estatística do método escolhido.

## Docker

> **Desatualizado:** o `Dockerfile` servia o app Streamlit em `http://localhost:8501`. Depois da
> troca para Qt o statlab é um app de desktop — rodar em contêiner exige expor o servidor gráfico
> (X11/Wayland), o que ainda não está configurado aqui. Use `uv run statlab` na máquina.

A imagem usa Python 3.13 e o uv 0.13.6 (versões fixas), instala só as dependências de produção a partir do `uv.lock` e tem *health check* em `/_stcore/health`.
