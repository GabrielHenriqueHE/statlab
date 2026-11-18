"""A janela de sessão: a saída acumulada dos comandos, em abas, como no Minitab.

Cada bloco é um ``ItemRelatorio`` desenhado aqui — título, tabelas, linhas de resultado,
diagnósticos, notas, figuras e o cálculo. Nenhuma conclusão é redigida: interpretar é do usuário.

As figuras continuam sendo as mesmas do Plotly; o visualizador é um ``QWebEngineView`` com uma cópia
local do ``plotly.min.js`` (nada de CDN). Como cada visualizador embute um Chromium, a figura só é
criada quando a aba aparece.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from statlab.graficos import exportar
from statlab.relatorio import ItemRelatorio, para_html, para_markdown
from statlab.ui import estado
from statlab.ui.comandos.formulario import ESTILOS, markdown_para_html
from statlab.ui.grade import GradeModel

#: Se o visualizador de gráficos do Qt está disponível (ver ``preparar_webengine``).
WEBENGINE = False

_PASTA_PLOTLY: Path | None = None
ALTURA_TABELA = 320


def preparar_webengine() -> bool:
    """Importa o QtWebEngine **antes** da ``QApplication`` existir, como o Qt exige.

    Devolve se o visualizador está disponível; sem ele, cada figura ganha um botão que abre o
    gráfico no navegador.
    """
    global WEBENGINE
    try:
        import PySide6.QtWebEngineWidgets  # noqa: F401  (o import é o que habilita o visualizador)
    except ImportError:
        WEBENGINE = False
    else:
        WEBENGINE = True
    return WEBENGINE


def pasta_plotly() -> Path:
    """Diretório temporário com uma cópia do ``plotly.min.js``, escrita uma única vez."""
    global _PASTA_PLOTLY
    if _PASTA_PLOTLY is None:
        from plotly.offline import get_plotlyjs

        pasta = Path(tempfile.mkdtemp(prefix="statlab_graficos_"))
        (pasta / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
        _PASTA_PLOTLY = pasta
    return _PASTA_PLOTLY


class Grafico(QWidget):
    """Uma figura Plotly; o visualizador nasce na primeira vez que a aba é mostrada."""

    def __init__(self, fig) -> None:
        super().__init__()
        self._fig = fig
        self._pronto = False
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumHeight(380)

    def showEvent(self, event) -> None:  # noqa: N802 — nome do Qt
        super().showEvent(event)
        if self._pronto:
            return
        self._pronto = True
        self._layout.addWidget(self._visualizador())

    def _visualizador(self) -> QWidget:
        if not WEBENGINE:
            return self._sem_visualizador()
        from PySide6.QtWebEngineWidgets import QWebEngineView

        pasta = pasta_plotly()
        vista = QWebEngineView()
        vista.setHtml(
            self._fig.to_html(include_plotlyjs="plotly.min.js", full_html=True),
            QUrl.fromLocalFile(f"{pasta}/"),
        )
        return vista

    def _sem_visualizador(self) -> QWidget:
        caixa = QWidget()
        layout = QVBoxLayout(caixa)
        aviso = QLabel(
            "O visualizador de gráficos do Qt (QtWebEngine) não está disponível neste sistema. "
            "O gráfico abre no navegador."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet(ESTILOS["warning"])
        botao = QPushButton("Abrir gráfico no navegador")
        botao.clicked.connect(self._abrir_no_navegador)
        layout.addWidget(aviso)
        layout.addWidget(botao)
        layout.addStretch()
        return caixa

    def _abrir_no_navegador(self) -> None:
        arquivo = Path(tempfile.mkdtemp(prefix="statlab_grafico_")) / "grafico.html"
        arquivo.write_bytes(exportar.html(self._fig))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(arquivo)))


def _etiqueta(texto: str, *, estilo: str = "", formato=Qt.RichText) -> QLabel:
    etiqueta = QLabel(texto)
    etiqueta.setTextFormat(formato)
    etiqueta.setWordWrap(True)
    if estilo:
        etiqueta.setStyleSheet(estilo)
    return etiqueta


def bloco(item: ItemRelatorio) -> QWidget:
    """Desenha um bloco de sessão (o conteúdo de uma aba)."""
    conteudo = QWidget()
    layout = QVBoxLayout(conteudo)
    layout.setAlignment(Qt.AlignTop)

    cabecalho = f"<b>{markdown_para_html(item.titulo)}</b>"
    if item.teste and item.teste != item.titulo:
        cabecalho += f"  ·  {markdown_para_html(item.teste)}"
    layout.addWidget(_etiqueta(cabecalho))
    layout.addWidget(
        _etiqueta(item.criado_em.strftime("%H:%M:%S"), estilo="color: gray; font-size: 11px;")
    )

    for nome, tabela in item.tabelas:
        layout.addWidget(_etiqueta(f"<i>{markdown_para_html(nome)}</i>"))
        vista = QTableView()
        model = GradeModel(tabela, editavel=False)
        model.setParent(vista)  # sem dono, o model é coletado e a view fica sem dados
        vista.setModel(model)
        vista.verticalHeader().setVisible(False)
        vista.setMaximumHeight(ALTURA_TABELA)
        layout.addWidget(vista)

    for linha in item.resultado:
        layout.addWidget(_etiqueta(f"• {markdown_para_html(linha)}"))

    if item.verificacoes:
        layout.addWidget(_etiqueta("<i>Diagnósticos</i>"))
        for icone, nome, detalhe in item.verificacoes:
            layout.addWidget(
                _etiqueta(f"{icone} <b>{markdown_para_html(nome)}</b> — {markdown_para_html(detalhe)}")
            )

    for aviso in item.avisos:
        layout.addWidget(_etiqueta(f"ℹ️ {markdown_para_html(aviso)}", estilo=ESTILOS["warning"]))

    for fig in item.figuras:
        layout.addWidget(Grafico(fig))

    if item.passos:
        botao = QPushButton("Cálculo")
        botao.setCheckable(True)
        detalhe = _etiqueta("\n".join(item.passos), formato=Qt.PlainText, estilo="font-family: monospace;")
        detalhe.setVisible(False)
        botao.toggled.connect(detalhe.setVisible)
        layout.addWidget(botao)
        layout.addWidget(detalhe)

    rolagem = QScrollArea()
    rolagem.setWidgetResizable(True)
    rolagem.setWidget(conteudo)
    return rolagem


def rotulo_da_aba(indice: int, item: ItemRelatorio) -> str:
    rotulo = f"{indice + 1}. {item.teste or item.titulo}"
    return rotulo if len(rotulo) <= 50 else rotulo[:47] + "..."


class PainelSessao(QWidget):
    """A janela de sessão: abas com a saída dos comandos, mais limpar e exportar."""

    def __init__(self) -> None:
        super().__init__()
        fora = QVBoxLayout(self)
        fora.setContentsMargins(6, 6, 6, 6)

        topo = QHBoxLayout()
        topo.addWidget(_etiqueta("<b>Sessão</b>"))
        topo.addStretch()
        self.botao_html = QPushButton("Exportar HTML")
        self.botao_md = QPushButton("Exportar Markdown")
        self.botao_limpar = QPushButton("Limpar")
        self.botao_html.clicked.connect(self._exportar_html)
        self.botao_md.clicked.connect(self._exportar_markdown)
        self.botao_limpar.clicked.connect(estado.limpar_sessao)
        for botao in (self.botao_html, self.botao_md, self.botao_limpar):
            topo.addWidget(botao)
        fora.addLayout(topo)

        self.aviso_vazio = _etiqueta(
            "A saída dos comandos aparece aqui. Comece pelo menu <b>Dados</b>.",
            estilo="color: gray; padding: 12px;",
        )
        self.abas = QTabWidget()
        self.abas.setTabsClosable(True)
        self.abas.setMovable(True)
        self.abas.tabCloseRequested.connect(estado.remover_da_sessao)
        fora.addWidget(self.aviso_vazio)
        fora.addWidget(self.abas, 1)

        self._desenhados: list[ItemRelatorio] = []
        estado.atual().sessao_mudou.connect(self.redesenhar)
        self.redesenhar()

    # ------------------------------------------------------------------ desenho
    def redesenhar(self) -> None:
        """Acompanha a sessão: se só entraram blocos no fim, acrescenta abas em vez de refazer todas."""
        itens = estado.sessao()
        acrescentou = len(itens) > len(self._desenhados) and all(
            a is b for a, b in zip(self._desenhados, itens[: len(self._desenhados)], strict=False)
        )
        if acrescentou:
            for i in range(len(self._desenhados), len(itens)):
                self.abas.addTab(bloco(itens[i]), rotulo_da_aba(i, itens[i]))
            self.abas.setCurrentIndex(len(itens) - 1)
        else:
            atual = self.abas.currentIndex()
            for i in range(self.abas.count()):  # clear() não apaga as páginas antigas
                self.abas.widget(i).deleteLater()
            self.abas.clear()
            for i, item in enumerate(itens):
                self.abas.addTab(bloco(item), rotulo_da_aba(i, item))
            if itens:
                self.abas.setCurrentIndex(min(max(atual, 0), len(itens) - 1))

        self._desenhados = list(itens)
        tem = bool(itens)
        self.aviso_vazio.setVisible(not tem)
        self.abas.setVisible(tem)
        for botao in (self.botao_html, self.botao_md, self.botao_limpar):
            botao.setEnabled(tem)

    # ------------------------------------------------------------------ exportação
    def _exportar(self, titulo: str, sugestao: str, filtro: str, conteudo: str) -> None:
        caminho, _ = QFileDialog.getSaveFileName(self, titulo, sugestao, filtro)
        if not caminho:
            return
        try:
            Path(caminho).write_text(conteudo, encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Não foi possível salvar", str(exc))
            return
        QMessageBox.information(self, "Sessão exportada", f"Arquivo salvo em:\n{caminho}")

    def _exportar_html(self) -> None:
        self._exportar(
            "Exportar sessão em HTML",
            "sessao_statlab.html",
            "Página HTML (*.html)",
            para_html(estado.sessao()),
        )

    def _exportar_markdown(self) -> None:
        self._exportar(
            "Exportar sessão em Markdown",
            "sessao_statlab.md",
            "Markdown (*.md)",
            para_markdown(estado.sessao()),
        )
