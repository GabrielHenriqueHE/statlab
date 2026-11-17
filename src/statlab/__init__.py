"""statlab — análise estatística com pré-requisitos, testes e conclusões em pt-BR."""

import subprocess
import sys
from pathlib import Path

__version__ = "0.1.0"

APP = Path(__file__).parent / "ui" / "app.py"


def main() -> None:
    """Abre o app Streamlit (equivalente a ``streamlit run src/statlab/ui/app.py``)."""
    raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(APP), *sys.argv[1:]]))
