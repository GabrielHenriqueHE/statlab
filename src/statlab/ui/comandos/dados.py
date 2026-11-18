"""Menu Dados: abrir, colar, empilhar, desempilhar, recodificar e subconjunto."""

from __future__ import annotations

import pandas as pd

from statlab.core import importacao, tabela
from statlab.ui import estado
from statlab.ui.comandos import _base as b
from statlab.ui.comandos import formulario as st

MENU = "Dados"
MAX_DISTINTOS = 50


@b.comando(MENU, "", "Abrir arquivo (CSV ou Excel)")
def abrir() -> None:
    arquivo = st.file_uploader("Arquivo CSV ou Excel (.xlsx)", type=["csv", "xlsx"], key="imp_arq")
    if arquivo is None:
        return
    eh_excel = arquivo.name.lower().endswith(".xlsx")
    aba = intervalo = ""
    separador = "automático"
    if eh_excel:
        aba = st.text_input("Aba (vazio = primeira)", key="imp_aba")
        intervalo = st.text_input("Intervalo (ex.: C8:D12; vazio = todos os dados)", key="imp_int")
    else:
        separador = st.selectbox("Separador", list(importacao.SEPARADORES), key="imp_sep")
    cabecalho = st.checkbox("A primeira linha é o cabeçalho", value=True, key="imp_cab")
    nome = st.text_input("Nome da worksheet", value=arquivo.name.rsplit(".", 1)[0], key="imp_nome")

    def executar():
        if eh_excel:
            df = importacao.ler_xlsx(
                arquivo.getvalue(),
                aba=aba.strip() or None,
                intervalo=intervalo.strip() or None,
                cabecalho=cabecalho,
            )
        else:
            df = importacao.ler_csv(
                arquivo.getvalue(), separador=importacao.SEPARADORES[separador], cabecalho=cabecalho
            )
        final = estado.nova_planilha(nome, df)
        return b.item_simples(
            f"Worksheet aberta: {final}",
            comando_nome="Abrir arquivo",
            linhas=[f"{len(df)} linha(s) × {df.shape[1]} coluna(s)."],
        )

    b.rodar(executar, "Abrir")


@b.comando(MENU, "", "Colar dados")
def colar() -> None:
    texto = st.text_area("Cole aqui (do Excel, ou separado por ';')", height=180, key="col_txt")
    cabecalho = st.checkbox("A primeira linha é o cabeçalho", value=True, key="col_cab")
    nome = st.text_input("Nome da worksheet", "Dados colados", key="col_nome")

    def executar():
        df = importacao.ler_texto_colado(texto, cabecalho=cabecalho)
        final = estado.nova_planilha(nome, df)
        return b.item_simples(
            f"Worksheet criada: {final}",
            comando_nome="Colar dados",
            linhas=[f"{len(df)} linha(s) × {df.shape[1]} coluna(s)."],
        )

    b.rodar(executar, "Colar")


@b.comando(MENU, "", "Empilhar colunas")
def empilhar() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    nome, df = alvo
    escolhidas = st.multiselect("Colunas a empilhar (≥ 2)", list(df.columns), key="emp_cols")
    c1, c2 = st.columns(2)
    nome_resp = c1.text_input("Coluna de resposta", "Dados", key="emp_resp")
    nome_sub = c2.text_input("Coluna de subscritos", "Subscritos", key="emp_sub")
    if len(escolhidas) < 2:
        st.info("Escolha pelo menos duas colunas.")
        return

    def executar():
        nova, descartados = tabela.empilhar(df, escolhidas, nome_resposta=nome_resp, nome_subscritos=nome_sub)
        final = estado.nova_planilha(f"{nome} - empilhada", nova)
        notas = [f"{descartados} valor(es) faltante(s) descartado(s)."] if descartados else []
        return b.item_simples(
            f"Worksheet criada: {final}",
            comando_nome="Empilhar",
            linhas=[f"{len(nova)} linha(s)."],
            notas=notas,
        )

    b.rodar(executar, "Empilhar")


@b.comando(MENU, "", "Desempilhar coluna")
def desempilhar() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    nome, df = alvo
    cols = list(df.columns)
    c1, c2 = st.columns(2)
    resposta = c1.selectbox("Coluna de resposta", cols, key="des_resp")
    subscritos = c2.selectbox("Coluna de subscritos (níveis)", cols, index=min(1, len(cols) - 1), key="des_sub")
    if resposta == subscritos:
        st.info("Escolha colunas diferentes.")
        return

    def executar():
        nova, niveis = tabela.desempilhar(df, resposta, subscritos)
        final = estado.nova_planilha(f"{nome} - desempilhada", nova)
        return b.item_simples(
            f"Worksheet criada: {final}",
            comando_nome="Desempilhar",
            linhas=[f"Colunas: {', '.join(niveis)}."],
        )

    b.rodar(executar, "Desempilhar")


@b.comando(MENU, "", "Recodificar valores")
def recodificar() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    nome, df = alvo
    coluna = st.selectbox("Coluna", list(df.columns), key="rec_col")
    distintos = tabela.valores_distintos(df[coluna])
    if not distintos:
        st.info("A coluna não tem valores preenchidos.")
        return
    if len(distintos) > MAX_DISTINTOS:
        st.warning(
            f"A coluna tem {len(distintos)} valores distintos (máximo {MAX_DISTINTOS}). Recodificar serve "
            "para categorias ou códigos, não para medidas contínuas."
        )
        return
    mapa_df = st.data_editor(
        pd.DataFrame({"Valor atual": distintos, "Novo valor": [""] * len(distintos)}),
        disabled=["Valor atual"],
        hide_index=True,
        key=f"rec_mapa_{nome}_{coluna}",
    )
    destino = st.text_input("Coluna nova", f"{coluna} recodificada", key="rec_dest").strip()

    def executar():
        from statlab.core.dados import ErroDeDados

        if not destino:
            raise ErroDeDados("Informe o nome da coluna nova.")
        if destino in df.columns:
            raise ErroDeDados(f"Já existe uma coluna chamada {destino!r}; escolha outro nome.")
        mapa = dict(zip(mapa_df["Valor atual"], mapa_df["Novo valor"].fillna(""), strict=True))
        recodificada, trocados = tabela.recodificar(df[coluna], mapa)
        novo_df = df.copy()
        novo_df[destino] = recodificada
        estado.salvar(nome, novo_df)
        return b.item_simples(
            f"Coluna criada: {destino}",
            comando_nome="Recodificar",
            linhas=[f"{trocados} valor(es) trocado(s) a partir de {coluna}."],
        )

    b.rodar(executar, "Recodificar")


@b.comando(MENU, "", "Subconjunto (filtrar linhas)")
def subconjunto() -> None:
    alvo = b.worksheet()
    if alvo is None:
        return
    nome, df = alvo
    coluna = st.selectbox("Coluna do filtro", list(df.columns), key="sub_col")
    valores = tabela.valores_distintos(df[coluna])
    manter = st.multiselect("Manter as linhas com estes valores", valores, default=valores, key="sub_val")
    if not manter:
        st.info("Escolha pelo menos um valor.")
        return

    def executar():
        mascara = df[coluna].map(tabela.rotulo_valor).isin(manter)
        nova = df[mascara].reset_index(drop=True)
        final = estado.nova_planilha(f"{nome} - subconjunto", nova)
        return b.item_simples(
            f"Worksheet criada: {final}",
            comando_nome="Subconjunto",
            linhas=[f"{len(nova)} de {len(df)} linha(s) mantida(s), filtrando por {coluna}."],
        )

    b.rodar(executar, "Filtrar")
