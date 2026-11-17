"""Peças de interface reutilizadas pelas páginas de testes (sem regras estatísticas)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from statlab.core import tabela
from statlab.core.formatacao import num, p_valor
from statlab.core.resultados import ATENCAO, FALHA, OK, Resultado

ICONES = {OK: "✅", ATENCAO: "⚠️", FALHA: "❌"}
ALTERNATIVAS = {"Diferente (bilateral)": "bilateral", "Maior (unilateral)": "maior", "Menor (unilateral)": "menor"}
MODO_COLUNAS = "Uma coluna por grupo"
MODO_EMPILHADO = "Resposta em uma coluna e grupo em outra"


def escolher_alternativa(chave: str, descricao_maior: str, descricao_menor: str) -> str:
    """Radio da hipótese alternativa. As descrições dizem o que 'maior' e 'menor' significam no problema."""
    rotulos = {
        "Diferente (bilateral)": "Diferente (bilateral)",
        "Maior (unilateral)": f"Maior: {descricao_maior}",
        "Menor (unilateral)": f"Menor: {descricao_menor}",
    }
    escolha = st.radio(
        "Hipótese alternativa (H₁)", list(ALTERNATIVAS), format_func=rotulos.get, key=chave, horizontal=True
    )
    if ALTERNATIVAS[escolha] != "bilateral":
        st.caption("⚠️ Use o teste unilateral só se a direção foi definida **antes** de olhar os dados.")
    return ALTERNATIVAS[escolha]


def _formatar_gl(gl: tuple[float, ...] | None) -> str:
    if not gl:
        return "—"
    return "; ".join(num(g, 0) if float(g).is_integer() else num(g, 1) for g in gl)


def resultado(res: Resultado) -> None:
    """Teste usado, estatística, gl, p, n, IC e a decisão pela regra da apostila."""
    st.subheader(f"Resultado: {res.nome}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(res.rotulo_estatistica or "Estatística", "—" if res.estatistica is None else num(res.estatistica, 3))
    c2.metric("gl", _formatar_gl(res.gl))
    c3.metric("p", p_valor(res.p).removeprefix("= "))
    c4.metric("n", "—" if res.n is None else str(res.n))
    if res.ic is not None:
        st.write(f"IC 95% para {res.ic_descricao}: **({num(res.ic[0])}; {num(res.ic[1])})**")
    alpha_txt = num(res.alpha, 2)
    if res.significativo:
        st.success(
            f"Significativo com {res.nivel_confianca}% de confiança (p {p_valor(res.p)} ≤ α = {alpha_txt}): "
            "rejeita-se H₀."
        )
    else:
        st.info(
            f"Não significativo ao nível α = {alpha_txt} (p {p_valor(res.p)}): não se rejeita H₀ — "
            "não há evidência suficiente (isso não prova H₀)."
        )


def prerequisitos(res: Resultado) -> None:
    """Cartões ✅/⚠️/❌ de cada pré-requisito verificado."""
    if not res.verificacoes:
        return
    st.subheader("Pré-requisitos")
    for v in res.verificacoes:
        st.markdown(f"{ICONES.get(v.status, '•')} **{v.nome}** — {v.detalhe}")


def avisos(res: Resultado) -> None:
    for a in res.avisos:
        st.warning(a)


def calculo(res: Resultado) -> None:
    with st.expander("Mostrar cálculo"):
        for linha in res.passos:
            st.text(linha)


def mostrar(res: Resultado) -> None:
    """Bloco completo: pré-requisitos, resultado, avisos e cálculo."""
    prerequisitos(res)
    resultado(res)
    avisos(res)
    calculo(res)


def exigir_numericas(df: pd.DataFrame, nome: str, minimo: int = 1) -> list[str]:
    numericas = tabela.colunas_numericas(df)
    if len(numericas) < minimo:
        st.warning(f"A worksheet **{nome}** precisa de pelo menos {minimo} coluna(s) numérica(s).")
        st.stop()
    return numericas


def selecionar_grupos(
    df: pd.DataFrame, chave: str, *, minimo: int = 2, maximo: int | None = None
) -> dict[str, np.ndarray] | None:
    """Escolha dos grupos como no Minitab: colunas separadas ou resposta + coluna de grupos.

    Devolve ``{nome_do_grupo: valores}`` ou None (com mensagem) se a escolha ainda está incompleta.
    """
    numericas = tabela.colunas_numericas(df)
    modo = st.radio("Como os dados estão organizados?", [MODO_COLUNAS, MODO_EMPILHADO], key=f"{chave}_modo")
    if modo == MODO_COLUNAS:
        padrao = numericas[:maximo] if maximo is not None else numericas
        cols = st.multiselect(
            "Colunas (uma por grupo)", numericas, default=padrao, key=f"{chave}_cols", max_selections=maximo
        )
        if len(cols) < minimo:
            st.info(f"Escolha pelo menos {minimo} colunas.")
            return None
        return {c: df[c].to_numpy(dtype=float) for c in cols}

    outras = list(df.columns)
    if not numericas or len(outras) < 2:
        st.info("A worksheet precisa de uma coluna numérica (resposta) e de outra coluna com os grupos.")
        return None
    resposta = st.selectbox("Resposta (numérica)", numericas, key=f"{chave}_resp")
    candidatas = [c for c in outras if c != resposta]
    grupo = st.selectbox("Coluna com os grupos", candidatas, key=f"{chave}_grupo")
    niveis = [str(n) for n in pd.unique(df[grupo].dropna())]
    if maximo is not None and len(niveis) > maximo:
        niveis = st.multiselect(
            f"Níveis a comparar ({maximo})",
            niveis,
            default=niveis[:maximo],
            key=f"{chave}_niveis",
            max_selections=maximo,
        )
    if len(niveis) < minimo:
        st.info(f"São necessários pelo menos {minimo} grupos (níveis) na coluna escolhida.")
        return None
    rotulos = df[grupo].astype(str)
    return {n: df.loc[rotulos == n, resposta].to_numpy(dtype=float) for n in niveis}
