"""Assistente "Qual teste usar?" (Tabela 2 da apostila).

``decidir`` é uma árvore de perguntas que **indica o comando a usar** — ela não recebe dados, não
roda análise e não decide nada por conta própria. Respostas ``None`` ("não sei") viram pendências,
dizendo o que verificar e com qual comando.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Objetivo:
    chave: str
    descricao: str
    parametrico: str
    nao_parametrico: str
    comando: str
    prerequisitos: str


OBJETIVOS: dict[str, Objetivo] = {
    o.chave: o
    for o in (
        Objetivo(
            "relacao",
            "Relação entre duas variáveis quantitativas (x, y)",
            "Correlação de Pearson",
            "Correlação de Spearman",
            "Estat › Estatísticas básicas › Correlação",
            "pares (x, y), padrão de reta, normalidade de x e de y (sem atalho do TCL), outliers tratados",
        ),
        Objetivo(
            "dois_grupos",
            "Comparar duas médias de grupos independentes",
            "t independente (Welch se as variâncias forem diferentes)",
            "Mann-Whitney",
            "Estat › Estatísticas básicas › t de 2 amostras",
            "normalidade de cada grupo (ou n ≥ 30) e teste F de variâncias",
        ),
        Objetivo(
            "pareado",
            "Comparar antes × depois (mesmos indivíduos)",
            "t pareado",
            "Wilcoxon",
            "Estat › Estatísticas básicas › t pareado",
            "normalidade das diferenças (ou n ≥ 30)",
        ),
        Objetivo(
            "tres_grupos",
            "Comparar três ou mais médias",
            "ANOVA de 1 fator (+ Tukey se significativa)",
            "Kruskal-Wallis (+ comparações 2 a 2)",
            "Estat › ANOVA › Um fator",
            "normalidade de cada grupo (ou n ≥ 30) e maior variância até 9× a menor",
        ),
        Objetivo(
            "proporcoes",
            "Comparar proporções (sim/não) entre dois grupos",
            "Teste de duas proporções (z)",
            "Exato de Fisher",
            "Estat › Estatísticas básicas › 2 proporções",
            "n·p·q ≥ 5 (apostila) e n·p ≥ 5, n·q ≥ 5",
        ),
        Objetivo(
            "associacao",
            "Associação entre duas variáveis categóricas",
            "Qui-quadrado de independência",
            "Exato de Fisher (tabela 2 × 2)",
            "Estat › Tabelas › Qui-quadrado de independência",
            "contagens esperadas: nenhuma < 1 e no máximo 20% < 5 (fora da apostila)",
        ),
        Objetivo(
            "uma_amostra",
            "Comparar uma média com um valor de referência",
            "t para uma amostra",
            "Wilcoxon para uma amostra",
            "Estat › Estatísticas básicas › t de 1 amostra",
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
    comando: str = ""


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
        return Decisao(teste=teste, caminho=caminho, pendencias=pendencias, comando=obj.comando)

    if objetivo == "relacao":
        caminho.append(f"x e y são normais? {_resposta(normal)} (na correlação não vale o atalho n ≥ 30)")
        if normal is None:
            pendencias.append(
                "Verifique a normalidade de x e de y em Estat › Estatísticas básicas › Teste de normalidade."
            )
            return fim(None)
        return fim(obj.parametrico if normal else obj.nao_parametrico)

    if objetivo in ("dois_grupos", "pareado", "tres_grupos", "uma_amostra"):
        alvo = "as diferenças são normais" if objetivo == "pareado" else "os dados (de cada grupo) são normais"
        caminho.append(f"{alvo[0].upper()}{alvo[1:]}? {_resposta(normal)}")
        caminho.append(f"n ≥ 30 (em cada grupo)? {'sim' if n_grande else 'não'}")
        if normal is None and not n_grande:
            pendencias.append("Verifique a normalidade em Estat › Estatísticas básicas › Teste de normalidade.")
            return fim(None)
        norm_ok = bool(normal) or n_grande
        if not norm_ok:
            caminho.append("Normalidade não atendida e n < 30 → teste não paramétrico")
            return fim(obj.nao_parametrico)
        if objetivo == "dois_grupos":
            caminho.append(f"Variâncias iguais (teste F)? {_resposta(variancias_iguais)}")
            if variancias_iguais is None:
                pendencias.append("Verifique as variâncias em Estat › Variâncias › Teste F.")
                return fim(None)
            return fim("t independente (variância combinada)" if variancias_iguais else "t de Welch")
        if objetivo == "tres_grupos":
            caminho.append(f"Maior variância até 9× a menor? {_resposta(razao_ate_9)}")
            if razao_ate_9 is None:
                pendencias.append("Calcule a razão maior/menor variância em Estat › Variâncias › Bartlett / Levene.")
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
        pendencias.append("Estat › Tabelas › Qui-quadrado de independência mostra as contagens esperadas e o critério.")
        return fim(None)
    if esperados_ok:
        return fim(obj.parametrico)
    if tabela_2x2:
        return fim(obj.nao_parametrico)
    caminho.append("Tabela maior que 2 × 2 com esperados pequenos → agrupe categorias e refaça")
    return fim(None)


# ----------------------------------------------------------------------------- com os dados
