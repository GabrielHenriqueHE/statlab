"""Peças comuns dos diálogos de comando.

Só interface: escolher variáveis, opções e nível de confiança, rodar o núcleo e mandar a saída para
a janela de sessão. Nenhuma regra estatística mora aqui.

O corpo de cada comando é desenhado pelo ``DialogoComando``, que o chama de novo a cada mudança de
opção (ver ``formulario.py``). Os helpers abaixo são os mesmos de sempre: quem chama não sabe se o
widget é do Qt ou de outra coisa.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from plotly import graph_objects as go
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from statlab.core import tabela as tab_mod
from statlab.core.dados import ErroDeDados, amostra
from statlab.core.descritiva import detectar_outliers, sem_extremos
from statlab.core.formatacao import num
from statlab.core.resultados import ATENCAO, FALHA, OK
from statlab.relatorio import ItemRelatorio, item_de
from statlab.ui import estado
from statlab.ui.comandos import formulario as st

ICONES = {OK: "✅", ATENCAO: "⚠️", FALHA: "❌"}
ALTERNATIVAS = {"Diferente (bilateral)": "bilateral", "Maior (unilateral)": "maior", "Menor (unilateral)": "menor"}
MODO_COLUNAS = "Uma coluna por grupo"
MODO_EMPILHADO = "Resposta numa coluna e grupo em outra"


@dataclass(frozen=True)
class Comando:
    menu: str  # "Estat"
    grupo: str  # "Estatísticas básicas" (submenu); "" = direto no menu
    nome: str  # "2 amostras (t)"
    abrir: Callable[[], None]  # abre o diálogo modal do comando
    corpo: Callable[[], None]  # o corpo que desenha as opções (os testes abrem o diálogo com ele)


COMANDOS: list[Comando] = []


def _apagar(layout) -> None:
    """Descarta os widgets de um layout (a área de conteúdo é refeita a cada desenho).

    Os sinais são bloqueados antes de soltar o widget: um sinal emitido na saída agendaria outro
    desenho, e o ciclo não terminaria.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.blockSignals(True)
            widget.setParent(None)
            widget.deleteLater()
            continue
        interno = item.layout()
        if interno is not None:
            _apagar(interno)
            interno.deleteLater()


class DialogoComando(QDialog):
    """O diálogo de um comando: área de opções redesenhável + botões fixos, como no Minitab.

    A área de opções é refeita por inteiro a cada mudança (é o corpo do comando que a desenha).
    Os botões ficam fora dela, então nunca somem no meio de uma interação.
    """

    def __init__(self, nome: str, corpo: Callable[[], None], pai: QWidget | None = None) -> None:
        super().__init__(pai)
        self.setWindowTitle(nome)
        self.setModal(True)
        self.resize(620, 560)
        self._corpo = corpo

        fora = QVBoxLayout(self)

        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        area = QWidget()
        self._conteudo = QVBoxLayout(area)
        self._conteudo.setAlignment(Qt.AlignTop)
        rolagem.setWidget(area)
        fora.addWidget(rolagem, 1)

        #: Mensagem de erro de dados da última execução ("" quando não houve).
        self.ultimo_erro = ""
        self.aviso_erro = QLabel()
        self.aviso_erro.setWordWrap(True)
        self.aviso_erro.setStyleSheet(st.ESTILOS["error"])
        self.aviso_erro.setVisible(False)
        fora.addWidget(self.aviso_erro)

        botoes = QDialogButtonBox()
        self._ok = botoes.addButton("Executar", QDialogButtonBox.AcceptRole)
        self._cancelar = botoes.addButton("Cancelar", QDialogButtonBox.RejectRole)
        self._ok.setDefault(True)
        self._ok.clicked.connect(self.executar)
        self._cancelar.clicked.connect(self.reject)
        fora.addWidget(botoes)

        self.encerrado = False
        self.formulario = st.Formulario(self._conteudo, self, self.desenhar)
        self.desenhar()

    def done(self, resultado: int) -> None:
        """Fechou (Executar ou Cancelar): nenhum desenho atrasado pode rodar depois disto."""
        self.encerrado = True
        super().done(resultado)

    def desenhar(self) -> None:
        """Roda o corpo do comando outra vez, refazendo a área de opções com os valores atuais."""
        if self.encerrado:
            return
        _apagar(self._conteudo)
        self.formulario.iniciar()
        marca = st.ATUAL.set(self.formulario)
        try:
            self._corpo()
        finally:
            st.ATUAL.reset(marca)
        self._ok.setText(self.formulario.rotulo_acao)
        self._ok.setEnabled(self.formulario.acao is not None)

    def executar(self) -> None:
        """Roda o comando e manda a saída para a sessão. Erro de dados não fecha o diálogo."""
        self.ultimo_erro = ""
        self.aviso_erro.setVisible(False)
        self.formulario.sincronizar()
        self.desenhar()  # o corpo roda com o que está nos widgets agora
        acao = self.formulario.acao
        if acao is None:
            return
        try:
            saida = acao()
        except ErroDeDados as exc:
            self.ultimo_erro = str(exc)
            self.aviso_erro.setText(f"❌ {exc}")
            self.aviso_erro.setVisible(True)
            return
        if saida is not None:
            itens = [saida] if isinstance(saida, ItemRelatorio) else list(saida)
            estado.registrar(*itens)
        self.accept()


