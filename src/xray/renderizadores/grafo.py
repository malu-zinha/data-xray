"""Grafo: matriz de adjacência (ou qualquer matriz) e lista de adjacência.

         A  B  C             A → [B] [C]
      A  ·  1  1             B → [A]
      B  1  ·  ·             C → [A]
      C  1  ·  ·
"""
from xray.nucleo.canvas import Canvas
from xray.renderizadores.comum import (nomes_por_endereco, texto, titulo, valores_do_topo,
                                       variaveis_do_topo)


def matriz(cv, lin, col, rotulos, linhas, tag_rotulo, tag_celula, texto=None, espaco=3,
           colunas=None, tag_coluna=None):
    """Cabeçalho na linha `lin`, uma linha por vértice abaixo dele.

    tag_rotulo(i)          → tag do rótulo da linha i (e da coluna i, se tag_coluna faltar)
    tag_celula(i, j, v)    → tag da célula
    texto(v)               → texto da célula (padrão: 0/1 vira "·"/"1")
    colunas                → rótulos das colunas, se diferentes dos das linhas
    """
    texto = texto or (lambda v: "1" if v else "·")
    colunas = rotulos if colunas is None else colunas
    tag_coluna = tag_coluna or tag_rotulo
    for j, r in enumerate(colunas):
        cv.escrever(lin, col + 3 + j * espaco, str(r), tag_coluna(j))    # colunas
    for i, r in enumerate(rotulos):
        cv.escrever(lin + 1 + i, col, str(r), tag_rotulo(i))           # rótulo da linha
        for j, v in enumerate(linhas[i]):
            cv.escrever(lin + 1 + i, col + 3 + j * espaco, texto(v), tag_celula(i, j, v))


def adjacencia(cv, lin, col, adj, tag_vertice, tag_vizinho):
    """Uma linha por vértice: 'A → [B] [C]'."""
    for i, (v, vizinhos) in enumerate(adj.items()):
        pedacos = [(str(v), tag_vertice(v)), (" →", "fraco")]
        for u in vizinhos:
            pedacos += [(" ", "normal"), (f"[{u}]", tag_vizinho(v, u))]
        cv.trechos(lin + i, col, pedacos)


# ───────────────────────────── fluxo genérico ──────────────────────────────

def _rotulos_da_matriz(passo, ident, n):
    """Nomes dos vértices: uma lista de n primitivos ao lado da matriz.

    Procura no objeto que guarda a matriz (ex.: Grafo.vertices ao lado de
    Grafo.matriz) e entre as variáveis do topo. Sem isso: 0, 1, 2...
    """
    heap = passo.heap
    grupos = [e["campos"] for e in heap.values()
              if e["forma"] == "objeto" and ("ref", ident) in e["campos"].values()]
    grupos.append(variaveis_do_topo(passo))
    for grupo in grupos:
        if ("ref", ident) not in grupo.values():
            continue
        for r in grupo.values():
            vizinho = heap.get(r[1]) if r[0] == "ref" else None
            if (vizinho and vizinho["forma"] == "sequencia" and len(vizinho["itens"]) == n
                    and all(i[0] == "valor" for i in vizinho["itens"])):
                return [i[1] for i in vizinho["itens"]]
    return list(range(n))


def desenhar_matriz(passo, est, d):
    """Matriz (retangular) ou matriz de adjacência (quadrada de 0/1).

    Célula que acabou de mudar sai como "novo".
    """
    heap = passo.heap
    internas = [r[1] for r in heap[est.raiz]["itens"]]           # endereço de cada linha
    linhas = [[r[1] for r in heap[i]["itens"]] for i in internas]
    de_adjacencia = est.forma == "matriz_adjacencia"
    em_foco = valores_do_topo(passo)
    cv = Canvas()
    titulo(cv, est.forma, nomes_por_endereco(passo, so_topo=False).get(est.raiz, []))
    if de_adjacencia:                               # vértices com nome, células 1/·
        rotulos = _rotulos_da_matriz(passo, est.raiz, len(linhas))

        def tag_rotulo(i):
            return "foco" if rotulos[i] in em_foco else "normal"

        def tag_celula(i, j, v):
            if d.mudou(internas[i], j):
                return "novo"
            if v and rotulos[i] in em_foco:
                return "destaque"                   # vizinhos do vértice em foco
            return "normal" if v else "fraco"

        matriz(cv, 2, 3, rotulos, linhas, tag_rotulo, tag_celula)
    else:                                           # índices; células com o valor
        espaco = max(3, max(len(texto(v)) for linha in linhas for v in linha) + 1)
        matriz(cv, 2, 3, list(range(len(linhas))), linhas, lambda i: "fraco",
               lambda i, j, v: "novo" if d.mudou(internas[i], j) else "normal",
               texto, espaco, colunas=list(range(len(linhas[0]))))
    return cv


def desenhar_adjacencia(passo, est, d):
    """Dicionário vértice → lista de vizinhos (vizinho recém-incluído = "novo")."""
    heap, em_foco = passo.heap, valores_do_topo(passo)
    pares = heap[est.raiz]["pares"]
    adj = {k[1]: [r[1] for r in heap[v[1]]["itens"]] for k, v in pares}
    novos = {(k[1], r[1]) for k, v in pares
             for pos, r in enumerate(heap[v[1]]["itens"]) if d.mudou(v[1], pos)}
    cv = Canvas()
    titulo(cv, est.forma, nomes_por_endereco(passo, so_topo=False).get(est.raiz, []))
    adjacencia(cv, 2, 2, adj,
               lambda v: "foco" if v in em_foco else "normal",
               lambda v, u: ("novo" if (v, u) in novos else "foco" if u in em_foco
                             else "destaque" if v in em_foco else "normal"))
    return cv
