"""Menus Assistente e Ajuda.

O Assistente responde "qual comando usar?" — ele indica, não analisa. Nenhum dado é lido aqui.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from statlab.core import assistente
from statlab.ui.comandos import _base as b

RESPOSTAS = {"Sim": True, "Não": False, "Não sei": None}


@b.comando("Assistente", "", "Qual teste usar?")
def qual_teste() -> None:
    st.caption(
        "Responda pelo que você já sabe dos dados. O assistente segue a Tabela 2 da apostila e indica o "
        "comando a abrir — ele não roda a análise nem olha a worksheet."
    )
    chaves = list(assistente.OBJETIVOS)
    objetivo = st.radio(
        "Qual é o objetivo?", chaves, format_func=lambda c: assistente.OBJETIVOS[c].descricao, key="as_obj"
    )

    def pergunta(rotulo: str, chave: str) -> bool | None:
        return RESPOSTAS[st.radio(rotulo, list(RESPOSTAS), index=2, key=chave, horizontal=True)]

    respostas: dict[str, object] = {}
    if objetivo == "relacao":
        respostas["normal"] = pergunta("x e y são normais (Shapiro-Wilk p > α)?", "as_normal")
    elif objetivo in ("dois_grupos", "pareado", "tres_grupos", "uma_amostra"):
        alvo = "As diferenças (1ª − 2ª)" if objetivo == "pareado" else "Os dados de cada grupo"
        respostas["normal"] = pergunta(f"{alvo} são normais (Shapiro-Wilk p > α)?", "as_normal")
        respostas["n_grande"] = st.checkbox("Todos os grupos têm n ≥ 30", key="as_n30")
        if objetivo == "dois_grupos":
            respostas["variancias_iguais"] = pergunta("As variâncias são iguais (teste F, p > α)?", "as_var")
        if objetivo == "tres_grupos":
            respostas["razao_ate_9"] = pergunta("A maior variância é até 9 vezes a menor?", "as_razao")
    elif objetivo == "proporcoes":
        respostas["npq_ok"] = pergunta("n·p·q ≥ 5 e n·p, n·q ≥ 5 em cada grupo?", "as_npq")
    else:
        respostas["esperados_ok"] = pergunta(
            "As contagens esperadas atendem ao critério (nenhuma < 1, ≤ 20% < 5)?", "as_esp"
        )
        respostas["tabela_2x2"] = st.checkbox("A tabela é 2 × 2", key="as_2x2")

    decisao = assistente.decidir(objetivo, **respostas)
    st.markdown("**Caminho**")
    for linha in decisao.caminho:
        st.markdown(f"- {linha}")
    if decisao.teste:
        st.success(f"Use **{decisao.teste}** — abra **{decisao.comando}**.")
    for pendencia in decisao.pendencias:
        st.info(pendencia)


@b.comando("Assistente", "", "Tabela de referência")
def tabela_referencia() -> None:
    objetivos = assistente.OBJETIVOS.values()
    st.dataframe(
        pd.DataFrame(
            {
                "Objetivo": [o.descricao for o in objetivos],
                "Paramétrico": [o.parametrico for o in objetivos],
                "Pré-requisitos": [o.prerequisitos for o in objetivos],
                "Não paramétrico": [o.nao_parametrico for o in objetivos],
                "Comando": [o.comando for o in objetivos],
            }
        ),
        hide_index=True,
        width="stretch",
    )


@b.comando("Ajuda", "", "Como usar")
def como_usar() -> None:
    st.markdown(
        """
**O statlab executa o que você pede.** Ele não escolhe o teste, não exclui dados e não escreve a
conclusão: essas decisões são suas. O que ele faz é calcular direito e reportar.

1. **Dados** — abra um CSV/Excel, cole do Excel ou edite a worksheet na tela. Empilhar, desempilhar,
   recodificar e filtrar também ficam aqui.
2. **Estat** e **Gráfico** — cada comando abre um diálogo com as opções (variáveis, nível de
   confiança, hipótese alternativa, Tukey, excluir outliers…). A saída vai para a janela de sessão,
   à direita, e fica acumulada.
3. **Assistente** — se você não sabe qual comando usar, ele pergunta e indica. Não analisa nada.

**Diagnósticos.** Normalidade, outliers e critérios como n·p·q ≥ 5 aparecem como ✅ / ⚠️ / ❌ junto
da saída: são informação para você decidir, nunca um motivo para o app trocar o teste.

| Cartão | Significado |
|---|---|
| ✅ | O critério foi atendido. |
| ⚠️ | O critério não foi atendido, ou foi com ressalva. |
| ❌ | O critério foi violado. |

**Excluir outliers** é uma caixa de opção nos diálogos que a oferecem, desmarcada por padrão. Quando
marcada, a saída diz quantos saíram e o n antes e depois.

**Regras da disciplina** (reportadas como nota, não aplicadas sozinhas): outlier suave fora de
[Q1 − 1,5D; Q3 + 1,5D] e extremo fora de [Q1 − 3D; Q3 + 3D]; normalidade por Shapiro-Wilk ou
Anderson-Darling; n·p·q ≥ 5 nas proporções; razão maior/menor variância até 9× na ANOVA; p ≤ 0,01 →
99% de confiança, p ≤ 0,05 → 95%.

**Sessão.** Cada comando acrescenta um bloco. Dá para remover um bloco, limpar tudo e exportar em
HTML (com os gráficos interativos) ou Markdown. A sessão vive só enquanto a aba estiver aberta.
"""
    )
