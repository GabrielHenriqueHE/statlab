"""Página Prática: listas do gerador da disciplina, com gabarito e conferência pelo statlab."""

import streamlit as st

from statlab import pratica
from statlab.core.conclusoes import concluir
from statlab.ui import estado

st.header("Prática")
st.caption(
    "Gere uma lista de exercícios com dados aleatórios (o mesmo gerador da disciplina). Resolva com as páginas "
    "do statlab e confira com o gabarito. A mesma semente gera sempre a mesma lista."
)

c1, c2 = st.columns([1, 2])
n = c1.number_input("Número de exercícios", min_value=1, max_value=20, value=6, key="pr_n_ex")
tipos = c2.multiselect(
    "Tipos", list(pratica.TIPOS), default=list(pratica.TIPOS), format_func=pratica.TIPOS.get, key="pr_tipos"
)
semente_txt = st.text_input("Semente (vazio = aleatória; 2026 = lista da disciplina)", value="", key="pr_semente")

if st.button("Gerar lista", type="primary", key="pr_gerar"):
    if not tipos:
        st.error("Escolha pelo menos um tipo de exercício.")
    else:
        try:
            semente = int(semente_txt) if semente_txt.strip() else None
        except ValueError:
            st.error("A semente deve ser um número inteiro.")
        else:
            st.session_state["pratica_lista"] = pratica.gerar(int(n), tipos, semente)

if "pratica_lista" not in st.session_state:
    st.info("Escolha as opções e clique em **Gerar lista**.")
    st.stop()

exs, semente = st.session_state["pratica_lista"]
st.subheader(f"Lista com semente {semente}")
d1, d2 = st.columns(2)
d1.download_button(
    "Baixar enunciados (Markdown)",
    data=pratica.lista_markdown(exs, semente).encode("utf-8"),
    file_name=f"exercicios_{semente}.md",
    mime="text/markdown",
    key="pr_baixar_lista",
)
d2.download_button(
    "Baixar gabarito (Markdown)",
    data=pratica.gabarito_markdown(exs, semente).encode("utf-8"),
    file_name=f"gabarito_{semente}.md",
    mime="text/markdown",
    key="pr_baixar_gab",
)

for i, e in enumerate(exs, 1):
    with st.expander(f"Exercício {i} — {e.titulo}", expanded=i == 1):
        st.markdown(e.enunciado)
        if st.button("Carregar os dados como worksheet", key=f"pr_carregar_{i}"):
            nome = estado.nova_planilha(f"Ex{i} (semente {semente})", pratica.worksheet_bruta(e))
            st.success(f"Worksheet **{nome}** criada e ativa. Analise-a nas páginas de testes.")
        if st.toggle("Mostrar gabarito", key=f"pr_gab_{i}"):
            st.markdown(e.gabarito)
            conf = pratica.conferir(e)
            if conf.concorda:
                st.success(f"Conferência: o statlab também escolheu **{conf.teste_statlab}**.")
            else:
                st.warning(
                    f"Conferência: o gabarito usa **{conf.teste_gerador}**, mas o statlab escolheu "
                    f"**{conf.teste_statlab}**. Confira os pré-requisitos com o professor."
                )
            st.markdown(f"> {concluir(conf.resultado)}")
