"""Conclusões em pt-BR no padrão dos "Modelos de redação" da apostila (seção 10) e dos exemplos resolvidos.

Regras de redação: citar o teste, a estatística e o p; dizer o sentido do efeito e o nível de confiança
(95% ou 99%); dar o IC quando houver; em não paramétricos, citar medianas; quando não significativo, dizer
"não há diferença/correlação significativa" (nunca "as médias são iguais").
"""

from __future__ import annotations

from statlab.core.anova import Anova
from statlab.core.anova_dois_fatores import AnovaDoisFatores
from statlab.core.correlacao import Correlacao
from statlab.core.formatacao import num, p_valor
from statlab.core.nao_parametricos import TesteNaoParametrico
from statlab.core.normalidade import Normalidade
from statlab.core.proporcoes import Proporcoes
from statlab.core.qui_quadrado import QuiQuadrado
from statlab.core.regressao import Regressao
from statlab.core.regressao_multipla import RegressaoMultipla
from statlab.core.resultados import Resultado
from statlab.core.testes_t import TesteT
from statlab.core.uma_amostra import UmaAmostra, UmaProporcao
from statlab.core.variancias import Variancias


def _v(x: float) -> str:
    """Número para texto corrido: inteiros sem casas ("mediana 459"), demais com 2 casas."""
    return num(x, 0) if float(x).is_integer() else num(x, 2)


def _p(res: Resultado) -> str:
    return f"p {p_valor(res.p)}"


def _confianca(res: Resultado) -> str:
    return f"com {res.nivel_confianca}% de confiança"


def _gl(res: Resultado) -> str:
    if not res.gl:
        return ""
    partes = [num(g, 0) if float(g).is_integer() else num(g, 1) for g in res.gl]
    return f"gl = {'; '.join(partes)}; "


def _estat(res: Resultado, casas: int = 2) -> str:
    if res.estatistica is None:
        return ""
    return f"{res.rotulo_estatistica} = {num(res.estatistica, casas)}; {_gl(res)}"


def concluir(res: Resultado, *, variavel: str = "a variável") -> str:
    """Texto da conclusão para qualquer resultado do núcleo. ``variavel``: o que foi medido (ex.: "força")."""
    for tipo, funcao in _DESPACHO:
        if isinstance(res, tipo):
            return funcao(res, variavel)
    return _generica(res, variavel)


# ----------------------------------------------------------------------------- correlação e regressão


def _correlacao(res: Correlacao, _: str) -> str:
    x, y = res.nome_x, res.nome_y
    rotulo = "r" if res.metodo == "Pearson" else "rₛ"
    valor = res.r if res.metodo == "Pearson" else res.r_s
    teste = "" if res.metodo == "Pearson" else "Spearman: "
    if not res.significativo:
        linear = "linear " if res.metodo == "Pearson" else ""
        return (
            f"Não existe correlação {linear}significativa entre {x} e {y} ({teste}{rotulo} = {num(valor, 3)}; "
            f"{_p(res)}). A regressão linear não deve ser aplicada; olhe o diagrama de dispersão, pois pode "
            "haver relação não linear."
        )
    sentido = "positiva" if valor > 0 else "negativa"
    movimento = "aumenta" if valor > 0 else "diminui"
    texto = (
        f"Existe correlação {sentido}, significativa e {res.forca} entre {x} e {y} ({teste}{rotulo} = "
        f"{num(valor, 3)}; {_p(res)}), {_confianca(res)}: à medida que {x} aumenta, {y} {movimento}."
    )
    if res.metodo == "Pearson":
        explicado = res.r2 * 100
        texto += (
            f" A variação de {x} explica cerca de {num(explicado, 1)}% da variação de {y}; os "
            f"{num(100 - explicado, 1)}% restantes se devem a outros fatores."
        )
    else:
        texto += " Como os dados não são normais, o r² e a regressão linear devem ser vistos com cautela."
    return texto + " Correlação não prova causalidade."


