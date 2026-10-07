"""Buckets de tabela hash: uma cadeia por índice.

    [0] ─▶ [ana] ─▶ [leo]
    [1] ─▶ ∅
"""
from xray.nucleo.canvas import Canvas
from xray.renderizadores.comum import indices_do_topo, nomes_por_endereco, texto, titulo



def buckets(cv, lin, col, cadeias, tag_indice, tag_item, texto=str):
    """tag_indice(k) → tag do "[k]"; tag_item(k, item) → tag de cada item."""
    for k, cadeia in enumerate(cadeias):
        x = cv.escrever(lin + k, col, f"[{k}]", tag_indice(k))
        x = cv.escrever(lin + k, x, " ─▶ " if cadeia else " ─▶ ∅", "fraco")
        for n, item in enumerate(cadeia):
            if n:
                x = cv.escrever(lin + k, x, " ─▶ ", "ponteiro")
            x = cv.escrever(lin + k, x, f"[{texto(item)}]", tag_item(k, item))


# ───────────────────────────── fluxo genérico ──────────────────────────────

def desenhar_estrutura(passo, est, d):
    """Lista de listas de tamanhos variados: uma cadeia por índice.

    Item que acabou de entrar num bucket sai como "novo".
    """
    heap = passo.heap
    internas = [r[1] for r in heap[est.raiz]["itens"]]           # endereço de cada bucket
    cadeias = [[r[1] for r in heap[i]["itens"]] for i in internas]
    marcados = indices_do_topo(passo, len(cadeias))
    cv = Canvas()
    titulo(cv, "buckets", nomes_por_endereco(passo, so_topo=False).get(est.raiz, []))
    novos = {(k, item) for k, i in enumerate(internas) for pos, item in enumerate(cadeias[k])
             if d.mudou(i, pos)}
    buckets(cv, 2, 2, cadeias, lambda k: "destaque" if k in marcados else "fraco",
            lambda k, item: "novo" if (k, item) in novos else "normal", texto)
    for k in marcados:                               # ▶ no bucket que um int do topo indica
        cv.escrever(2 + k, 0, "▶", "destaque")
    return cv
