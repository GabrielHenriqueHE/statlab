"""Página Dados: importar arquivos, colar dados, editar e reorganizar worksheets (menu Dados do Minitab)."""

import pandas as pd
import streamlit as st

from statlab.core import importacao, tabela
from statlab.core.dados import ErroDeDados
from statlab.ui import estado

st.header("Dados")
st.caption(
    "Uma worksheet é um conjunto de colunas. Importe um arquivo, cole dados do Excel ou edite diretamente. "
    "Faltantes ficam em branco e são descartados das análises, com aviso."
)

aba_importar, aba_colar, aba_editar, aba_reorganizar, aba_recodificar = st.tabs(
    ["Importar arquivo", "Colar dados", "Editar worksheet", "Empilhar / desempilhar", "Recodificar"]
)

# ---------------------------------------------------------------- importar arquivo
with aba_importar:
    arquivo = st.file_uploader("Arquivo CSV ou Excel (.xlsx)", type=["csv", "xlsx"], key="upload_arquivo")
    if arquivo is not None:
        eh_excel = arquivo.name.lower().endswith(".xlsx")
        aba = intervalo = ""
        separador = "automático"
        if eh_excel:
            aba = st.text_input("Aba (vazio = primeira aba)", key="xlsx_aba")
            intervalo = st.text_input("Intervalo (ex.: C8:D12; vazio = todos os dados)", key="xlsx_intervalo")
        else:
            separador = st.selectbox("Separador", list(importacao.SEPARADORES), key="csv_separador")
        cabecalho = st.checkbox("A primeira linha é o cabeçalho (nomes das colunas)", value=True, key="imp_cab")
        nome = st.text_input("Nome da worksheet", value=arquivo.name.rsplit(".", 1)[0], key="imp_nome")
        if st.button("Importar", type="primary", key="btn_importar"):
            try:
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
            except ErroDeDados as exc:
                st.error(str(exc))
            else:
                final = estado.nova_planilha(nome, df)
                st.success(f"Worksheet **{final}** criada: {len(df)} linhas × {df.shape[1]} colunas.")
                st.rerun()

# ---------------------------------------------------------------- colar dados
with aba_colar:
    texto = st.text_area(
        "Cole aqui os dados (copiados do Excel: colunas separadas por tab; ou uma lista separada por ; ou espaço)",
        height=180,
        key="colar_texto",
    )
    cabecalho_colar = st.checkbox("A primeira linha é o cabeçalho", value=False, key="colar_cab")
    nome_colar = st.text_input("Nome da worksheet", value="Dados colados", key="colar_nome")
    if st.button("Criar worksheet a partir do texto", type="primary", key="btn_colar"):
        try:
            df = importacao.ler_texto_colado(texto, cabecalho=cabecalho_colar)
        except ErroDeDados as exc:
            st.error(str(exc))
        else:
            final = estado.nova_planilha(nome_colar, df)
            st.success(f"Worksheet **{final}** criada: {len(df)} linhas × {df.shape[1]} colunas.")
            st.rerun()

# ---------------------------------------------------------------- editar
with aba_editar:
    ativa = estado.ativa()
    if ativa is None:
        st.info("Ainda não há worksheets. Importe um arquivo ou cole dados.")
    else:
        nome, df = ativa
        st.subheader(f"Worksheet: {nome}")
        st.dataframe(tabela.faltantes_por_coluna(df), hide_index=True)
        editado = st.data_editor(df, num_rows="dynamic", key=f"editor_{nome}")
        if st.button("Salvar alterações", key=f"salvar_{nome}"):
            estado.salvar(nome, pd.DataFrame(editado))
            st.success("Alterações salvas nesta sessão.")

