"""Entrada do app statlab (Streamlit). Rode com ``uv run statlab`` ou ``streamlit run src/statlab/ui/app.py``."""

import streamlit as st

from statlab.ui import estado

st.set_page_config(page_title="statlab", layout="wide")

paginas = [
    st.Page("paginas/dados.py", title="Dados", default=True),
    st.Page("paginas/descritiva.py", title="Estatísticas descritivas"),
    st.Page("paginas/graficos.py", title="Gráficos"),
]
estado.seletor_lateral()
st.navigation(paginas).run()
