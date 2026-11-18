"""Estado do app: as worksheets abertas (como no Minitab) e a janela de sessão.

As funções de módulo são as mesmas de antes (``planilhas()``, ``nova_planilha()``, ``ativa()``, …):
os comandos não sabem que por baixo existe um ``QObject`` com Signals. Quem desenha a tela se
inscreve nos Signals de ``atual()`` para se redesenhar.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QObject, Signal

from statlab.relatorio import ItemRelatorio


class Estado(QObject):
    """As worksheets e a sessão de uma execução do app."""

    worksheets_mudaram = Signal()  # criou/removeu worksheet
    ativa_mudou = Signal(str)  # outra worksheet passou a ser a ativa
    sessao_mudou = Signal()  # entrou/saiu bloco da janela de sessão

    def __init__(self) -> None:
        super().__init__()
        self._planilhas: dict[str, pd.DataFrame] = {}
        self._ativa: str | None = None
        self._sessao: list[ItemRelatorio] = []

    # ----------------------------------------------------------------- worksheets
    def planilhas(self) -> dict[str, pd.DataFrame]:
        return self._planilhas

    def nome_unico(self, base: str) -> str:
        base = (base or "Worksheet").strip() or "Worksheet"
        if base not in self._planilhas:
            return base
        k = 2
        while f"{base} ({k})" in self._planilhas:
            k += 1
        return f"{base} ({k})"

    def nova_planilha(self, nome: str, df: pd.DataFrame) -> str:
        final = self.nome_unico(nome)
        self._planilhas[final] = df
        self._ativa = final
        self.worksheets_mudaram.emit()
        self.ativa_mudou.emit(final)
        return final

    def salvar(self, nome: str, df: pd.DataFrame) -> None:
        self._planilhas[nome] = df

    def ativa(self) -> tuple[str, pd.DataFrame] | None:
        """Worksheet ativa como ``(nome, tabela)``; None se não há nenhuma aberta."""
        if not self._planilhas:
            return None
        nome = self._ativa
        if nome not in self._planilhas:
            nome = next(iter(self._planilhas))
            self._ativa = nome
        return nome, self._planilhas[nome]

    def ativa_set(self, nome: str) -> None:
        if nome in self._planilhas and nome != self._ativa:
            self._ativa = nome
            self.ativa_mudou.emit(nome)

    # -------------------------------------------------------------- janela de sessão
    def sessao(self) -> list[ItemRelatorio]:
        """Saídas acumuladas dos comandos, na ordem em que foram executados."""
        return self._sessao

    def registrar(self, *itens: ItemRelatorio) -> None:
        self._sessao.extend(itens)
        self.sessao_mudou.emit()

    def limpar_sessao(self) -> None:
        self._sessao = []
        self.sessao_mudou.emit()

    def remover_da_sessao(self, indice: int) -> None:
        if 0 <= indice < len(self._sessao):
            del self._sessao[indice]
            self.sessao_mudou.emit()


# --------------------------------------------------------------------- instância do processo

_ATUAL: Estado | None = None


def set_estado(novo: Estado) -> None:
    """Troca o estado do processo (a janela faz isso ao abrir; os testes, a cada caso)."""
    global _ATUAL
    _ATUAL = novo


def atual() -> Estado:
    """O estado do processo, criado na primeira vez que alguém pede."""
    global _ATUAL
    if _ATUAL is None:
        _ATUAL = Estado()
    return _ATUAL


# --------------------------------------------------------------------- API de módulo


def planilhas() -> dict[str, pd.DataFrame]:
    return atual().planilhas()


def nome_unico(base: str) -> str:
    return atual().nome_unico(base)


def nova_planilha(nome: str, df: pd.DataFrame) -> str:
    return atual().nova_planilha(nome, df)


def salvar(nome: str, df: pd.DataFrame) -> None:
    atual().salvar(nome, df)


def ativa() -> tuple[str, pd.DataFrame] | None:
    return atual().ativa()


def ativa_set(nome: str) -> None:
    atual().ativa_set(nome)


def sessao() -> list[ItemRelatorio]:
    return atual().sessao()


def registrar(*itens: ItemRelatorio) -> None:
    atual().registrar(*itens)


def limpar_sessao() -> None:
    atual().limpar_sessao()


def remover_da_sessao(indice: int) -> None:
    atual().remover_da_sessao(indice)
