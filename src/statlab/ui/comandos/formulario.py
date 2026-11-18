"""O formulário de um diálogo de comando, com o mesmo modelo de rerun que os comandos já usavam.

Cada comando é uma função que **desenha o diálogo inteiro** e sai cedo (``return``) enquanto a
escolha do usuário está incompleta. Isso vem do Streamlit, que reexecuta a função a cada
interação. Para não reescrever os ~44 comandos, este módulo refaz o mesmo contrato dentro de um
``QDialog``:

* cada widget é identificado pela ``key=`` que o comando já passava;
* o valor que o usuário escolheu fica guardado por ``key``, e é ele (não o ``default`` do código)
  que o widget mostra na reconstrução seguinte — é o papel do ``session_state``;
* mexer num widget que ramifica a tela (combo, radio, checkbox, lista) agenda uma reconstrução
  completa da área de conteúdo, que chama a função do comando outra vez.

Os comandos importam este módulo como ``st``, então as assinaturas abaixo imitam as do Streamlit.
Quem desenha a área e dispara a reconstrução é o ``DialogoComando`` (``_base.py``).
"""

from __future__ import annotations

import contextvars
import html
import re
from collections.abc import Callable, Iterable, Sequence
from functools import partial
from pathlib import Path
from typing import Any

import pandas as pd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QBoxLayout,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from statlab.ui.grade import GradeModel

#: O formulário que está sendo desenhado. Uso deliberado e restrito a este framework: é o que
#: permite ``st.selectbox(...)`` funcionar dentro do corpo do comando sem passar o diálogo adiante.
ATUAL: contextvars.ContextVar[Formulario | None] = contextvars.ContextVar("formulario", default=None)

ESTILOS = {
    "info": "background: rgba(80,140,220,0.18); border-radius: 4px; padding: 6px;",
    "warning": "background: rgba(230,170,40,0.22); border-radius: 4px; padding: 6px;",
    "success": "background: rgba(70,180,110,0.20); border-radius: 4px; padding: 6px;",
    "error": "background: rgba(220,80,80,0.22); border-radius: 4px; padding: 6px;",
}
ICONES_MENSAGEM = {"info": "ℹ️", "warning": "⚠️", "success": "✅", "error": "❌"}
ALTURA_TABELA = 260


class Arquivo:
    """O arquivo escolhido, com a interface mínima que os comandos usam (``name``/``getvalue``)."""

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self.name = self.caminho.name

    def getvalue(self) -> bytes:
        return self.caminho.read_bytes()


def markdown_para_html(texto: str) -> str:
    """Converte o pouco de Markdown que os comandos usam (negrito, itálico, código, bullet)."""
    saida = html.escape(str(texto))
    saida = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", saida)
    saida = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", saida)
    saida = re.sub(r"`(.+?)`", r"<code>\1</code>", saida)
    if saida.startswith("- "):
        saida = "• " + saida[2:]
    return saida


def _mesmo(a: object, b: object) -> bool:
    try:
        return bool(a == b)
    except Exception:  # noqa: BLE001 — comparação de tipos exóticos não pode derrubar a tela
        return False


def _indice_de(opcoes: Sequence[Any], valor: object) -> int | None:
    for i, o in enumerate(opcoes):
        if _mesmo(o, valor):
            return i
    return None


class Coluna:
    """Uma das colunas de ``st.columns``: encaminha os widgets para o seu próprio layout."""

    def __init__(self, formulario: Formulario, layout: QBoxLayout) -> None:
        self._formulario = formulario
        self._layout = layout

    def __getattr__(self, nome: str) -> Callable[..., Any]:
        metodo = getattr(self._formulario, nome)
        return partial(metodo, destino=self._layout)


