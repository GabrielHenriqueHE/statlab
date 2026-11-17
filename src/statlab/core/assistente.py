"""Assistente "Qual teste usar?" (Tabela 2 da apostila).

Dois modos:
- ``decidir``: árvore de decisão por perguntas, sem dados. Respostas ``None`` ("não sei") viram pendências,
  dizendo o que verificar e em qual página.
- ``analisar``: roda a análise com os dados (as mesmas funções das páginas) e ``caminho`` explica o percurso:
  cada pré-requisito verificado e por que o teste final foi escolhido.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from statlab.core.anova import analisar_grupos
from statlab.core.correlacao import analisar_correlacao
from statlab.core.proporcoes import analisar_proporcoes
from statlab.core.qui_quadrado import independencia
from statlab.core.resultados import ALPHA_PADRAO, ATENCAO, FALHA, OK, Resultado
from statlab.core.testes_t import analisar_antes_depois, analisar_dois_grupos
from statlab.core.uma_amostra import analisar_uma_amostra


@dataclass(frozen=True)
class Objetivo:
    chave: str
    descricao: str
    parametrico: str
    nao_parametrico: str
    pagina: str
    prerequisitos: str


OBJETIVOS: dict[str, Objetivo] = {
    o.chave: o
    for o in (
        Objetivo(
            "relacao",
            "Relação entre duas variáveis quantitativas (x, y)",
            "Correlação de Pearson",
            "Correlação de Spearman",
            "Correlação e regressão",
            "pares (x, y), padrão de reta, normalidade de x e de y (sem atalho do TCL), outliers tratados",
        ),
        Objetivo(
            "dois_grupos",
            "Comparar duas médias de grupos independentes",
            "t independente (Welch se as variâncias forem diferentes)",
            "Mann-Whitney",
            "Dois grupos independentes",
            "normalidade de cada grupo (ou n ≥ 30) e teste F de variâncias",
        ),
        Objetivo(
            "pareado",
            "Comparar antes × depois (mesmos indivíduos)",
            "t pareado",
            "Wilcoxon",
            "Antes × depois (pareado)",
            "normalidade das diferenças (ou n ≥ 30)",
        ),
        Objetivo(
            "tres_grupos",
            "Comparar três ou mais médias",
            "ANOVA de 1 fator (+ Tukey se significativa)",
            "Kruskal-Wallis (+ comparações 2 a 2)",
            "Três ou mais grupos (ANOVA)",
            "normalidade de cada grupo (ou n ≥ 30) e maior variância até 9× a menor",
        ),
        Objetivo(
            "proporcoes",
            "Comparar proporções (sim/não) entre dois grupos",
            "Teste de duas proporções (z)",
            "Exato de Fisher",
            "Duas proporções",
            "n·p·q ≥ 5 (apostila) e n·p ≥ 5, n·q ≥ 5",
        ),
        Objetivo(
            "associacao",
            "Associação entre duas variáveis categóricas",
            "Qui-quadrado de independência",
            "Exato de Fisher (tabela 2 × 2)",
            "Qui-quadrado",
            "contagens esperadas: nenhuma < 1 e no máximo 20% < 5 (fora da apostila)",
        ),
        Objetivo(
            "uma_amostra",
            "Comparar uma média com um valor de referência",
            "t para uma amostra",
            "Wilcoxon para uma amostra",
            "Uma amostra (t, Z, proporção)",
            "normalidade (ou n ≥ 30) (fora da apostila)",
        ),
    )
}


@dataclass(frozen=True)
class Decisao:
    """Resultado da árvore: teste indicado (ou None se faltar informação), o caminho e o que falta verificar."""

    teste: str | None
    caminho: list[str] = field(default_factory=list)
    pendencias: list[str] = field(default_factory=list)
    pagina: str = ""


def _objetivo(chave: str) -> Objetivo:
    if chave not in OBJETIVOS:
        raise ValueError(f"Objetivo desconhecido: {chave!r}. Use um de: {', '.join(OBJETIVOS)}.")
    return OBJETIVOS[chave]


def _resposta(valor: bool | None) -> str:
    return {True: "sim", False: "não", None: "não sei"}[valor]


def decidir(
    objetivo: str,
    *,
    normal: bool | None = None,
    n_grande: bool = False,
    variancias_iguais: bool | None = None,
    razao_ate_9: bool | None = None,
    npq_ok: bool | None = None,
    esperados_ok: bool | None = None,
    tabela_2x2: bool = False,
) -> Decisao:
    """Árvore de decisão da Tabela 2. ``normal`` refere-se a x e y (relação), às diferenças (pareado) ou a
    cada grupo (demais). ``n_grande`` = n ≥ 30 em cada grupo (atalho do TCL; não vale para a correlação)."""
    obj = _objetivo(objetivo)
    caminho = [f"Objetivo: {obj.descricao}"]
    pendencias: list[str] = []

    def fim(teste: str | None) -> Decisao:
        return Decisao(teste=teste, caminho=caminho, pendencias=pendencias, pagina=obj.pagina)

    if objetivo == "relacao":
        caminho.append(f"x e y são normais? {_resposta(normal)} (na correlação não vale o atalho n ≥ 30)")
        if normal is None:
            pendencias.append("Verifique a normalidade de x e de y na página Normalidade (Shapiro-Wilk).")
            return fim(None)
        return fim(obj.parametrico if normal else obj.nao_parametrico)

    if objetivo in ("dois_grupos", "pareado", "tres_grupos", "uma_amostra"):
        alvo = "as diferenças são normais" if objetivo == "pareado" else "os dados (de cada grupo) são normais"
        caminho.append(f"{alvo[0].upper()}{alvo[1:]}? {_resposta(normal)}")
        caminho.append(f"n ≥ 30 (em cada grupo)? {'sim' if n_grande else 'não'}")
        if normal is None and not n_grande:
            pendencias.append("Verifique a normalidade na página Normalidade (Shapiro-Wilk).")
            return fim(None)
        norm_ok = bool(normal) or n_grande
        if not norm_ok:
            caminho.append("Normalidade não atendida e n < 30 → teste não paramétrico")
            return fim(obj.nao_parametrico)
        if objetivo == "dois_grupos":
            caminho.append(f"Variâncias iguais (teste F)? {_resposta(variancias_iguais)}")
            if variancias_iguais is None:
                pendencias.append("Verifique as variâncias na página Dois grupos, aba Comparar variâncias.")
                return fim(None)
            return fim("t independente (variância combinada)" if variancias_iguais else "t de Welch")
        if objetivo == "tres_grupos":
            caminho.append(f"Maior variância até 9× a menor? {_resposta(razao_ate_9)}")
            if razao_ate_9 is None:
                pendencias.append("Calcule a razão maior/menor variância (página Estatísticas descritivas).")
                return fim(None)
            if not razao_ate_9:
                caminho.append("Razão de variâncias acima de 9 → teste não paramétrico")
                return fim(obj.nao_parametrico)
        return fim(obj.parametrico)

    if objetivo == "proporcoes":
        caminho.append(f"n·p·q ≥ 5 e n·p, n·q ≥ 5 em cada grupo? {_resposta(npq_ok)}")
        if npq_ok is None:
            pendencias.append("Calcule n·p·q de cada grupo (p = proporção observada, q = 1 − p).")
            return fim(None)
        return fim(obj.parametrico if npq_ok else obj.nao_parametrico)

    # associação
    caminho.append(f"Contagens esperadas suficientes (Cochran)? {_resposta(esperados_ok)}")
    if esperados_ok is None:
        pendencias.append("A página Qui-quadrado calcula as contagens esperadas e verifica o critério.")
        return fim(None)
    if esperados_ok:
        return fim(obj.parametrico)
    if tabela_2x2:
        return fim(obj.nao_parametrico)
    caminho.append("Tabela maior que 2 × 2 com esperados pequenos → agrupe categorias e refaça")
    return fim(None)


# ----------------------------------------------------------------------------- com os dados


def analisar(objetivo: str, *, alpha: float = ALPHA_PADRAO, **dados: Any) -> Resultado:
    """Roda a análise do objetivo com os dados. Argumentos por objetivo:

    relacao: x, y, nome_x, nome_y | dois_grupos: a, b, nome_a, nome_b, alternativa | pareado: antes, depois,
    alternativa | tres_grupos: grupos | proporcoes: x1, n1, x2, n2, nome_1, nome_2, alternativa |
    associacao: tabela | uma_amostra: valores, mu0, nome, alternativa
    """
    _objetivo(objetivo)
    if objetivo == "relacao":
        return analisar_correlacao(
            dados["x"], dados["y"], alpha=alpha, nome_x=dados.get("nome_x", "x"), nome_y=dados.get("nome_y", "y")
        )
    if objetivo == "dois_grupos":
        return analisar_dois_grupos(
            dados["a"],
            dados["b"],
            alpha=alpha,
            alternativa=dados.get("alternativa", "bilateral"),
            nome_a=dados.get("nome_a", "Grupo 1"),
            nome_b=dados.get("nome_b", "Grupo 2"),
        )
    if objetivo == "pareado":
        return analisar_antes_depois(
            dados["antes"], dados["depois"], alpha=alpha, alternativa=dados.get("alternativa", "bilateral")
        )
    if objetivo == "tres_grupos":
        return analisar_grupos(dados["grupos"], alpha=alpha)
    if objetivo == "proporcoes":
        return analisar_proporcoes(
            dados["x1"],
            dados["n1"],
            dados["x2"],
            dados["n2"],
            alpha=alpha,
            alternativa=dados.get("alternativa", "bilateral"),
            nome_1=dados.get("nome_1", "grupo 1"),
            nome_2=dados.get("nome_2", "grupo 2"),
        )
    if objetivo == "associacao":
        return independencia(dados["tabela"], alpha=alpha)
    return analisar_uma_amostra(
        dados["valores"],
        dados["mu0"],
        alpha=alpha,
        alternativa=dados.get("alternativa", "bilateral"),
        nome=dados.get("nome", "amostra"),
    )


_SIMBOLO = {OK: "✅", ATENCAO: "⚠️", FALHA: "❌"}


def foi_parametrico(res: Resultado) -> bool:
    """Se o teste escolhido é o paramétrico do objetivo (pelo nome do teste)."""
    nao_param = ("Spearman", "Mann-Whitney", "Wilcoxon", "Kruskal-Wallis", "Fisher")
    return not any(marca in res.nome for marca in nao_param)


def caminho(objetivo: str, res: Resultado) -> list[str]:
    """Percurso da decisão, em texto: objetivo, cada pré-requisito verificado e o teste escolhido com o motivo."""
    obj = _objetivo(objetivo)
    linhas = [f"Objetivo: {obj.descricao}", f"Teste paramétrico indicado: {obj.parametrico}"]
    linhas += [f"{_SIMBOLO.get(v.status, '•')} {v.nome}: {v.detalhe}" for v in res.verificacoes]
    violados = [v.nome for v in res.verificacoes if v.status == FALHA]
    if foi_parametrico(res):
        motivo = "pré-requisitos atendidos"
        if any(v.status == ATENCAO for v in res.verificacoes):
            motivo += " (com ressalvas ⚠️ acima)"
    else:
        motivo = "pré-requisito violado: " + "; ".join(violados) if violados else "pré-requisito não atendido"
    linhas.append(f"Teste escolhido: {res.nome} — {motivo}")
    return linhas
