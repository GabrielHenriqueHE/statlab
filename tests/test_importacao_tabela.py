"""F2: importação (CSV, XLSX com aba e intervalo, texto colado) e operações de worksheet."""

import io

import numpy as np
import pandas as pd
import pytest
from openpyxl import Workbook

from statlab.core import importacao, tabela
from statlab.core.dados import ErroDeDados


def _xlsx(abas: dict[str, list[list[object]]]) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    for nome, linhas in abas.items():
        ws = wb.create_sheet(nome)
        for linha in linhas:
            ws.append(linha)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------------- intervalos


@pytest.mark.parametrize(
    "ref, esperado",
    [("C8:D12", (8, 3, 12, 4)), ("a1:b2", (1, 1, 2, 2)), ("$C$8:$D$12", (8, 3, 12, 4)), ("AA3", (3, 27, None, None))],
)
def test_interpretar_intervalo(ref, esperado):
    assert importacao.interpretar_intervalo(ref) == esperado


@pytest.mark.parametrize("ruim", ["", "12", "C", "D12:C8", "xx"])
def test_intervalo_invalido_erro_claro(ruim):
    with pytest.raises(ErroDeDados):
        importacao.interpretar_intervalo(ruim)


# --------------------------------------------------------------------------- xlsx


def test_xlsx_aba_e_intervalo_como_no_minitab():
    conteudo = _xlsx(
        {
            "Resumo": [["x", "y"], [1, 2]],
            "Dados": [
                ["lixo", "lixo", "lixo"],
                ["lixo", "Antes", "Depois"],
                ["lixo", 784, 686],
                ["lixo", 635, 648],
                ["lixo", 743, None],
            ],
        }
    )
    df = importacao.ler_xlsx(conteudo, aba="Dados", intervalo="B2:C5")
    assert list(df.columns) == ["Antes", "Depois"]
    assert len(df) == 3
    assert df["Antes"].tolist() == [784.0, 635.0, 743.0]
    assert np.isnan(df["Depois"].iloc[2])


def test_xlsx_primeira_aba_sem_intervalo():
    df = importacao.ler_xlsx(_xlsx({"A": [["valor"], [1], [2]]}))
    assert df["valor"].tolist() == [1.0, 2.0]


def test_xlsx_aba_inexistente_erro_lista_as_abas():
    with pytest.raises(ErroDeDados, match="Abas disponíveis"):
        importacao.ler_xlsx(_xlsx({"A": [["v"], [1]]}), aba="Não existe")


def test_xlsx_invalido_erro_claro():
    with pytest.raises(ErroDeDados, match=r"\.xlsx"):
        importacao.ler_xlsx(b"isto nao e um excel")


def test_xlsx_coluna_com_texto_vira_texto_e_numeros_viram_float():
    df = importacao.ler_xlsx(_xlsx({"A": [["Centro", "Dias"], ["Central", 3.5], ["Oriente", "4,2"]]}))
    assert df["Centro"].tolist() == ["Central", "Oriente"]
    assert df["Dias"].tolist() == [3.5, 4.2]


# --------------------------------------------------------------------------- csv


def test_csv_separador_ponto_e_virgula_com_decimal_pt_br():
    texto = "Antes;Depois\n784,5;686\n635;648,25\n"
    df = importacao.ler_csv(texto.encode("utf-8"))
    assert df["Antes"].tolist() == [784.5, 635.0]
    assert df["Depois"].tolist() == [686.0, 648.25]


def test_csv_detecta_tab_e_virgula():
    tab = importacao.ler_csv(b"a\tb\n1\t2\n3\t4")
    assert tab.shape == (2, 2)
    virg = importacao.ler_csv(b"a,b\n1,2\n3,4")
    assert virg.shape == (2, 2)


def test_csv_latin1_acentos_preservados():
    df = importacao.ler_csv("Região;Valor\nSul;1\nNorte;2".encode("cp1252"))
    assert df["Região"].tolist() == ["Sul", "Norte"]


def test_csv_sem_cabecalho_nomeia_colunas():
    df = importacao.ler_csv(b"1;2\n3;4", cabecalho=False)
    assert list(df.columns) == ["C1", "C2"]
    assert len(df) == 2


def test_csv_vazio_erro():
    with pytest.raises(ErroDeDados):
        importacao.ler_csv(b"   \n  ")


def test_nomes_duplicados_recebem_sufixo():
    df = importacao.ler_csv(b"a;a;\n1;2;3")
    assert list(df.columns) == ["a", "a_2", "C3"]