class Formulario:
    """Os widgets de um diálogo e os valores que o usuário escolheu, por ``key``."""

    def __init__(self, destino: QVBoxLayout, pai: QWidget, reconstruir: Callable[[], None]) -> None:
        self._destino = destino
        self._pai = pai
        self._reconstruir = reconstruir
        self._valores: dict[str, Any] = {}
        self._leitores: dict[str, Callable[[], Any]] = {}
        self._rebuild_agendado = False
        self.acao: Callable[[], Any] | None = None
        self.rotulo_acao = "Executar"
        #: Todo rótulo e mensagem desenhados nesta passada, na ordem (o que o diálogo está mostrando).
        self.textos: list[str] = []

    # ---------------------------------------------------------------- ciclo de desenho
    def iniciar(self) -> None:
        """Começa uma passada de desenho: os widgets antigos já foram descartados pelo diálogo."""
        self._leitores.clear()
        self.textos.clear()
        self.acao = None
        self.rotulo_acao = "Executar"

    def definir_valor(self, chave: str, valor: Any) -> None:
        """Marca uma opção de fora (é o que os testes usam) e redesenha o diálogo na hora."""
        self._valores[chave] = valor
        self._reconstruir()

    def sincronizar(self) -> None:
        """Lê o valor atual de cada widget vivo (texto digitado sem sair do campo, por exemplo)."""
        for chave, leitor in list(self._leitores.items()):
            try:
                self._valores[chave] = leitor()
            except RuntimeError:
                self._leitores.pop(chave, None)  # widget já destruído

    def agendar_rebuild(self) -> None:
        """Reconstrói a área de conteúdo depois de sair do tratador do sinal atual."""
        if self._rebuild_agendado:
            return
        self._rebuild_agendado = True
        QTimer.singleShot(0, self._rebuild)

    def _rebuild(self) -> None:
        self._rebuild_agendado = False
        self.sincronizar()
        self._reconstruir()

    # ---------------------------------------------------------------- utilidades internas
    def _onde(self, destino: QBoxLayout | None) -> QBoxLayout:
        return destino if destino is not None else self._destino

    def _por(self, widget: QWidget, destino: QBoxLayout | None) -> QWidget:
        self._onde(destino).addWidget(widget)
        return widget

    def _rotulo(self, texto: str, destino: QBoxLayout | None) -> None:
        if not texto:
            return
        self.textos.append(str(texto))
        etiqueta = QLabel(markdown_para_html(texto))
        etiqueta.setTextFormat(Qt.RichText)
        etiqueta.setWordWrap(True)
        self._por(etiqueta, destino)

    def _guardar(self, chave: str, valor: Any, leitor: Callable[[], Any]) -> Any:
        self._valores[chave] = valor
        if chave:
            self._leitores[chave] = leitor
        return valor

    def _lembrado(self, chave: str, padrao: Any) -> Any:
        return self._valores[chave] if chave in self._valores else padrao

    # ---------------------------------------------------------------- mensagens
    def _mensagem(self, texto: str, tipo: str, destino: QBoxLayout | None) -> None:
        self.textos.append(str(texto))
        etiqueta = QLabel(f"{ICONES_MENSAGEM[tipo]} {markdown_para_html(texto)}")
        etiqueta.setTextFormat(Qt.RichText)
        etiqueta.setWordWrap(True)
        etiqueta.setStyleSheet(ESTILOS[tipo])
        self._por(etiqueta, destino)

    def info(self, texto: str, *, destino: QBoxLayout | None = None) -> None:
        self._mensagem(texto, "info", destino)

    def warning(self, texto: str, *, icon: str | None = None, destino: QBoxLayout | None = None) -> None:
        self._mensagem(texto, "warning", destino)

    def success(self, texto: str, *, destino: QBoxLayout | None = None) -> None:
        self._mensagem(texto, "success", destino)

    def error(self, texto: str, *, destino: QBoxLayout | None = None) -> None:
        self._mensagem(texto, "error", destino)

    def markdown(self, texto: str, *, destino: QBoxLayout | None = None) -> None:
        self._rotulo(texto, destino)

    def text(self, texto: str, *, destino: QBoxLayout | None = None) -> None:
        etiqueta = QLabel(str(texto))
        etiqueta.setTextFormat(Qt.PlainText)
        etiqueta.setWordWrap(True)
        self._por(etiqueta, destino)

    def caption(self, texto: str, *, destino: QBoxLayout | None = None) -> None:
        etiqueta = QLabel(markdown_para_html(texto))
        etiqueta.setTextFormat(Qt.RichText)
        etiqueta.setWordWrap(True)
        etiqueta.setStyleSheet("color: gray; font-size: 11px;")
        self._por(etiqueta, destino)

    def rerun(self) -> None:
        """No Qt não existe rerun: a reconstrução já acontece por conta do widget alterado."""
        return None

    # ---------------------------------------------------------------- layout
    def columns(self, quantas: int | Sequence[float], *, destino: QBoxLayout | None = None) -> list[Coluna]:
        pesos = [1] * quantas if isinstance(quantas, int) else [float(p) for p in quantas]
        caixa = QWidget()
        linha = QHBoxLayout(caixa)
        linha.setContentsMargins(0, 0, 0, 0)
        colunas = []
        for peso in pesos:
            interna = QVBoxLayout()
            interna.setContentsMargins(0, 0, 0, 0)
            linha.addLayout(interna, int(peso * 10) or 1)
            colunas.append(Coluna(self, interna))
        self._por(caixa, destino)
        return colunas

    # ---------------------------------------------------------------- widgets de escolha
    def selectbox(
        self,
        rotulo: str,
        opcoes: Iterable[Any],
        *,
        index: int = 0,
        key: str = "",
        format_func: Callable[[Any], str] | None = None,
        destino: QBoxLayout | None = None,
    ) -> Any:
        opcoes = list(opcoes)
        self._rotulo(rotulo, destino)
        combo = QComboBox()
        for opcao in opcoes:
            texto = format_func(opcao) if format_func else opcao
            combo.addItem(str(opcao if texto is None else texto), opcao)
        if not opcoes:
            combo.setEnabled(False)
            self._por(combo, destino)
            return self._guardar(key, None, lambda: None)
        i = _indice_de(opcoes, self._lembrado(key, object()))
        if i is None:
            i = min(max(int(index), 0), len(opcoes) - 1)
        combo.setCurrentIndex(i)
        combo.currentIndexChanged.connect(lambda *_: self.agendar_rebuild())
        self._por(combo, destino)
        return self._guardar(key, opcoes[i], combo.currentData)

    def radio(
        self,
        rotulo: str,
        opcoes: Iterable[Any],
        *,
        index: int = 0,
        key: str = "",
        format_func: Callable[[Any], str] | None = None,
        horizontal: bool = False,
        destino: QBoxLayout | None = None,
    ) -> Any:
        opcoes = list(opcoes)
        self._rotulo(rotulo, destino)
        caixa = QWidget()
        layout: QBoxLayout = QHBoxLayout(caixa) if horizontal else QVBoxLayout(caixa)
        layout.setContentsMargins(8, 0, 0, 0)
        grupo = QButtonGroup(caixa)
        if not opcoes:
            self._por(caixa, destino)
            return self._guardar(key, None, lambda: None)
        i = _indice_de(opcoes, self._lembrado(key, object()))
        if i is None:
            i = min(max(int(index), 0), len(opcoes) - 1)
        for j, opcao in enumerate(opcoes):
            texto = format_func(opcao) if format_func else opcao
            botao = QRadioButton(str(opcao if texto is None else texto))
            botao.setChecked(j == i)
            grupo.addButton(botao, j)
            layout.addWidget(botao)
        if horizontal:
            layout.addStretch()
        grupo.idToggled.connect(lambda _id, marcado: self.agendar_rebuild() if marcado else None)
        self._por(caixa, destino)
        return self._guardar(key, opcoes[i], lambda: opcoes[grupo.checkedId()] if grupo.checkedId() >= 0 else None)

    def multiselect(
        self,
        rotulo: str,
        opcoes: Iterable[Any],
        default: Iterable[Any] | None = None,
        *,
        key: str = "",
        max_selections: int | None = None,
        destino: QBoxLayout | None = None,
    ) -> list[Any]:
        opcoes = list(opcoes)
        padrao = list(default) if default is not None else []
        lembrado = self._lembrado(key, padrao)
        marcados = [o for o in opcoes if _indice_de(list(lembrado), o) is not None]
        if max_selections is not None:
            marcados = marcados[:max_selections]

        rotulo_final = rotulo
        if max_selections is not None:
            rotulo_final = f"{rotulo} — no máximo {max_selections}"
        self._rotulo(rotulo_final, destino)

        lista = QListWidget()
        lista.setSelectionMode(QListWidget.NoSelection)
        for opcao in opcoes:
            item = QListWidgetItem(str(opcao))
            item.setData(Qt.UserRole, opcao)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if _indice_de(marcados, opcao) is not None else Qt.Unchecked)
            lista.addItem(item)
        altura = 24 * max(1, min(len(opcoes), 6)) + 8
        lista.setMaximumHeight(altura)
        lista.setMinimumHeight(min(altura, 80))

        def ler() -> list[Any]:
            return [
                lista.item(i).data(Qt.UserRole)
                for i in range(lista.count())
                if lista.item(i).checkState() == Qt.Checked
            ]

        def ao_marcar(item: QListWidgetItem) -> None:
            if (
                max_selections is not None
                and item.checkState() == Qt.Checked
                and len(ler()) > max_selections
            ):
                lista.blockSignals(True)
                item.setCheckState(Qt.Unchecked)
                lista.blockSignals(False)
                return
            self.agendar_rebuild()

        lista.itemChanged.connect(ao_marcar)
        self._por(lista, destino)
        return self._guardar(key, marcados, ler)

    def checkbox(
        self,
        rotulo: str,
        value: bool = False,
        *,
        help: str | None = None,  # noqa: A002 — assinatura do Streamlit
        key: str = "",
        destino: QBoxLayout | None = None,
    ) -> bool:
        marcado = bool(self._lembrado(key, value))
        caixa = QCheckBox(rotulo)
        caixa.setChecked(marcado)
        if help:
            caixa.setToolTip(help)
        caixa.toggled.connect(lambda *_: self.agendar_rebuild())
        self._por(caixa, destino)
        return self._guardar(key, marcado, caixa.isChecked)

    # ---------------------------------------------------------------- widgets de digitação
    def number_input(
        self,
        rotulo: str,
        *,
        min_value: float | int | None = None,
        max_value: float | int | None = None,
        value: float | int = 0.0,
        step: float | int | None = None,
        format: str | None = None,  # noqa: A002 — assinatura do Streamlit
        key: str = "",
        destino: QBoxLayout | None = None,
    ) -> float | int:
        def eh_int(v: object) -> bool:
            return isinstance(v, int) and not isinstance(v, bool)

        inteiro = all(eh_int(v) for v in (value, min_value, max_value, step) if v is not None)
        lembrado = self._lembrado(key, value)
        self._rotulo(rotulo, destino)

        if inteiro:
            campo_int = QSpinBox()
            campo_int.setRange(
                int(min_value) if min_value is not None else -(2**31),
                int(max_value) if max_value is not None else 2**31 - 1,
            )
            campo_int.setSingleStep(int(step) if step else 1)
            campo_int.setValue(int(lembrado))
            campo_int.valueChanged.connect(lambda v: self._valores.__setitem__(key, int(v)) if key else None)
            campo_int.editingFinished.connect(self.agendar_rebuild)
            self._por(campo_int, destino)
            return self._guardar(key, campo_int.value(), campo_int.value)

        decimais = 4
        if format:
            achou = re.search(r"\.(\d+)f", format)
            if achou:
                decimais = int(achou.group(1))
        campo = QDoubleSpinBox()
        campo.setDecimals(decimais)
        campo.setRange(
            float(min_value) if min_value is not None else -1e12,
            float(max_value) if max_value is not None else 1e12,
        )
        campo.setSingleStep(float(step) if step else 10.0**-min(decimais, 2))
        campo.setValue(float(lembrado))
        campo.valueChanged.connect(lambda v: self._valores.__setitem__(key, float(v)) if key else None)
        campo.editingFinished.connect(self.agendar_rebuild)
        self._por(campo, destino)
        return self._guardar(key, campo.value(), campo.value)

    def text_input(
        self,
        rotulo: str,
        value: str = "",
        *,
        key: str = "",
        destino: QBoxLayout | None = None,
    ) -> str:
        texto = str(self._lembrado(key, value))
        self._rotulo(rotulo, destino)
        campo = QLineEdit(texto)
        campo.textChanged.connect(lambda t: self._valores.__setitem__(key, t) if key else None)
        campo.editingFinished.connect(self.agendar_rebuild)
        self._por(campo, destino)
        return self._guardar(key, campo.text(), campo.text)

    def text_area(
        self,
        rotulo: str,
        value: str = "",
        *,
        height: int | None = None,
        key: str = "",
        destino: QBoxLayout | None = None,
    ) -> str:
        texto = str(self._lembrado(key, value))
        self._rotulo(rotulo, destino)
        campo = QPlainTextEdit()
        campo.setPlainText(texto)
        if height:
            campo.setMinimumHeight(int(height))
            campo.setMaximumHeight(int(height) * 2)
        campo.textChanged.connect(
            lambda: self._valores.__setitem__(key, campo.toPlainText()) if key else None
        )
        self._por(campo, destino)
        return self._guardar(key, campo.toPlainText(), campo.toPlainText)

    def file_uploader(
        self,
        rotulo: str,
        *,
        type: Sequence[str] = (),  # noqa: A002 — assinatura do Streamlit
        key: str = "",
        destino: QBoxLayout | None = None,
    ) -> Arquivo | None:
        caminho = self._lembrado(key, None)
        self._rotulo(rotulo, destino)
        caixa = QWidget()
        linha = QHBoxLayout(caixa)
        linha.setContentsMargins(0, 0, 0, 0)
        botao = QPushButton("Escolher arquivo…")
        nome = QLabel(Path(caminho).name if caminho else "nenhum arquivo escolhido")
        nome.setStyleSheet("color: gray;")
        linha.addWidget(botao)
        linha.addWidget(nome, 1)

        extensoes = " ".join(f"*.{e.lstrip('.')}" for e in type)
        filtro = f"Dados ({extensoes});;Todos os arquivos (*)" if extensoes else "Todos os arquivos (*)"

        def escolher() -> None:
            escolhido, _ = QFileDialog.getOpenFileName(self._pai, rotulo or "Abrir arquivo", "", filtro)
            if escolhido:
                self._valores[key] = escolhido
                self.agendar_rebuild()

        botao.clicked.connect(escolher)
        self._por(caixa, destino)
        self._valores[key] = caminho
        return Arquivo(caminho) if caminho else None

    # ---------------------------------------------------------------- tabelas
    def dataframe(
        self,
        df: pd.DataFrame,
        *,
        hide_index: bool = False,
        width: str | int | None = None,
        destino: QBoxLayout | None = None,
    ) -> None:
        model = GradeModel(df, editavel=False)
        tabela = QTableView()
        model.setParent(tabela)  # sem dono, o model é coletado e a view fica sem dados
        tabela.setModel(model)
        if hide_index:
            tabela.verticalHeader().setVisible(False)
        tabela.setMaximumHeight(ALTURA_TABELA)
        self._por(tabela, destino)

    def data_editor(
        self,
        df: pd.DataFrame,
        *,
        disabled: Sequence[str] = (),
        hide_index: bool = False,
        key: str = "",
        destino: QBoxLayout | None = None,
    ) -> pd.DataFrame:
        anterior = self._valores.get(key)
        mesma_forma = (
            isinstance(anterior, pd.DataFrame)
            and list(anterior.columns) == list(df.columns)
            and len(anterior) == len(df)
        )
        base = anterior if mesma_forma else df.copy()
        model = GradeModel(base, bloqueadas=disabled)
        tabela = QTableView()
        model.setParent(tabela)  # sem dono, o model é coletado e a view fica sem dados
        tabela.setModel(model)
        if hide_index:
            tabela.verticalHeader().setVisible(False)
        tabela.setMaximumHeight(ALTURA_TABELA)
        self._por(tabela, destino)
        return self._guardar(key, model.df(), model.df)

    # ---------------------------------------------------------------- ação do diálogo
    def registrar_acao(self, fn: Callable[[], Any], rotulo: str) -> None:
        """O que o botão de executar do diálogo roda nesta passada de desenho (ver ``_base.rodar``)."""
        self.acao = fn
        self.rotulo_acao = rotulo


