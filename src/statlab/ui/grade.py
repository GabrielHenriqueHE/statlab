"""A grade da worksheet: um ``pd.DataFrame`` dentro de uma ``QTableView``.

Só interface. A grade não interpreta nada dos dados: mostra o que está na worksheet e grava o que o
usuário digita, preservando o dtype de cada coluna.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal


def texto_da_celula(valor: object) -> str:
    """O valor como aparece na grade: vírgula decimal, sem notação científica, vazio se faltante."""
    if valor is None:
        return ""
    if isinstance(valor, float | np.floating):
        if pd.isna(valor):
            return ""
        if np.isinf(valor):
            return "∞" if valor > 0 else "−∞"
        return np.format_float_positional(float(valor), trim="-").replace(".", ",")
    if isinstance(valor, int | np.integer) and not isinstance(valor, bool):
        return str(int(valor))
    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass
    return str(valor)


def numero_digitado(texto: str) -> float | None:
    """Converte o que foi digitado em número, aceitando vírgula ou ponto decimal.

    ``None`` quando o texto está vazio (célula faltante). Levanta ``ValueError`` se não é número.
    """
    limpo = texto.strip().replace(" ", "")
    if not limpo:
        return None
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    return float(limpo)


class GradeModel(QAbstractTableModel):
    """Model de uma worksheet.

    Editar uma célula de coluna numérica com texto que não é número é **recusado** (o valor anterior
    fica na célula): é validação de entrada, não o app decidindo algo sobre a análise.
    """

    mudou = Signal()  # qualquer alteração; quem ouve grava a worksheet no estado

    def __init__(
        self,
        df: pd.DataFrame | None = None,
        *,
        editavel: bool = True,
        bloqueadas: Sequence[str] = (),
    ) -> None:
        super().__init__()
        self._df = pd.DataFrame() if df is None else df
        self._editavel = editavel
        self._bloqueadas = set(bloqueadas)

    # --------------------------------------------------------------------- dados
    def df(self) -> pd.DataFrame:
        """A worksheet como está agora."""
        return self._df

    def set_df(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    # --------------------------------------------------------------------- Qt
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        if index.row() >= len(self._df) or index.column() >= len(self._df.columns):
            return None
        return texto_da_celula(self._df.iat[index.row(), index.column()])

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole or not self._editavel:
            return False
        if index.row() >= len(self._df) or index.column() >= len(self._df.columns):
            return False
        coluna = self._df.columns[index.column()]
        if coluna in self._bloqueadas:
            return False

        texto = "" if value is None else str(value)
        if pd.api.types.is_numeric_dtype(self._df[coluna]):
            try:
                numero = numero_digitado(texto)
            except ValueError:
                return False  # não é número: a célula numérica fica como estava
            novo: object = float("nan") if numero is None else numero
            if pd.api.types.is_integer_dtype(self._df[coluna]):
                if numero is None or float(numero) != int(numero):
                    self._df[coluna] = self._df[coluna].astype(float)
                else:
                    novo = int(numero)
        else:
            novo = texto

        self._df.iat[index.row(), index.column()] = novo
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        self.mudou.emit()
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section < len(self._df.columns):
                return str(self._df.columns[section])
            return None
        return str(section + 1)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        base = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if not self._editavel or self._df.columns[index.column()] in self._bloqueadas:
            return base
        return base | Qt.ItemIsEditable

    def _coluna_vazia(self, col: object, count: int) -> pd.Series:
        if pd.api.types.is_numeric_dtype(self._df[col]):
            return pd.Series([float("nan")] * count, dtype=float)
        return pd.Series([""] * count, dtype=object)

    def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if parent.isValid() or count < 1 or not len(self._df.columns):
            return False
        row = max(0, min(row, len(self._df)))
        vazias = pd.DataFrame({col: self._coluna_vazia(col, count) for col in self._df.columns})
        self.beginInsertRows(parent, row, row + count - 1)
        self._df = pd.concat([self._df.iloc[:row], vazias, self._df.iloc[row:]], ignore_index=True)
        self.endInsertRows()
        self.mudou.emit()
        return True

    def removeRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        if parent.isValid() or count < 1 or row < 0 or row + count > len(self._df):
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        self._df = pd.concat([self._df.iloc[:row], self._df.iloc[row + count :]], ignore_index=True)
        self.endRemoveRows()
        self.mudou.emit()
        return True
