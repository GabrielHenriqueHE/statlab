"""Importação de dados externos para worksheets: CSV, XLSX (aba e intervalo) e texto colado.

Não contém regras estatísticas. Cada coluna vira numérica (float, com NaN para faltantes) quando
todos os valores preenchidos são números (aceita vírgula decimal pt-BR); caso contrário, texto.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Sequence
from typing import Any

import pandas as pd
from openpyxl import load_workbook

from statlab.core.dados import ErroDeDados, numero, parse_lista

_RE_INTERVALO = re.compile(r"^\s*\$?([A-Za-z]{1,3})\$?(\d+)\s*(?::\s*\$?([A-Za-z]{1,3})\$?(\d+))?\s*$")
SEPARADORES = {"automático": None, "ponto e vírgula (;)": ";", "vírgula (,)": ",", "tabulação": "\t"}


def _letras_para_indice(letras: str) -> int:
    n = 0
    for ch in letras.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def interpretar_intervalo(ref: str) -> tuple[int, int, int | None, int | None]:
    """'C8:D12' -> (linha_ini, col_ini, linha_fim, col_fim), base 1. Uma célula única ('C8') significa
    'a partir dela, até o fim dos dados' e devolve fim None."""
    m = _RE_INTERVALO.match(ref or "")
    if not m:
        raise ErroDeDados(f"Intervalo inválido: {ref!r}. Use algo como C8:D12.")
    col_ini, lin_ini, col_fim, lin_fim = m.group(1), int(m.group(2)), m.group(3), m.group(4)
    ci = _letras_para_indice(col_ini)
    if col_fim is None:
        return lin_ini, ci, None, None
    cf, lf = _letras_para_indice(col_fim), int(lin_fim)
    if lf < lin_ini or cf < ci:
        raise ErroDeDados("O intervalo deve ir do canto superior esquerdo ao inferior direito (ex.: C8:D12).")
    return lin_ini, ci, lf, cf


def _normalizar_coluna(valores: Sequence[Any]) -> list[Any]:
    """Número (float/NaN) se todos os preenchidos forem numéricos; senão texto (ou None)."""
    numericos: list[float | None] = []
    try:
        for v in valores:
            numericos.append(numero(v))
    except ErroDeDados:
        return [None if v is None or (isinstance(v, str) and v.strip() == "") else str(v).strip() for v in valores]
    return [float("nan") if x is None else x for x in numericos]


def _nomes_unicos(brutos: Sequence[Any]) -> list[str]:
    nomes: list[str] = []
    usados: dict[str, int] = {}
    for j, bruto in enumerate(brutos, start=1):
        base = str(bruto).strip() if bruto not in (None, "") else f"C{j}"
        nome, k = base, 1
        while nome in usados:
            k += 1
            nome = f"{base}_{k}"
        usados[nome] = 1
        nomes.append(nome)
    return nomes


def montar_tabela(linhas: Sequence[Sequence[Any]], cabecalho: bool = True) -> pd.DataFrame:
    """Transforma linhas (listas) em DataFrame. Linhas totalmente vazias são descartadas."""
    linhas = [list(r) for r in linhas if any(v is not None and str(v).strip() != "" for v in r)]
    if not linhas:
        raise ErroDeDados("Nenhum dado encontrado.")
    largura = max(len(r) for r in linhas)
    linhas = [r + [None] * (largura - len(r)) for r in linhas]
    if cabecalho:
        nomes = _nomes_unicos(linhas[0])
        corpo = linhas[1:]
        if not corpo:
            raise ErroDeDados("Há cabeçalho, mas nenhuma linha de dados.")
    else:
        nomes = _nomes_unicos([None] * largura)
        corpo = linhas
    colunas = {nome: _normalizar_coluna([r[j] for r in corpo]) for j, nome in enumerate(nomes)}
    return pd.DataFrame(colunas)


def ler_xlsx(
    conteudo: bytes,
    *,
    aba: str | None = None,
    intervalo: str | None = None,
    cabecalho: bool = True,
) -> pd.DataFrame:
    """Lê uma aba (ou um intervalo como 'C8:D12') de um arquivo .xlsx."""
    try:
        wb = load_workbook(io.BytesIO(conteudo), data_only=True)
    except Exception as exc:  # openpyxl levanta vários tipos de erro para arquivo inválido
        raise ErroDeDados("Não foi possível abrir o arquivo Excel (.xlsx).") from exc
    if aba:
        if aba not in wb.sheetnames:
            raise ErroDeDados(f"A aba {aba!r} não existe. Abas disponíveis: {', '.join(wb.sheetnames)}.")
        ws = wb[aba]
    else:
        ws = wb.worksheets[0]
    if intervalo:
        l1, c1, l2, c2 = interpretar_intervalo(intervalo)
    else:
        l1, c1, l2, c2 = 1, 1, None, None
    if l2 is None:
        l2 = ws.max_row
        c2 = ws.max_column
    linhas = [list(r) for r in ws.iter_rows(min_row=l1, max_row=l2, min_col=c1, max_col=c2, values_only=True)]
    return montar_tabela(linhas, cabecalho=cabecalho)


def _decodificar(conteudo: bytes) -> str:
    for codec in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return conteudo.decode(codec)
        except UnicodeDecodeError:
            continue
    raise ErroDeDados("Não foi possível decodificar o arquivo de texto.")


def _detectar_separador(texto: str) -> str:
    """Escolhe o separador que dá o mesmo número de colunas (> 1) nas primeiras linhas; padrão ';'."""
    linhas = [ln for ln in texto.splitlines() if ln.strip()][:20]
    melhor, melhor_cols = ";", 1
    for sep in (";", "\t", ","):
        cols = [len(next(csv.reader([ln], delimiter=sep))) for ln in linhas]
        if cols and len(set(cols)) == 1 and cols[0] > melhor_cols:
            melhor, melhor_cols = sep, cols[0]
    return melhor


def ler_csv(conteudo: bytes, *, separador: str | None = None, cabecalho: bool = True) -> pd.DataFrame:
    """Lê CSV. Separador automático (';', tab ou ','), com vírgula decimal pt-BR aceita nos valores."""
    texto = _decodificar(conteudo)
    sep = separador or _detectar_separador(texto)
    linhas = list(csv.reader(io.StringIO(texto), delimiter=sep))
    return montar_tabela(linhas, cabecalho=cabecalho)


def ler_texto_colado(texto: str, *, cabecalho: bool = False) -> pd.DataFrame:
    """Dados copiados do Excel/Minitab.

    - Com tab (copiado do Excel): uma linha por registro, colunas separadas por tab.
    - Com ';' em várias linhas de mesmo número de campos (> 1): tabela separada por ';'.
    - Caso contrário (ex.: "15; 40; 31" ou uma coluna por linha): lista de uma coluna.
    """
    if texto is None or not texto.strip():
        raise ErroDeDados("Cole os dados na caixa de texto.")
    if "\t" in texto:
        return montar_tabela(list(csv.reader(io.StringIO(texto), delimiter="\t")), cabecalho=cabecalho)
    linhas_pv = [ln for ln in texto.splitlines() if ln.strip()]
    if ";" in texto and len(linhas_pv) > 1:
        campos = {len(next(csv.reader([ln], delimiter=";"))) for ln in linhas_pv}
        if len(campos) == 1 and campos != {1}:
            return montar_tabela(list(csv.reader(io.StringIO(texto), delimiter=";")), cabecalho=cabecalho)
    valores = parse_lista(texto)
    linhas = [[v] for v in valores]
    if cabecalho:
        linhas = [["Dados"], *linhas]
    return montar_tabela(linhas, cabecalho=cabecalho)
