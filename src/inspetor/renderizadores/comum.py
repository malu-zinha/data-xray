"""Leituras do passo que vários renderizadores especializados usam."""
from inspetor.deteccao.formas import NOMES


def texto(v):
    """Valor dentro de uma célula: None vira "·", o resto vira str (sem aspas)."""
    return "·" if v is None else str(v)


def centralizar(texto, largura):
    """Texto no meio de `largura` colunas; se a sobra é ímpar, o espaço extra vai à esquerda.

    O `^` do Python faz o contrário e deixa "2" puxado para a esquerda numa
    célula de 4 ("·2··"). Assim o caractere do meio cai na coluna
    largura // 2, que é onde os desenhos põem o ▲ e o índice.
    """
    esquerda = (largura - len(texto) + 1) // 2
    return " " * esquerda + texto + " " * (largura - len(texto) - esquerda)


def largura_de_celula(textos, minimo):
    """Largura que cabe todos os textos e deixa o maior número deles exatamente no meio.

    Texto e célula com a mesma paridade centralizam sem sobra; entre a
    largura justa e a de uma coluna a mais, fica a que acerta mais textos.
    """
    justa = max(minimo, max((len(t) for t in textos), default=0) + 2)
    no_meio = [sum((w - len(t)) % 2 == 0 for t in textos) for w in (justa, justa + 1)]
    return justa + 1 if no_meio[1] > no_meio[0] else justa


def variaveis_do_topo(passo):
    """Refs visíveis na linha atual: globais + locais do frame do topo.

    No nível do arquivo o topo é <module>, sem locais: valem as globais.
    """
    visiveis = dict(passo.globais)
    visiveis.update(passo.topo.locais)          # uma local esconde a global de mesmo nome
    return visiveis


def nomes_por_endereco(passo, so_topo=True):
    """Endereço → nomes das variáveis que apontam para ele."""
    if so_topo:
        grupos = [variaveis_do_topo(passo)]
    else:
        grupos = [passo.globais, *(q.locais for q in passo.quadros)]
    nomes = {}
    for grupo in grupos:
        for nome, r in grupo.items():
            if r[0] == "ref" and nome not in nomes.get(r[1], []):
                nomes.setdefault(r[1], []).append(nome)
    return nomes


def indices_do_topo(passo, n):
    """Índice → nomes das variáveis inteiras do topo que cabem em range(n).

    É o que desenha "▲ j" embaixo de um array: um int que é um índice válido.
    """
    indices = {}
    for nome, r in variaveis_do_topo(passo).items():
        v = r[1]
        if r[0] == "valor" and type(v) is int and 0 <= v < n:   # bool não conta
            indices.setdefault(v, []).append(nome)
    return indices


def valores_do_topo(passo):
    """Valores primitivos das variáveis do topo (ex.: o vértice `atual` de uma BFS)."""
    return {r[1] for r in variaveis_do_topo(passo).values()
            if r[0] == "valor" and r[1] is not None and type(r[1]) is not bool}


def titulo(cv, forma, nomes=(), detalhe=""):
    """Linha 0: 'array  ← numeros, v'."""
    pedacos = [(NOMES[forma], "titulo")]
    if detalhe:
        pedacos.append((f" · {detalhe}", "fraco"))
    if nomes:
        pedacos.append(("  ← " + ", ".join(nomes), "foco"))
    cv.trechos(0, 0, pedacos)
