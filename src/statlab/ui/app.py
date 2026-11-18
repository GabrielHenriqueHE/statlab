"""Entrada do app statlab (Qt). Rode com ``uv run statlab``.

Layout no modelo do Minitab: barra de menus nativa em cima, janela de sessão e seção de worksheets
separadas por um divisor que o usuário arrasta.
"""

from __future__ import annotations

import sys
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplitter

from statlab.ui import menu, sessao, worksheet

TITULO = "statlab"
RODAPE = (
    "O statlab executa o comando que você escolher, com as opções que você marcar. "
    "Ele não troca o teste, não exclui dados e não escreve a conclusão."
)


class JanelaPrincipal(QMainWindow):
    """A janela do app. Quem quiser um estado próprio chama ``estado.set_estado`` antes de criá-la."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(TITULO)
        self.resize(1200, 820)

        self.painel_sessao = sessao.PainelSessao()
        self.painel_worksheet = worksheet.PainelWorksheet()

        divisor = QSplitter(Qt.Vertical)
        divisor.addWidget(self.painel_sessao)
        divisor.addWidget(self.painel_worksheet)
        divisor.setStretchFactor(0, 3)
        divisor.setStretchFactor(1, 2)
        divisor.setSizes([480, 340])
        self.setCentralWidget(divisor)

        self.acoes = menu.montar(self.menuBar())
        self.statusBar().showMessage(RODAPE)


def mostrar_erro_inesperado(tipo, valor, tb) -> None:
    """Bug não vira traceback na tela: o detalhe vai para o terminal e a tela mostra uma caixa."""
    traceback.print_exception(tipo, valor, tb)
    try:
        QMessageBox.critical(
            None,
            "Erro inesperado",
            f"{tipo.__name__}: {valor}\n\nO detalhe completo saiu no terminal.",
        )
    except Exception:  # noqa: BLE001 — se nem a caixa de erro abre, resta o terminal
        pass


def main() -> None:
    """Abre a janela do statlab."""
    sessao.preparar_webengine()  # antes da QApplication existir, como o Qt exige
    app = QApplication(sys.argv)
    app.setApplicationName(TITULO)
    sys.excepthook = mostrar_erro_inesperado
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
