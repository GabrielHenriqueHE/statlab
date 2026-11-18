"""Configuração dos testes.

O Qt roda sem tela: a variável tem de estar no ambiente **antes** de qualquer ``QApplication``, e o
conftest é importado antes dos módulos de teste.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
