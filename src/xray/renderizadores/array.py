"""Array: células lado a lado com o índice embaixo.

    ┌─────┬─────┬─────┐
    │  5  │  2  │  9  │
    └─────┴─────┴─────┘
       0     1     2
"""
from xray.nucleo.canvas import Canvas
from xray.renderizadores.comum import (centralizar, indices_do_topo, largura_de_celula,
                                           nomes_por_endereco, texto, titulo)



def celulas(cv, lin, col, textos, tags, largura=4):
    """Desenha as células a partir de (lin, col); ocupa 4 linhas (a última = índices).

    Devolve a coluna do centro de cada célula (para marcar ▲ embaixo).
    """
    cv.escrever(lin, col, "┌" + "┬".join("─" * largura for _ in textos) + "┐", "fraco")
    cv.escrever(lin + 2, col, "└" + "┴".join("─" * largura for _ in textos) + "┘", "fraco")
    centros = []
    for i, (texto, tag) in enumerate(zip(textos, tags)):
        c = col + i * (largura + 1)
        cv.escrever(lin + 1, c, "│", "fraco")                 # parede da célula
        cv.escrever(lin + 1, c + 1, centralizar(texto, largura), tag)
        cv.escrever(lin + 3, c + 1, centralizar(str(i), largura), "fraco")   # índice embaixo
        centros.append(c + 1 + largura // 2)
    cv.escrever(lin + 1, col + len(textos) * (largura + 1), "│", "fraco")
    return centros


# ───────────────────────────── fluxo genérico ──────────────────────────────

MAX_CELULAS = 30


def desenhar_estrutura(passo, est, d):
    """Array apontado por variável: células, e "▲ j" nos inteiros que são índices.

    Célula que acabou de mudar (ex.: a troca do bubble sort) sai como "novo".
    """
    itens = [r[1] for r in passo.heap[est.raiz]["itens"]]
    textos = [texto(x) for x in itens[:MAX_CELULAS]]
    largura = largura_de_celula(textos, 4)
    marcados = indices_do_topo(passo, len(textos))
    cv = Canvas()
    titulo(cv, "array", nomes_por_endereco(passo, so_topo=False).get(est.raiz, []))
    tags = ["novo" if d.mudou(est.raiz, i) else "destaque" if i in marcados else "normal"
            for i in range(len(textos))]
    centros = celulas(cv, 2, 2, textos, tags, largura)
    if len(itens) > MAX_CELULAS:
        cv.escrever(3, 2 + len(textos) * (largura + 1) + 2, f"… +{len(itens) - MAX_CELULAS}",
                    "fraco")
    ocupado = {}                          # linha → última coluna usada (nomes não se sobrepõem)
    for i in sorted(marcados):
        x = centros[i]
        cv.escrever(6, x, "▲", "destaque")
        nome = ", ".join(marcados[i])
        lin = 7
        while ocupado.get(lin, -1) >= x - 1:
            lin += 1                      # desce até achar espaço
        cv.escrever(lin, x, nome, "destaque")
        ocupado[lin] = x + len(nome)
    return cv