# --------------------------------------------------------------------------- texto colado


def test_colar_tab_do_excel():
    df = importacao.ler_texto_colado("784\t686\n635\t648\n")
    assert df.shape == (2, 2)
    assert df.iloc[0, 1] == 686.0


def test_colar_lista_uma_coluna_com_espacos_e_quebras():
    df = importacao.ler_texto_colado("15; 40; 31\n25 48")
    assert df.shape == (5, 1)
    assert df.iloc[:, 0].tolist() == [15.0, 40.0, 31.0, 25.0, 48.0]


def test_colar_tabela_com_ponto_e_virgula_por_linha():
    df = importacao.ler_texto_colado("784;686\n635;648")
    assert df.shape == (2, 2)
    assert df.iloc[1, 1] == 648.0


def test_colar_com_cabecalho():
    df = importacao.ler_texto_colado("Antes\tDepois\n1\t2", cabecalho=True)
    assert list(df.columns) == ["Antes", "Depois"]


def test_colar_vazio_erro():
    with pytest.raises(ErroDeDados):
        importacao.ler_texto_colado("   ")


# --------------------------------------------------------------------------- worksheet


def _df_empilhar() -> pd.DataFrame:
    return pd.DataFrame({"A": [1.0, 2.0, np.nan, np.nan], "B": [3.0, np.nan, 5.0, 6.0]})


def test_empilhar_descarta_faltantes_e_conta():
    tab, descartados = tabela.empilhar(_df_empilhar(), ["A", "B"])
    assert len(tab) == 5  # A: 2 valores; B: 3 valores
    assert descartados == 3  # 2 faltantes em A e 1 em B
    assert set(tab["Subscritos"]) == {"A", "B"}
    assert tab.loc[tab["Subscritos"] == "B", "Dados"].tolist() == [3.0, 5.0, 6.0]


def test_empilhar_precisa_de_duas_colunas():
    with pytest.raises(ErroDeDados, match="pelo menos 2"):
        tabela.empilhar(_df_empilhar(), ["A"])


def test_empilhar_nomes_iguais_erro():
    with pytest.raises(ErroDeDados):
        tabela.empilhar(_df_empilhar(), ["A", "B"], nome_resposta="x", nome_subscritos="x")


def test_desempilhar_separa_por_nivel_com_faltantes_no_fim():
    longa = pd.DataFrame(
        {
            "Dias": [4.0, 5.0, 3.0, 2.0, 6.0],
            "Centro": ["Central", "Central", "Oriente", "Oriente", "Oriente"],
        }
    )
    larga, niveis = tabela.desempilhar(longa, "Dias", "Centro")
    assert niveis == ["Central", "Oriente"]
    assert larga["Central"].tolist()[:2] == [4.0, 5.0]
    assert np.isnan(larga["Central"].iloc[2])
    assert larga["Oriente"].tolist() == [3.0, 2.0, 6.0]


def test_desempilhar_colunas_iguais_erro():
    with pytest.raises(ErroDeDados):
        tabela.desempilhar(_df_empilhar(), "A", "A")


def test_empilhar_e_desempilhar_sao_inversos():
    original = pd.DataFrame({"G1": [1.0, 2.0, 3.0], "G2": [4.0, 5.0, 6.0]})
    longa, _ = tabela.empilhar(original, ["G1", "G2"], nome_resposta="Resp", nome_subscritos="Grupo")
    volta, niveis = tabela.desempilhar(longa, "Resp", "Grupo")
    assert niveis == ["G1", "G2"]
    assert volta["G1"].tolist() == [1.0, 2.0, 3.0]
    assert volta["G2"].tolist() == [4.0, 5.0, 6.0]


def test_pares_completos_avisa_quantos_descartados():
    df = pd.DataFrame({"Antes": [1.0, np.nan, 3.0, 4.0], "Depois": [2.0, 2.0, np.nan, 5.0]})
    completo, descartadas = tabela.pares_completos(df, ["Antes", "Depois"])
    assert len(completo) == 2
    assert descartadas == 2


def test_faltantes_por_coluna_e_tipos():
    df = pd.DataFrame({"n": [1.0, np.nan], "t": ["a", None]})
    resumo = tabela.faltantes_por_coluna(df)
    assert resumo.loc[0, "tipo"] == "numérico"
    assert resumo.loc[1, "tipo"] == "texto"
    assert resumo.loc[0, "faltantes"] == 1
