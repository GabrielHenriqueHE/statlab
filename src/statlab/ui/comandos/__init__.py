"""Comandos do statlab: um diálogo por item de menu.

Importar este pacote registra todos os comandos em ``COMANDOS`` (ver ``_base.comando``).
"""

from statlab.ui.comandos import analises, basicas, dados, graficos, orientacao  # noqa: F401  (registram)
from statlab.ui.comandos._base import COMANDOS, Comando

MENUS = ["Dados", "Estat", "Gráfico", "Assistente", "Ajuda"]

__all__ = ["COMANDOS", "Comando", "MENUS"]
