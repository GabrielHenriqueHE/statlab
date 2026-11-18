"""statlab — análise estatística com pré-requisitos, testes e conclusões em pt-BR."""

__version__ = "0.1.0"


def main() -> None:
    """Abre o app Qt."""
    from statlab.ui.app import main as qt_main

    qt_main()
