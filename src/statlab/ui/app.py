"""Entrada do app statlab (Streamlit). Rode com ``uv run statlab`` ou ``streamlit run src/statlab/ui/app.py``."""

import streamlit as st

from statlab.ui import estado

st.set_page_config(page_title="statlab", layout="wide")

paginas = {
    "Dados": [
        st.Page("paginas/dados.py", title="Dados", default=True),
        st.Page("paginas/descritiva.py", title="Estatísticas descritivas"),
        st.Page("paginas/graficos.py", title="Gráficos"),
    ],
    "Testes de hipótese": [
        st.Page("paginas/assistente.py", title="Qual teste usar?"),
        st.Page("paginas/normalidade.py", title="Normalidade"),
        st.Page("paginas/uma_amostra.py", title="Uma amostra (t, Z, proporção)"),
        st.Page("paginas/dois_grupos.py", title="Dois grupos independentes"),
        st.Page("paginas/pareado.py", title="Antes × depois (pareado)"),
        st.Page("paginas/anova.py", title="Três ou mais grupos (ANOVA)"),
        st.Page("paginas/anova_dois_fatores.py", title="ANOVA de dois fatores"),
        st.Page("paginas/proporcoes.py", title="Duas proporções"),
        st.Page("paginas/qui_quadrado.py", title="Qui-quadrado"),
    ],
    "Relações": [
        st.Page("paginas/correlacao.py", title="Correlação e regressão"),
        st.Page("paginas/regressao_multipla.py", title="Regressão múltipla"),
    ],
    "Relatório": [
        st.Page("paginas/relatorio.py", title="Relatório"),
    ],
}
estado.seletor_lateral()
estado.seletor_alpha()
st.navigation(paginas).run()