def _regressao(res: Regressao, _: str) -> str:
    if not res.permitida or res.a is None or res.b is None:
        return "A correlação não é significativa: a reta de regressão não deve ser usada para previsões."
    x, y = res.nome_x, res.nome_y
    sentido = "aumento" if res.a > 0 else "redução"
    texto = (
        f"A cada unidade a mais de {x}, espera-se {sentido} de {num(abs(res.a), 3)} unidade(s) em {y} ({res.equacao})."
    )
    if res.x_min is not None and res.x_min <= 0 <= (res.x_max or 0):
        texto += f" Para {x} = 0, estima-se {y} = {num(res.b, 2)}."
    else:
        texto += (
            f" Para {x} = 0, o modelo estimaria {y} = {num(res.b, 2)}, mas isso é extrapolação "
            f"(faixa observada: {num(res.x_min, 2)} a {num(res.x_max, 2)})."
        )
    if res.avisos and any("NÃO significativa" in a for a in res.avisos):
        texto += " Atenção: a correlação não é significativa; a reta foi calculada só por escolha do usuário."
    return texto


def _regressao_multipla(res: RegressaoMultipla, _: str) -> str:
    if not res.significativo:
        return (
            f"O modelo não é significativo ({_estat(res)}{_p(res)}): os preditores, em conjunto, não explicam "
            f"significativamente {res.resposta}."
        )
    signif = [c for c in res.coeficientes if c.termo != "Constante" and c.p <= res.alpha]
    nao = [c for c in res.coeficientes if c.termo != "Constante" and c.p > res.alpha]
    texto = (
        f"O modelo é significativo ({_estat(res)}{_p(res)}), {_confianca(res)}, e explica "
        f"{num(res.r2 * 100, 1)}% da variação de {res.resposta} (R²(aj) = {num(res.r2_aj * 100, 1)}%)."
    )
    if signif:
        efeitos = "; ".join(
            f"{c.termo} ({'+' if c.coef > 0 else '−'}{num(abs(c.coef), 3)} por unidade, p {p_valor(c.p)})"
            for c in signif
        )
        texto += f" Preditores significativos, mantidos os demais constantes: {efeitos}."
    if nao:
        texto += f" Não significativos: {', '.join(c.termo for c in nao)}."
    return texto


# ----------------------------------------------------------------------------- testes t e não paramétricos


def _teste_t(res: TesteT, variavel: str) -> str:
    if res.nome == "t pareado":
        return _pareado(res, variavel)
    (nome_a, media_a), (nome_b, media_b) = res.medias.items()
    if not res.significativo:
        return (
            f"Não há diferença significativa entre as médias de {variavel} de {nome_a} e {nome_b} "
            f"({_estat(res)}{_p(res)})."
        )
    maior, menor = (nome_a, nome_b) if media_a > media_b else (nome_b, nome_a)
    lo, hi = res.ic if res.ic else (float("nan"), float("nan"))
    if maior != nome_a:  # IC de (a − b) → IC de (maior − menor)
        lo, hi = -hi, -lo
    welch = "Welch: " if "Welch" in res.nome else ""
    return (
        f"{maior} apresentou média de {variavel} significativamente maior que {menor} ({welch}"
        f"{_estat(res)}{_p(res)}), {_confianca(res)}. Espera-se, com 95% de confiança, que a média de {maior} "
        f"supere a de {menor} entre {num(lo)} e {num(hi)}."
    )


def _pareado(res: TesteT, variavel: str) -> str:
    dbar = res.media_diferenca or 0.0
    if not res.significativo:
        return f"Não há evidência significativa de mudança em {variavel} entre antes e depois ({_estat(res)}{_p(res)})."
    lo, hi = res.ic if res.ic else (float("nan"), float("nan"))
    if dbar > 0:
        sentido, efeito, faixa = "menor", "redução", (lo, hi)
    else:
        sentido, efeito, faixa = "maior", "aumento", (-hi, -lo)
    rel = ""
    media_antes = res.medias.get("antes")
    if media_antes:
        rel = f" (cerca de {num(abs(dbar) / abs(media_antes) * 100, 0)}% do valor antes)"
    return (
        f"Depois, {variavel} é significativamente {sentido} do que antes ({_estat(res)}{_p(res)}), "
        f"{_confianca(res)}. A {efeito} média foi de {num(abs(dbar))}{rel}, e espera-se, com 95% de confiança, "
        f"uma {efeito} média entre {num(faixa[0])} e {num(faixa[1])}."
    )