# ---------------------------------------------------------------- empilhar / desempilhar
with aba_reorganizar:
    ativa = estado.ativa()
    if ativa is None:
        st.info("Não há worksheet para reorganizar.")
    else:
        nome, df = ativa
        st.subheader("Empilhar colunas")
        st.caption(
            "Junta várias colunas em uma coluna de resposta, com outra coluna dizendo a origem "
            "(equivalente a Dados › Empilhar). Faltantes são descartados."
        )
        escolhidas = st.multiselect("Colunas a empilhar (≥ 2)", list(df.columns), key="emp_colunas")
        col1, col2 = st.columns(2)
        nome_resp = col1.text_input("Nome da coluna de resposta", value="Dados", key="emp_resp")
        nome_sub = col2.text_input("Nome da coluna de subscritos", value="Subscritos", key="emp_sub")
        if st.button("Empilhar", key="btn_empilhar"):
            try:
                empilhada, descartados = tabela.empilhar(
                    df, escolhidas, nome_resposta=nome_resp, nome_subscritos=nome_sub
                )
            except ErroDeDados as exc:
                st.error(str(exc))
            else:
                final = estado.nova_planilha(f"{nome} - empilhada", empilhada)
                msg = f"Worksheet **{final}** criada com {len(empilhada)} linhas."
                if descartados:
                    msg += f" {descartados} valor(es) faltante(s) foram descartados."
                st.success(msg)
                st.rerun()

        st.subheader("Desempilhar")
        st.caption(
            "Separa uma coluna de resposta em uma coluna por nível do subscrito (equivalente a Dados › Desempilhar)."
        )
        resposta = st.selectbox("Coluna de resposta", list(df.columns), key="desemp_resp")
        subscritos = st.selectbox("Coluna de subscritos (níveis)", list(df.columns), key="desemp_sub")
        if st.button("Desempilhar", key="btn_desempilhar"):
            try:
                desempilhada, niveis = tabela.desempilhar(df, resposta, subscritos)
            except ErroDeDados as exc:
                st.error(str(exc))
            else:
                final = estado.nova_planilha(f"{nome} - desempilhada", desempilhada)
                st.success(f"Worksheet **{final}** criada com as colunas: {', '.join(niveis)}.")
                st.rerun()

# ---------------------------------------------------------------- recodificar
MAX_DISTINTOS = 50

with aba_recodificar:
    ativa = estado.ativa()
    if ativa is None:
        st.info("Não há worksheet para recodificar.")
    else:
        nome, df = ativa
        st.caption(
            "Troca valores de uma coluna e grava o resultado em uma coluna nova (equivalente a Dados › Recodificar). "
            "Deixe o novo valor em branco para manter o valor atual. Ex.: 1 → Manhã, 2 → Tarde; ou A → 0, B → 1."
        )
        coluna = st.selectbox("Coluna", list(df.columns), key="rec_coluna")
        distintos = tabela.valores_distintos(df[coluna])
        if not distintos:
            st.info("A coluna não tem valores preenchidos.")
        elif len(distintos) > MAX_DISTINTOS:
            st.warning(
                f"A coluna tem {len(distintos)} valores distintos (máximo {MAX_DISTINTOS}). Recodificar serve para "
                "categorias ou códigos, não para medidas contínuas."
            )
        else:
            mapa_df = st.data_editor(
                pd.DataFrame({"Valor atual": distintos, "Novo valor": [""] * len(distintos)}),
                disabled=["Valor atual"],
                hide_index=True,
                key=f"rec_mapa_{nome}_{coluna}",
            )
            nova = st.text_input("Nome da coluna nova", value=f"{coluna} recodificada", key="rec_nova").strip()
            if st.button("Recodificar", type="primary", key="btn_recodificar"):
                if not nova:
                    st.error("Informe o nome da coluna nova.")
                elif nova in df.columns:
                    st.error(f"Já existe uma coluna chamada {nova!r}; escolha outro nome.")
                else:
                    mapa = dict(zip(mapa_df["Valor atual"], mapa_df["Novo valor"].fillna(""), strict=True))
                    try:
                        recodificada, trocados = tabela.recodificar(df[coluna], mapa)
                    except ErroDeDados as exc:
                        st.error(str(exc))
                    else:
                        novo_df = df.copy()
                        novo_df[nova] = recodificada
                        estado.salvar(nome, novo_df)
                        tipo = "numérica" if pd.api.types.is_numeric_dtype(recodificada) else "de texto"
                        st.success(f"Coluna **{nova}** ({tipo}) criada em **{nome}**: {trocados} valor(es) trocado(s).")
