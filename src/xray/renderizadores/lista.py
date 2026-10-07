"""Nós de lista encadeada: a caixa [valor | prox] com endereço e referências.

Os nomes dos campos são parâmetros; eles vêm da detecção.
"""
from xray.nucleo.canvas import Canvas
from xray.renderizadores.comum import centralizar, nomes_por_endereco, titulo

SEM_ATRIBUTO = object()                   # marca "o atributo ainda não existe"
LARGURA_NO = 15                           # caixa (10) + seta (5): distância entre nós


def caixa_no(cv, lin, col, no, passo, nomes, tag, tag_seta, valor="valor", prox="prox"):
    """Desenha [valor | prox], o endereço, o prox e as variáveis que apontam para o nó."""
    borda = "novo" if tag == "novo" else "fraco"
    cv.escrever(lin, col, "┌────┬───┐", borda)
    cv.escrever(lin + 1, col, "│", borda)
    cv.escrever(lin + 1, col + 1, centralizar(str(getattr(no, valor, '?')), 4), tag)
    cv.escrever(lin + 1, col + 5, "│", borda)
    seguinte = getattr(no, prox, SEM_ATRIBUTO)
    if seguinte is SEM_ATRIBUTO:          # __init__ ainda não criou o campo
        cv.escrever(lin + 1, col + 6, " ? │", "fraco")
        texto_prox = f"{prox} não existe"
    elif seguinte is None:
        cv.escrever(lin + 1, col + 6, " ∅ │", "fraco")
        texto_prox = f"{prox}=None"
    else:
        cv.escrever(lin + 1, col + 6, " ●─┼────▶", tag_seta)
        texto_prox = f"{prox}={passo.endereco(seguinte)}"
    cv.escrever(lin + 2, col, "└────┴───┘", borda)
    cv.escrever(lin + 3, col + 1, passo.endereco(no), "fraco")
    cv.escrever(lin + 4, col + 1, texto_prox, "fraco")
    if id(no) in nomes:
        cv.escrever(lin + 5, col + 1, "▲ " + ", ".join(nomes[id(no)]), "foco")


# ───────────────────────────── fluxo genérico ──────────────────────────────

MAX_NOS = 12                              # por cadeia; o resto vira "… +N"


def desenhar_estrutura(passo, est, d):
    """Lista (dupla ou simples) detectada: uma cadeia por "cabeça".

    Nó recém-criado e seta religada agora saem com a tag "novo".
    """
    v, no = passo.vista, est.no
    prox = no.ligacoes[0]
    ant = no.ligacoes[1] if len(no.ligacoes) > 1 else None
    nos = [v.objetos[i] for i in est.objetos]
    dos_nos = {id(n) for n in nos}
    apontados = {id(getattr(n, prox, None)) for n in nos}
    cabecas = [n for n in nos if id(n) not in apontados]   # ninguém aponta: começo
    nomes = {id(v.objetos[i]): ns for i, ns in nomes_por_endereco(passo).items()
             if i in v.objetos}

    # 1) separa as cadeias: de cada cabeça, seguindo prox
    vistos, cadeias = set(), []
    for inicio in cabecas + nos:          # `nos` no fim: pega ciclos sem cabeça
        if id(inicio) in vistos:
            continue
        cadeia, n = [], inicio
        while n is not None and id(n) in dos_nos and id(n) not in vistos:
            vistos.add(id(n))
            cadeia.append(n)
            n = getattr(n, prox, None)
        cadeias.append((cadeia, n))       # n: onde parou (None, ou nó já visto = ciclo)
    cadeias.sort(key=lambda c: -len(c[0]))   # a mais longa (a lista "de verdade") primeiro

    # 2) desenha uma cadeia por faixa de 7 linhas
    cv = Canvas()
    titulo(cv, est.forma, detalhe=no.tipo)
    lin = 2
    for num, (cadeia, n) in enumerate(cadeias):
        if num == 1:                      # as outras: nós que a principal não alcança
            cv.escrever(lin, 0, "soltos (a cadeia acima não os alcança):", "fraco")
            lin += 1
        for k, atual in enumerate(cadeia[:MAX_NOS]):
            col = k * LARGURA_NO
            ident = v.enderecos[id(atual)]
            tag = ("novo" if ident in d.novos
                   else "destaque" if ident in d.caminho else "normal")
            seta = "novo" if d.religou(ident, prox) else "ponteiro"
            caixa_no(cv, lin, col, atual, v, nomes, tag, seta,
                     valor=no.valor or "?", prox=prox)
            seguinte = getattr(atual, prox, None)
            if ant and seguinte is not None and getattr(seguinte, ant, None) is atual:
                cv.escrever(lin + 1, col + 10, "◀", "ponteiro")      # volta: ◀───▶
        if len(cadeia) > MAX_NOS:
            cv.escrever(lin + 1, MAX_NOS * LARGURA_NO, f"… +{len(cadeia) - MAX_NOS}", "fraco")
        elif n is not None and id(n) in vistos:
            # parou num nó já desenhado: da própria cadeia = ciclo; de outra = junção
            simbolo = "↺" if any(n is c for c in cadeia) else "→"
            cv.escrever(lin + 1, len(cadeia) * LARGURA_NO, f"{simbolo} {v.endereco(n)}",
                        "ponteiro")
        lin += 7
    return cv
