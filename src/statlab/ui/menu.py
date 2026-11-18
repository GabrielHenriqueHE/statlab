"""A barra de menus do statlab: ``QMenuBar`` nativo montado a partir de ``COMANDOS``/``MENUS``.

Um menu por entrada de ``MENUS``, um submenu em cascata por grupo de comando, na ordem em que os
comandos foram registrados (nada é reordenado aqui).
"""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar

from statlab.ui.comandos import COMANDOS, MENUS, Comando


def chave(comando: Comando) -> str:
    return f"{comando.menu}_{comando.grupo}_{comando.nome}"


def montar(barra: QMenuBar) -> dict[str, QAction]:
    """Preenche a barra de menus e devolve ``{chave do comando: ação}``."""
    acoes: dict[str, QAction] = {}
    for nome_menu in MENUS:
        comandos = [c for c in COMANDOS if c.menu == nome_menu]
        if not comandos:
            continue
        menu = barra.addMenu(nome_menu)
        submenus: dict[str, QMenu] = {}
        for comando in comandos:
            destino: QMenu = menu
            if comando.grupo:
                if comando.grupo not in submenus:
                    submenus[comando.grupo] = menu.addMenu(comando.grupo)
                destino = submenus[comando.grupo]
            acao = destino.addAction(comando.nome)
            acao.triggered.connect(lambda _marcado=False, cmd=comando: cmd.abrir())
            acoes[chave(comando)] = acao
    return acoes
