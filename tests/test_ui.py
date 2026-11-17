"""F2 (interface): fluxos das páginas Dados, Estatísticas descritivas e Gráficos, rodados no AppTest.

Nenhum navegador é aberto: o Streamlit executa o script da página e permite acionar widgets.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from statlab.ui import estado

PAGINAS = Path(__file__).resolve().parents[1] / "src" / "statlab" / "ui" / "paginas"
TIMEOUT = 60


def _df() -> pd.DataFrame:
    rng = np.random.default_rng(3)
    return pd.DataFrame(
        {
            "Centro": ["Central"] * 20 + ["Oriente"] * 20,
            "Dias": rng.normal(4, 1, 40),
            "Custo": rng.normal(10, 2, 40),
            "Qtd": np.r_[rng.integers(1, 9, 39).astype(float), np.nan],
        }
    )


def _app(pagina: str, planilhas: dict[str, pd.DataFrame] | None = None) -> AppTest:
    at = AppTest.from_file(str(PAGINAS / pagina), default_timeout=TIMEOUT)
    if planilhas is None:
        planilhas = {"Teste": _df()}
    at.session_state[estado.PLANILHAS] = planilhas
    if planilhas:
        at.session_state[estado.ATIVA] = next(iter(planilhas))
    return at.run()


def _sem_erros(at: AppTest, esperando_mensagem: bool = False) -> None:
    """Nenhuma exceção não tratada. Sem ``esperando_mensagem``, também nenhum ``st.error``."""
    assert [e.value for e in at.exception] == []
    if not esperando_mensagem:
        assert [e.value for e in at.error] == []


# --------------------------------------------------------------------------- Dados


def test_dados_sem_worksheet_mostra_orientacao():
    at = _app("dados.py", planilhas={})
    _sem_erros(at)
    assert any("Ainda não há worksheets" in i.value for i in at.info)


def test_dados_colar_cria_nova_worksheet_e_ativa():
    at = _app("dados.py")
    at.text_area(key="colar_texto").input("784\t686\n635\t648")
    at.button(key="btn_colar").click().run()
    _sem_erros(at)
    planilhas = at.session_state[estado.PLANILHAS]
    assert "Dados colados" in planilhas
    assert planilhas["Dados colados"].shape == (2, 2)
    assert at.session_state[estado.ATIVA] == "Dados colados"


def test_dados_colar_vazio_mostra_erro_amigavel():
    at = _app("dados.py")
    at.text_area(key="colar_texto").input("   ")
    at.button(key="btn_colar").click().run()
    _sem_erros(at, esperando_mensagem=True)
    assert any("Cole os dados" in e.value for e in at.error)


def test_dados_empilhar_cria_worksheet_empilhada():
    at = _app("dados.py")
    at.multiselect(key="emp_colunas").set_value(["Dias", "Custo"])
    at.button(key="btn_empilhar").click().run()
    _sem_erros(at)
    nova = at.session_state[estado.PLANILHAS]["Teste - empilhada"]
    assert set(nova["Subscritos"]) == {"Dias", "Custo"}
    assert len(nova) == 80


def test_dados_empilhar_uma_coluna_mostra_erro():
    at = _app("dados.py")
    at.multiselect(key="emp_colunas").set_value(["Dias"])
    at.button(key="btn_empilhar").click().run()
    _sem_erros(at, esperando_mensagem=True)
    assert any("pelo menos 2" in e.value for e in at.error)


def test_dados_desempilhar_por_grupo():
    at = _app("dados.py")
    at.selectbox(key="desemp_resp").set_value("Dias")
    at.selectbox(key="desemp_sub").set_value("Centro")
    at.button(key="btn_desempilhar").click().run()
    _sem_erros(at)
    nova = at.session_state[estado.PLANILHAS]["Teste - desempilhada"]
    assert list(nova.columns) == ["Central", "Oriente"]


def test_dados_editar_salva_alteracoes():
    at = _app("dados.py")
    at.button(key="salvar_Teste").click().run()
    _sem_erros(at)
    assert any("salvas" in s.value for s in at.success)


# --------------------------------------------------------------------------- Estatísticas descritivas


def test_descritiva_resumo_por_grupo_no_formato_minitab():
    at = _app("descritiva.py")
    at.multiselect(key="desc_vars").set_value(["Dias"])
    at.selectbox(key="desc_grupo").set_value("Centro")
    at.run()
    _sem_erros(at)
    tabela = at.dataframe[0].value
    assert list(tabela["Grupo"]) == ["Central", "Oriente"]
    assert {"N", "N*", "EP da média", "Assimetria", "Curtose"} <= set(tabela.columns)
    assert list(tabela["N"]) == ["20", "20"]


def test_descritiva_mostra_anderson_darling_e_faltantes():
    at = _app("descritiva.py")
    at.multiselect(key="desc_vars").set_value(["Qtd"])
    at.run()
    _sem_erros(at)
    resumo = at.dataframe[0].value
    assert resumo.loc[0, "N*"] == "1"
    assert len(at.dataframe) == 2  # estatísticas + Anderson-Darling


def test_descritiva_sem_variaveis_pede_escolha():
    at = _app("descritiva.py")
    at.multiselect(key="desc_vars").set_value([])
    at.run()
    _sem_erros(at)
    assert any("pelo menos uma variável" in i.value for i in at.info)


def test_descritiva_sem_colunas_numericas_avisa():
    texto = pd.DataFrame({"nome": ["a", "b", "c"]})
    at = _app("descritiva.py", planilhas={"Texto": texto})
    _sem_erros(at)
    assert any("não tem colunas numéricas" in w.value for w in at.warning)


# --------------------------------------------------------------------------- Gráficos


@pytest.mark.parametrize(
    "tipo",
    [
        "Histograma",
        "Boxplot",
        "Valores individuais",
        "Intervalos (IC da média)",
        "Probabilidade normal",
        "Pareto",
        "Gráfico de barras",
        "Série temporal",
        "Correlograma",
        "Matriz de dispersão",
    ],
)
def test_graficos_cada_tipo_renderiza_sem_erro(tipo):
    at = _app("graficos.py")
    at.selectbox(key="graf_tipo").set_value(tipo).run()
    _sem_erros(at)
    assert len(at.get("plotly_chart")) == 1, f"{tipo} não gerou gráfico"


def test_graficos_dispersao_com_grupo_e_reta():
    at = _app("graficos.py")
    at.selectbox(key="graf_tipo").set_value("Diagrama de dispersão").run()
    at.selectbox(key="d_x").set_value("Dias")
    at.selectbox(key="d_y").set_value("Custo")
    at.selectbox(key="d_grupo").set_value("Centro")
    at.checkbox(key="d_reta").check()
    at.run()
    _sem_erros(at)
    assert len(at.get("plotly_chart")) == 1


def test_graficos_correlograma_exige_duas_colunas_mostra_aviso_amigavel():
    at = _app("graficos.py")
    at.selectbox(key="graf_tipo").set_value("Correlograma").run()
    at.multiselect(key="c_vars").set_value(["Dias"])
    at.run()
    _sem_erros(at)
    assert any("pelo menos 2 variáveis" in i.value for i in at.info)
    assert at.get("plotly_chart") == []


def test_graficos_tem_download_html():
    at = _app("graficos.py")
    botoes = at.get("download_button")
    assert any("HTML" in b.proto.label for b in botoes)
