"""Helpers dos testes de interface (Qt).

Os diálogos são montados direto (``DialogoComando``), sem ``exec()`` — o modal bloquearia o teste.
Mexer numa opção é ``definir(dialogo, chave, valor)``: grava o valor da ``key`` e redesenha o
diálogo na hora, que é exatamente o que uma interação do usuário faz.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import QApplication

from statlab.relatorio import ItemRelatorio
from statlab.ui import estado
from statlab.ui.app import JanelaPrincipal
from statlab.ui.comandos import COMANDOS, Comando
from statlab.ui.comandos._base import DialogoComando


def qt() -> QApplication:
    """A QApplication do processo de teste (uma só; ver ``conftest`` para o modo sem tela)."""
    return QApplication.instance() or QApplication([])


def app(planilhas: dict[str, pd.DataFrame] | None = None) -> JanelaPrincipal:
    """Abre o app com as worksheets dadas (a primeira fica ativa), num estado novo."""
    qt()
    estado.set_estado(estado.Estado())
    for nome, df in (planilhas or {}).items():
        estado.nova_planilha(nome, df)
    if planilhas:
        estado.ativa_set(next(iter(planilhas)))
    return JanelaPrincipal()


def comando(menu: str, grupo: str, nome: str) -> Comando:
    for c in COMANDOS:
        if (c.menu, c.grupo, c.nome) == (menu, grupo, nome):
            return c
    raise AssertionError(f"comando {menu}/{grupo}/{nome} não existe")


def abrir(_contexto, menu: str, grupo: str, nome: str) -> DialogoComando:
    """Abre o diálogo de um comando de menu (o contexto só deixa a chamada parecida com o uso)."""
    cmd = comando(menu, grupo, nome)
    return DialogoComando(cmd.nome, cmd.corpo)


def definir(dialogo: DialogoComando, chave: str, valor) -> DialogoComando:
    """Marca uma opção do diálogo pela ``key`` do widget e redesenha."""
    dialogo.formulario.definir_valor(chave, valor)
    return dialogo


def textos(dialogo: DialogoComando) -> list[str]:
    """Os rótulos e mensagens que o diálogo está mostrando agora."""
    return dialogo.formulario.textos


def executar(dialogo: DialogoComando, rotulo: str = "Executar") -> DialogoComando:
    """Clica no botão que roda o comando."""
    assert dialogo.formulario.acao is not None, f"diálogo sem ação; mostrando: {textos(dialogo)}"
    assert dialogo.formulario.rotulo_acao == rotulo, (
        f"o botão é {dialogo.formulario.rotulo_acao!r}, não {rotulo!r}"
    )
    dialogo.executar()
    return dialogo


def sem_erros(dialogo: DialogoComando, esperando_mensagem: bool = False) -> None:
    """Nenhum erro de dados na última execução (com ``esperando_mensagem``, não checa)."""
    if not esperando_mensagem:
        assert dialogo.ultimo_erro == "", dialogo.ultimo_erro


def saida() -> list[ItemRelatorio]:
    """Os blocos acumulados na janela de sessão."""
    return estado.sessao()


def linhas_da_saida(indice: int = -1) -> str:
    item = saida()[indice]
    return "\n".join([*item.resultado, *item.avisos, *item.passos])


def worksheet(**colunas: list[float]) -> pd.DataFrame:
    """Colunas de tamanhos diferentes viram uma worksheet com faltantes no fim (como no Minitab)."""
    return pd.DataFrame({k: pd.Series(v, dtype=float) for k, v in colunas.items()})
