"""Prática (F6): listas do gerador da disciplina, conferidas com o núcleo do statlab.

O gerador (``gerador.py``) tem lógica estatística própria para montar o gabarito. ``conferir`` roda a análise
do statlab nos dados brutos do enunciado e diz se os dois escolheram o mesmo teste.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from statlab.core.anova import analisar_grupos
from statlab.core.correlacao import analisar_correlacao
from statlab.core.proporcoes import analisar_proporcoes
from statlab.core.resultados import Resultado
from statlab.core.testes_t import analisar_antes_depois, analisar_dois_grupos
from statlab.pratica.gerador import GERADORES, Exercicio, gerar_lista

TIPOS = {
    "corr": "Correlação e regressão",
    "t_par": "Antes × depois (pareado)",
    "t_ind": "Dois grupos independentes",
    "anova": "Três ou mais grupos",
    "prop": "Duas proporções",
}
assert set(TIPOS) == set(GERADORES)


@dataclass(frozen=True)
class Conferencia:
    teste_gerador: str
    teste_statlab: str
    concorda: bool
    resultado: Resultado


def worksheet_bruta(e: Exercicio) -> pd.DataFrame:
    """Dados do enunciado, antes de excluir outliers extremos (colunas mais curtas ficam com faltantes)."""
    brutos = e.extra["brutos"]
    return pd.DataFrame({k: pd.Series(v) for k, v in brutos.items()})


def _analisar(e: Exercicio) -> tuple[str, Resultado]:
    b = e.extra["brutos"]
    if e.tipo == "corr":
        (nx, x), (ny, y) = b.items()
        r = analisar_correlacao(x, y, nome_x=nx, nome_y=ny)
        return r.metodo, r
    if e.tipo == "t_par":
        r = analisar_antes_depois(b["Antes"], b["Depois"], alternativa=e.extra["alternativa"])
        return ("t pareado" if r.nome == "t pareado" else "Wilcoxon"), r
    if e.tipo == "t_ind":
        (na, a), (nb, vb) = b.items()
        r = analisar_dois_grupos(a, vb, nome_a=na, nome_b=nb)
        nome = {"t independente (variâncias iguais)": "t (variâncias iguais)"}.get(r.nome, r.nome)
        return ("t de Welch" if "Welch" in nome else nome), r
    if e.tipo == "anova":
        r = analisar_grupos(b)
        return ("ANOVA" if r.modelo.startswith("ANOVA") else "Kruskal-Wallis"), r
    (g1, g2), (x1, x2), (n1, n2) = b["Grupo"], b["Ocorrências"], b["Total"]
    r = analisar_proporcoes(x1, n1, x2, n2, nome_1=g1, nome_2=g2)
    return ("z" if r.nome.startswith("Teste z") else "Fisher"), r


def conferir(e: Exercicio) -> Conferencia:
    teste, res = _analisar(e)
    return Conferencia(
        teste_gerador=e.extra["teste"], teste_statlab=teste, concorda=teste == e.extra["teste"], resultado=res
    )


def gerar(n: int, tipos: list[str], semente: int | None) -> tuple[list[Exercicio], int]:
    """Gera a lista (sorteio idêntico ao gerador da disciplina). Devolve (exercícios, semente usada)."""
    invalidos = [t for t in tipos if t not in GERADORES]
    if invalidos or not tipos:
        raise ValueError(f"Tipos inválidos ou vazios: {invalidos or tipos}.")
    exs = gerar_lista(n, list(tipos), semente)
    return exs, int(exs[0].extra["seed"])


def lista_markdown(exs: list[Exercicio], semente: int) -> str:
    partes = [
        "# Lista de exercícios — Análise Estatística",
        "",
        f"*Semente: {semente}.* Para cada exercício: verifique os pré-requisitos (outliers, normalidade, "
        "variâncias), escolha o teste, calcule e conclua na linguagem do problema. Use α = 5%.",
    ]
    for i, e in enumerate(exs, 1):
        partes += ["", f"## Exercício {i} — {e.titulo}", "", e.enunciado]
    return "\n".join(partes) + "\n"


def gabarito_markdown(exs: list[Exercicio], semente: int) -> str:
    partes = [
        "# Gabarito — Análise Estatística",
        "",
        f"*Semente: {semente}*",
        "",
        "> Valores calculados com SciPy. Pequenas diferenças em relação ao Excel/Minitab podem ocorrer.",
    ]
    for i, e in enumerate(exs, 1):
        partes += ["", f"## Exercício {i} — {e.titulo}", "", e.gabarito]
    return "\n".join(partes) + "\n"
