"""Vetor com índices em cima e marcadores embaixo (fila circular, deque).

      0     1     2
    ┌─────┬─────┬─────┐
    │  A  │  B  │  ·  │
    └─────┴─────┴─────┘
       ▲ ini       ▲ fim
"""
from xray.nucleo.canvas import Canvas
from xray.renderizadores.comum import centralizar, nomes_por_endereco, texto, titulo



def vetor(cv, lin, col, textos, tags, largura=5):
    """Índices na linha `lin`, células nas 3 linhas seguintes."""
    passo = largura + 1                                    # distância entre paredes
    cv.escrever(lin + 1, col, "┌" + "┬".join("─" * largura for _ in textos) + "┐", "fraco")
    cv.escrever(lin + 3, col, "└" + "┴".join("─" * largura for _ in textos) + "┘", "fraco")
    for i, (texto, tag) in enumerate(zip(textos, tags)):
        c = col + i * passo
        cv.escrever(lin, c + 1 + largura // 2, str(i), "fraco")   # índice em cima
        cv.escrever(lin + 2, c, "│", "fraco")
        cv.escrever(lin + 2, c + 1, centralizar(texto, largura), tag)
    cv.escrever(lin + 2, col + len(textos) * passo, "│", "fraco")


def marcar(cv, lin, col, indice, nome, largura=5, tag="ponteiro"):
    """"▲ nome" embaixo da célula `indice` de um vetor desenhado em `col`."""
    x = col + indice * (largura + 1) + 1 + largura // 2
    cv.escrever(lin, x, "▲", tag)
    cv.escrever(lin, x + 2, nome, tag)


# ───────────────────────────── fluxo genérico ──────────────────────────────

def desenhar_estrutura(passo, est, d):
    """Fila (deque): sai pela frente, entra pelo fim.

    Só o item que acabou de entrar fica "novo": depois de um popleft todos os
    índices mudam, e pintar tudo de verde esconderia o que aconteceu.
    """
    itens = [texto(r[1]) for r in passo.heap[est.raiz]["itens"]]
    cv = Canvas()
    titulo(cv, "fila", nomes_por_endereco(passo, so_topo=False).get(est.raiz, []))
    if not itens:
        cv.escrever(2, 2, "(vazia)", "fraco")
        return cv
    largura = max(5, max(len(t) for t in itens) + 2)
    tags = ["normal"] * len(itens)
    # append: só o fim muda. popleft: tudo desliza e o começo também muda.
    if d.mudou(est.raiz, len(itens) - 1) and (len(itens) == 1 or not d.mudou(est.raiz, 0)):
        tags[-1] = "novo"
    vetor(cv, 2, 2, itens, tags, largura)
    marcar(cv, 6, 2, 0, "frente (sai)", largura)
    marcar(cv, 7, 2, len(itens) - 1, "fim (entra)", largura)
    return cv
