"""Estrutura comum de resultado de todos os testes e análises do núcleo.

Cada função do núcleo devolve um objeto derivado de ``Resultado``. A UI só exibe esses campos;
nenhuma regra estatística é recalculada fora do núcleo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ALPHA_PADRAO = 0.05


@dataclass(frozen=True)
class ParComparacao:
    """Comparação entre dois grupos num post hoc (Tukey ou Mann-Whitney com Bonferroni).

    ``diferenca`` é média_a − média_b (Tukey) ou None (postos). ``ic`` só existe no Tukey.
    """

    grupo_a: str
    grupo_b: str
    p: float
    metodo: str
    diferenca: float | None = None
    ic: tuple[float, float] | None = None

    def significativo(self, alpha: float = ALPHA_PADRAO) -> bool:
        return self.p <= alpha


@dataclass(kw_only=True)
class Resultado:
    """Campos comuns a todo teste ou análise.

    - ``p``: valor p do teste que decidiu a conclusão (já unilateral se a direção foi escolhida antes).
    - ``passos``: cálculo em texto, na ordem em que foi feito.
    - ``avisos``: alertas para o usuário (exclusões, premissas violadas, extrapolação).
    - ``prerequisitos``: resultado de cada verificação prévia, em texto.
    """

    nome: str
    alpha: float = ALPHA_PADRAO
    estatistica: float | None = None
    rotulo_estatistica: str = ""
    gl: tuple[float, ...] | None = None
    p: float | None = None
    n: int | None = None
    ic: tuple[float, float] | None = None
    ic_descricao: str = ""
    prerequisitos: list[str] = field(default_factory=list)
    passos: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def significativo(self) -> bool | None:
        """True/False pela regra p ≤ α; None quando não há p."""
        if self.p is None:
            return None
        return self.p <= self.alpha

    @property
    def nivel_confianca(self) -> int | None:
        """99 se p ≤ 0,01; 95 se significativo com p entre 0,01 e α; None se não significativo."""
        if self.significativo is not True:
            return None
        return 99 if self.p <= 0.01 else 95