def _nao_parametrico(res: TesteNaoParametrico, variavel: str) -> str:
    med = res.medianas
    if res.nome.startswith("Wilcoxon"):
        antes, depois = med.get("antes", float("nan")), med.get("depois", float("nan"))
        if not res.significativo:
            return (
                f"Pelo teste de Wilcoxon, não há evidência significativa de mudança em {variavel} "
                f"(medianas: antes {_v(antes)}, depois {_v(depois)}; {_p(res)})."
            )
        sentido = "menor" if depois < antes else "maior"
        return (
            f"Pelo teste de Wilcoxon, {variavel} é significativamente {sentido} depois do que antes "
            f"(medianas: antes {_v(antes)}, depois {_v(depois)}; {_p(res)}), {_confianca(res)}."
        )
    (nome_a, med_a), (nome_b, med_b) = list(med.items())[:2]
    if not res.significativo:
        return (
            f"Pelo teste de Mann-Whitney, não há diferença significativa de {variavel} entre {nome_a} "
            f"(mediana {_v(med_a)}) e {nome_b} (mediana {_v(med_b)}) ({_p(res)})."
        )
    maior, menor = ((nome_a, med_a), (nome_b, med_b)) if med_a > med_b else ((nome_b, med_b), (nome_a, med_a))
    return (
        f"Pelo teste de Mann-Whitney, {maior[0]} (mediana {_v(maior[1])}) apresentou {variavel} "
        f"significativamente maior que {menor[0]} (mediana {_v(menor[1])}) ({_p(res)}), {_confianca(res)}."
    )


# ----------------------------------------------------------------------------- ANOVA


def _anova(res: Anova, variavel: str) -> str:
    kw = res.modelo == "Kruskal-Wallis"
    # como na apostila: "(ANOVA: F = 8,70; p < 0,001)" e "(Kruskal-Wallis: H = 29,37; p < 0,001)"
    teste = f"{'Kruskal-Wallis' if kw else 'ANOVA'}: {res.rotulo_estatistica} = {num(res.estatistica, 2)}; {_p(res)}"
    alvo = f"de {variavel} entre os grupos" if kw else f"entre as médias de {variavel} dos grupos"
    if not res.significativo:
        return f"Não há diferença significativa {alvo} ({teste})."
    texto = f"Há diferença significativa {alvo} ({teste}), {_confianca(res)}."
    if not res.comparacoes:
        return texto
    centro = res.medianas if kw else res.medias
    rotulo = "mediana" if kw else "média"
    difs, iguais = [], []
    for c in res.comparacoes:
        if c.significativo(res.alpha):
            a_maior = centro[c.grupo_a] > centro[c.grupo_b]
            maior, menor = (c.grupo_a, c.grupo_b) if a_maior else (c.grupo_b, c.grupo_a)
            conf = 99 if c.p <= 0.01 else 95
            if kw:
                difs.append(
                    f"{maior} ({rotulo} {_v(centro[maior])}) > {menor} ({rotulo} {_v(centro[menor])}) "
                    f"({conf}% de confiança)"
                )
            else:
                difs.append(f"{maior} tem {rotulo} significativamente maior que {menor} ({conf}% de confiança)")
        else:
            iguais.append(f"{c.grupo_a} e {c.grupo_b} (p {p_valor(c.p)})")
    texto += f" Pelo {res.metodo_comparacoes}: " + ("; ".join(difs) if difs else "nenhum par isolado difere") + "."
    if iguais:
        texto += f" Não houve diferença significativa entre {'; '.join(iguais)}."
    return texto


def _anova2(res: AnovaDoisFatores, variavel: str) -> str:
    partes = []
    for lin in res.tabela:
        if lin.p is None:
            continue
        estado = "significativo" if lin.p <= res.alpha else "não significativo"
        partes.append(f"{lin.fonte}: F = {num(lin.f, 2)}; p {p_valor(lin.p)} ({estado})")
    texto = f"ANOVA de dois fatores para {variavel}: " + "; ".join(partes) + "."
    inter = next((lin for lin in res.tabela if "*" in lin.fonte and lin.p is not None), None)
    if inter is not None and inter.p <= res.alpha:
        texto += (
            " Como a interação é significativa, o efeito de cada fator depende do nível do outro; "
            "a interpretação deve ser feita pelo gráfico de interação."
        )
    texto += f" O modelo explica {num(res.r2 * 100, 1)}% da variação (R²(aj) = {num(res.r2_aj * 100, 1)}%)."
    return texto


# ----------------------------------------------------------------------------- proporções, qui-quadrado, uma amostra


