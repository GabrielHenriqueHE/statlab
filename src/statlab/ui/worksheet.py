"""A seção de worksheets: a barra das worksheets abertas e a grade da ativa (como no Minitab)."""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from statlab.ui import estado
from statlab.ui.grade import GradeModel

COLUNAS_NOVA = 3
LINHAS_NOVA = 10


def worksheet_vazia() -> pd.DataFrame:
    """Uma worksheet nova: colunas C1…C3 e linhas em branco, prontas para digitar."""
    return pd.DataFrame({f"C{i}": [float("nan")] * LINHAS_NOVA for i in range(1, COLUNAS_NOVA + 1)})


class PainelWorksheet(QWidget):
    """Barra com um botão por worksheet aberta, mais a grade da worksheet ativa."""

    def __init__(self) -> None:
        super().__init__()
        fora = QVBoxLayout(self)
        fora.setContentsMargins(6, 6, 6, 6)

        self.titulo = QLabel()
        self.titulo.setTextFormat(Qt.RichText)

        self.barra = QHBoxLayout()
        self.barra.setContentsMargins(0, 0, 0, 0)
        self.grupo_botoes = QButtonGroup(self)
        self.grupo_botoes.setExclusive(True)
        caixa_barra = QWidget()
        caixa_barra.setLayout(self.barra)

        self.tabela = QTableView()
        self.modelo = GradeModel()
        self.tabela.setModel(self.modelo)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tabela.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        self.aviso_vazio = QLabel(
            "Nenhuma worksheet aberta. Use <b>Dados › Abrir arquivo</b>, <b>Dados › Colar dados</b> "
            "ou o botão <b>+</b> para começar uma em branco."
        )
        self.aviso_vazio.setTextFormat(Qt.RichText)
        self.aviso_vazio.setWordWrap(True)
        self.aviso_vazio.setStyleSheet("color: gray; padding: 12px;")

        linhas = QHBoxLayout()
        linhas.setContentsMargins(0, 0, 0, 0)
        self.botao_linha = QPushButton("Adicionar linha")
        self.botao_remover = QPushButton("Remover linhas selecionadas")
        self.botao_linha.clicked.connect(self._adicionar_linha)
        self.botao_remover.clicked.connect(self._remover_linhas)
        linhas.addWidget(self.botao_linha)
        linhas.addWidget(self.botao_remover)
        linhas.addStretch()

        fora.addWidget(self.titulo)
        fora.addWidget(caixa_barra)
        fora.addWidget(self.aviso_vazio)
        fora.addWidget(self.tabela, 1)
        fora.addLayout(linhas)

        self.modelo.mudou.connect(self._gravar)
        estado.atual().worksheets_mudaram.connect(self.redesenhar)
        estado.atual().ativa_mudou.connect(lambda _nome: self.redesenhar())
        self.redesenhar()

    # ------------------------------------------------------------------ desenho
    def redesenhar(self) -> None:
        """Refaz a barra de worksheets e põe a ativa na grade."""
        for botao in list(self.grupo_botoes.buttons()):
            self.grupo_botoes.removeButton(botao)
        while self.barra.count():
            item = self.barra.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        ativa = estado.ativa()
        nome_ativo = ativa[0] if ativa else None
        for nome in estado.planilhas():
            botao = QPushButton(nome)
            botao.setCheckable(True)
            botao.setChecked(nome == nome_ativo)
            botao.clicked.connect(lambda _marcado=False, n=nome: estado.ativa_set(n))
            self.grupo_botoes.addButton(botao)
            self.barra.addWidget(botao)
        mais = QPushButton("+")
        mais.setMaximumWidth(36)
        mais.setToolTip("Nova worksheet em branco")
        mais.clicked.connect(self.nova_worksheet)
        self.barra.addWidget(mais)
        self.barra.addStretch()

        tem_worksheet = ativa is not None
        self.titulo.setText(f"<b>Worksheet: {nome_ativo}</b>" if tem_worksheet else "<b>Worksheets</b>")
        self.aviso_vazio.setVisible(not tem_worksheet)
        self.tabela.setVisible(tem_worksheet)
        self.botao_linha.setEnabled(tem_worksheet)
        self.botao_remover.setEnabled(tem_worksheet)
        self.modelo.set_df(ativa[1] if tem_worksheet else pd.DataFrame())

    # ------------------------------------------------------------------ ações
    def nova_worksheet(self) -> None:
        estado.nova_planilha("Worksheet", worksheet_vazia())

    def _gravar(self) -> None:
        ativa = estado.ativa()
        if ativa is not None:
            estado.salvar(ativa[0], self.modelo.df())

    def _adicionar_linha(self) -> None:
        self.modelo.insertRows(self.modelo.rowCount(), 1)

    def _remover_linhas(self) -> None:
        linhas = sorted({i.row() for i in self.tabela.selectedIndexes()}, reverse=True)
        for linha in linhas:
            self.modelo.removeRows(linha, 1)