# --------------------------------------------------------------------- API de módulo (como ``st``)


def atual() -> Formulario:
    form = ATUAL.get()
    if form is None:
        raise RuntimeError("widget de comando usado fora de um diálogo (formulario.ATUAL não está setado)")
    return form


def _encaminhar(nome: str) -> Callable[..., Any]:
    def chamar(*args: Any, **kwargs: Any) -> Any:
        return getattr(atual(), nome)(*args, **kwargs)

    chamar.__name__ = nome
    return chamar


info = _encaminhar("info")
warning = _encaminhar("warning")
success = _encaminhar("success")
error = _encaminhar("error")
markdown = _encaminhar("markdown")
text = _encaminhar("text")
caption = _encaminhar("caption")
rerun = _encaminhar("rerun")
columns = _encaminhar("columns")
selectbox = _encaminhar("selectbox")
radio = _encaminhar("radio")
multiselect = _encaminhar("multiselect")
checkbox = _encaminhar("checkbox")
number_input = _encaminhar("number_input")
text_input = _encaminhar("text_input")
text_area = _encaminhar("text_area")
file_uploader = _encaminhar("file_uploader")
dataframe = _encaminhar("dataframe")
data_editor = _encaminhar("data_editor")
registrar_acao = _encaminhar("registrar_acao")