def _proporcoes(res: Proporcoes, variavel: str) -> str:
    if not res.significativo:
        return (
            f"Não há diferença significativa entre as proporções de {variavel} de {res.nome_1} e {res.nome_2} "
            f"({_p(res)})."
        )
    maior, p_maior, p_menor, menor = (
        (res.nome_1, res.p1, res.p2, res.nome_2) if res.p1 > res.p2 else (res.nome_2, res.p2, res.p1, res.nome_1)
    )
    return (
        f"A proporção de {variavel} é significativamente maior em {maior} ({num(p_maior * 100, 1)}%) do que em "
        f"{menor} ({num(p_menor * 100, 1)}%) ({res.nome}: {_p(res)}), {_confianca(res)}."
    )


def _qui_quadrado(res: QuiQuadrado, variavel: str) -> str:
    if res.nome.startswith("Qui-quadrado de aderência"):
        if not res.significativo:
            return f"As contagens de {variavel} são compatíveis com as proporções esperadas ({_estat(res)}{_p(res)})."
        return (
            f"As contagens de {variavel} diferem significativamente das proporções esperadas "
            f"({_estat(res)}{_p(res)}), {_confianca(res)}."
        )
    if not res.significativo:
        return f"Não há evidência de associação entre as variáveis ({res.nome}: {_estat(res)}{_p(res)})."
    return f"Há associação significativa entre as variáveis ({res.nome}: {_estat(res)}{_p(res)}), {_confianca(res)}."


def _uma_amostra(res: UmaAmostra, variavel: str) -> str:
    ref = num(res.valor_referencia)
    medida = "mediana" if res.nome.startswith("Wilcoxon") else "média"
    valor = res.mediana if medida == "mediana" else res.media
    if not res.significativo:
        return f"Não há evidência de que a {medida} de {variavel} difira de {ref} ({res.nome}: {_estat(res)}{_p(res)})."
    sentido = "maior" if (valor or 0) > res.valor_referencia else "menor"
    texto = (
        f"A {medida} de {variavel} ({num(valor)}) é significativamente {sentido} que {ref} "
        f"({res.nome}: {_estat(res)}{_p(res)}), {_confianca(res)}."
    )
    if res.ic:
        texto += f" IC 95% para a média: {num(res.ic[0])} a {num(res.ic[1])}."
    return texto


def _uma_proporcao(res: UmaProporcao, variavel: str) -> str:
    if not res.significativo:
        return f"Não há evidência de que a proporção de {variavel} difira de {num(res.p0, 4)} ({res.nome}: {_p(res)})."
    sentido = "maior" if res.p_amostral > res.p0 else "menor"
    return (
        f"A proporção de {variavel} ({num(res.p_amostral * 100, 1)}%) é significativamente {sentido} que "
        f"{num(res.p0 * 100, 1)}% ({res.nome}: {_p(res)}), {_confianca(res)}."
    )


def _variancias(res: Variancias, variavel: str) -> str:
    if not res.significativo:
        return f"As variâncias de {variavel} podem ser consideradas iguais (teste F: {_estat(res, 3)}{_p(res)})."
    return f"As variâncias de {variavel} são significativamente diferentes (teste F: {_estat(res, 3)}{_p(res)})."


def _normalidade(res: Normalidade, variavel: str) -> str:
    if res.normal:
        return f"Pode-se assumir que {variavel} vem de população normal ({res.nome}: {_p(res)})."
    return f"{variavel} não segue distribuição normal ({res.nome}: {_p(res)})."


def _generica(res: Resultado, _: str) -> str:
    if not res.significativo:
        return f"Resultado não significativo ({res.nome}: {_p(res)})."
    return f"Resultado significativo ({res.nome}: {_p(res)}), {_confianca(res)}."


# a ordem importa: subclasses antes das bases
_DESPACHO = (
    (Correlacao, _correlacao),
    (RegressaoMultipla, _regressao_multipla),
    (Regressao, _regressao),
    (TesteT, _teste_t),
    (TesteNaoParametrico, _nao_parametrico),
    (AnovaDoisFatores, _anova2),
    (Anova, _anova),
    (Proporcoes, _proporcoes),
    (QuiQuadrado, _qui_quadrado),
    (UmaAmostra, _uma_amostra),
    (UmaProporcao, _uma_proporcao),
    (Variancias, _variancias),
    (Normalidade, _normalidade),
)