def comando(menu: str, grupo: str, nome: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
    """Registra um comando no menu; abri-lo é abrir o diálogo modal com o corpo decorado."""

    def decorar(fn: Callable[[], None]) -> Callable[[], None]:
        def abrir() -> None:
            DialogoComando(nome, fn, QApplication.activeWindow()).exec()

        COMANDOS.append(Comando(menu=menu, grupo=grupo, nome=nome, abrir=abrir, corpo=fn))
        return fn

    return decorar


# --------------------------------------------------------------------------- dados de entrada


def worksheet() -> tuple[str, pd.DataFrame] | None:
    """A worksheet ativa, ou None (com aviso na tela) quando não há nenhuma."""
    ativa = estado.ativa()
    if ativa is None:
        st.info("Não há worksheet aberta. Use **Dados › Abrir arquivo** ou **Dados › Colar dados**.")
        return None
    return ativa


def numericas(df: pd.DataFrame, minimo: int = 1) -> list[str] | None:
    cols = tab_mod.colunas_numericas(df)
    if len(cols) < minimo:
        st.warning(f"Esta análise precisa de pelo menos {minimo} coluna(s) numérica(s) na worksheet.")
        return None
    return cols


def escolher_coluna(df: pd.DataFrame, rotulo: str, chave: str, *, indice: int = 0) -> str | None:
    cols = numericas(df)
    if not cols:
        return None
    return st.selectbox(rotulo, cols, index=min(indice, len(cols) - 1), key=chave)


def escolher_variaveis(df: pd.DataFrame, rotulo: str, chave: str, *, padrao: int = 1) -> list[str]:
    cols = numericas(df) or []
    return st.multiselect(rotulo, cols, default=cols[:padrao], key=chave)


def limpar(valores, nome: str) -> tuple[np.ndarray, list[str]]:
    """Converte uma coluna em array, descartando faltantes e reportando quantos (regra 12)."""
    v, faltantes = amostra(valores, nome)
    notas = [f"{nome}: {faltantes} valor(es) faltante(s) descartado(s); n = {len(v)}."] if faltantes else []
    return v, notas


def escolher_grupos(
    df: pd.DataFrame, chave: str, *, minimo: int = 2, maximo: int | None = None
) -> tuple[dict[str, np.ndarray], list[str]] | None:
    """Escolha dos grupos como no Minitab: colunas separadas ou resposta + coluna de grupos.

    Devolve ``(grupos, notas)`` com os faltantes já descartados e contabilizados, ou None quando a
    escolha ainda está incompleta.
    """
    cols = tab_mod.colunas_numericas(df)
    modo = st.radio("Como os dados estão organizados?", [MODO_COLUNAS, MODO_EMPILHADO], key=f"{chave}_modo")
    if modo == MODO_COLUNAS:
        padrao = cols[:maximo] if maximo is not None else cols
        escolhidas = st.multiselect(
            "Colunas (uma por grupo)", cols, default=padrao, key=f"{chave}_cols", max_selections=maximo
        )
        if len(escolhidas) < minimo:
            st.info(f"Escolha pelo menos {minimo} colunas.")
            return None
        brutos = {c: df[c] for c in escolhidas}
    else:
        outras = list(df.columns)
        if not cols or len(outras) < 2:
            st.info("A worksheet precisa de uma coluna numérica (resposta) e de outra com os grupos.")
            return None
        resposta = st.selectbox("Resposta (numérica)", cols, key=f"{chave}_resp")
        grupo = st.selectbox("Coluna com os grupos", [c for c in outras if c != resposta], key=f"{chave}_grupo")
        niveis = [str(n) for n in pd.unique(df[grupo].dropna())]
        if maximo is not None and len(niveis) > maximo:
            niveis = st.multiselect(
                f"Níveis a comparar ({maximo})",
                niveis,
                default=niveis[:maximo],
                key=f"{chave}_niveis",
                max_selections=maximo,
            )
        if len(niveis) < minimo:
            st.info(f"São necessários pelo menos {minimo} grupos (níveis) na coluna escolhida.")
            return None
        rotulos = df[grupo].astype(str)
        brutos = {n: df.loc[rotulos == n, resposta] for n in niveis}

    dados: dict[str, np.ndarray] = {}
    notas: list[str] = []
    for nome, serie in brutos.items():
        v, nota = limpar(serie, nome)
        dados[nome] = v
        notas += nota
    return dados, notas


# --------------------------------------------------------------------------- opções do diálogo


def confianca(chave: str) -> float:
    """Nível de confiança do comando (como no Minitab: opção do diálogo, não ajuste global)."""
    pct = st.number_input(
        "Nível de confiança (%)", min_value=50.0, max_value=99.99, value=95.0, step=1.0, key=chave, format="%.2f"
    )
    return float(pct) / 100.0


def alpha_de(conf: float) -> float:
    return round(1.0 - conf, 10)


def alternativa(chave: str, descricao_maior: str, descricao_menor: str) -> str:
    rotulos = {
        "Diferente (bilateral)": "Diferente (bilateral)",
        "Maior (unilateral)": f"Maior: {descricao_maior}",
        "Menor (unilateral)": f"Menor: {descricao_menor}",
    }
    escolha = st.radio(
        "Hipótese alternativa (H₁)", list(ALTERNATIVAS), format_func=rotulos.get, key=chave, horizontal=True
    )
    return ALTERNATIVAS[escolha]


def excluir_extremos(chave: str) -> bool:
    """Opção explícita de excluir outliers extremos. Desmarcada por padrão: o app não mexe nos dados."""
    return st.checkbox(
        "Excluir outliers extremos (fora de Q1 − 3D / Q3 + 3D) antes de calcular",
        value=False,
        key=chave,
        help="Desmarcado, a análise usa todos os valores recebidos.",
    )


def aplicar_exclusao(amostras: dict[str, np.ndarray], excluir: bool) -> tuple[dict[str, np.ndarray], list[str]]:
    """Aplica (ou não) a exclusão de extremos, devolvendo as amostras e as notas de n antes/depois."""
    if not excluir:
        return amostras, []
    saida: dict[str, np.ndarray] = {}
    notas: list[str] = []
    for nome, v in amostras.items():
        v = np.asarray(v, dtype=float)
        v = v[~np.isnan(v)]
        out = detectar_outliers(v)
        limpo = sem_extremos(v, out)
        saida[nome] = limpo
        if len(limpo) != len(v):
            fora = ", ".join(num(x) for x in v[out.extremo])
            notas.append(
                f"{nome}: {len(v) - len(limpo)} outlier(s) extremo(s) excluído(s) ({fora}); "
                f"n = {len(limpo)} (antes: {len(v)})."
            )
        else:
            notas.append(f"{nome}: nenhum outlier extremo; n = {len(limpo)}.")
    return saida, notas


# --------------------------------------------------------------------------- saída


def rodar(fn: Callable[[], ItemRelatorio | Sequence[ItemRelatorio] | None], rotulo: str = "Executar") -> None:
    """Diz ao diálogo o que o botão de executar roda e como ele se chama.

    Como no Minitab, o diálogo só fecha por um dos dois botões (ver ``DialogoComando.executar``).
    """
    st.registrar_acao(fn, rotulo)


def item_simples(
    titulo: str,
    *,
    comando_nome: str = "",
    linhas: Sequence[str] = (),
    tabelas: Sequence[tuple[str, pd.DataFrame]] = (),
    notas: Sequence[str] = (),
    figuras: Sequence[go.Figure] = (),
) -> ItemRelatorio:
    """Bloco de sessão para comandos que não devolvem um ``Resultado`` (dados, gráficos, descritivas)."""
    return ItemRelatorio(
        titulo=titulo,
        teste=comando_nome,
        resultado=list(linhas),
        tabelas=list(tabelas),
        avisos=list(notas),
        figuras=list(figuras),
    )


def item_de_resultado(res, titulo: str, *, notas: Sequence[str] = (), figuras: Sequence[go.Figure] = ()):
    """Bloco de sessão a partir de um ``Resultado``, com notas extras do comando."""
    item = item_de(res, titulo=titulo, figuras=figuras)
    item.avisos = [*notas, *item.avisos]
    return item
