"""Fluxo genérico completo: detecta as formas e escolhe o desenho de cada uma.

    passo → detectar formas → [árvore] [lista] [array] ...   (em cima)
                            → genérico com o resto            (embaixo)

O que um renderizador especializado desenha some do genérico; nas caixas
de variáveis, a referência vira um rótulo ("nó 30", "[0, 1]") em vez
de seta. Casos ambíguos simplesmente não são detectados e ficam
no genérico.
"""
from xray.deteccao.formas import detectar, tipos_de_no
from xray.nucleo.canvas import Canvas
from xray.nucleo.diferenca import Destaques, destaques
from xray.nucleo.memoria import resumo_do_heap
from xray.renderizadores import arvore, array, buckets, generico, grafo, lista, sequencia

RENDERIZADORES = {
    "arvore": arvore.desenhar_estrutura,
    "lista": lista.desenhar_estrutura,
    "lista_dupla": lista.desenhar_estrutura,
    "array": array.desenhar_estrutura,
    "fila": sequencia.desenhar_estrutura,
    "matriz": grafo.desenhar_matriz,
    "matriz_adjacencia": grafo.desenhar_matriz,
    "lista_adjacencia": grafo.desenhar_adjacencia,
    "buckets": buckets.desenhar_estrutura,
}

def _rotulos(passo, est):
    """Endereço → texto curto, para quem aponta para dentro da estrutura."""
    heap, rotulos = passo.heap, {}
    for ident in est.objetos:
        e = heap[ident]
        if est.no is not None:                          # nó: mostra o valor
            r = e["campos"].get(est.no.valor) if est.no.valor else None
            valor = r[1] if r and r[0] == "valor" else "?"
            rotulos[ident] = f"nó {valor}"
        else:                                           # array, fila, linha de matriz...
            rotulos[ident] = resumo_do_heap(("ref", ident), heap, generico.MAX_RESUMO)
    return rotulos


def desenhar(passo, tipos, d=None):
    """Passo → Canvas: estruturas especializadas em cima, genérico embaixo.

    d  destaques (o que mudou desde o passo anterior); None = nenhum
    """
    d = d or Destaques()
    estruturas = detectar(passo, tipos)
    if not estruturas:
        return generico.desenhar(passo, destaques=d)
    cv, lin = Canvas(), 0
    ocultos, rotulos = set(), {}
    for est in estruturas:
        parte = RENDERIZADORES[est.forma](passo, est, d)
        cv.colar(parte, lin, 0)
        lin += parte.altura + 1
        ocultos.update(est.objetos)
        rotulos.update(_rotulos(passo, est))
    cv.colar(generico.desenhar(passo, frozenset(ocultos), rotulos, d), lin, 0)
    return cv


class Desenhista:
    """desenhar(passo) para um Cenario, com os tipos de nó da linha do tempo inteira.

    Os tipos são calculados uma vez, na primeira chamada, olhando TODOS os
    passos (por isso recebe uma função que devolve os passos, não os passos).
    """

    def __init__(self, obter_passos):
        self._obter_passos = obter_passos
        self._tipos = None
        self._posicao = None               # id(passo) → índice na linha do tempo

    @property
    def tipos(self):
        if self._tipos is None:
            self._tipos = tipos_de_no(self._obter_passos())
        return self._tipos

    def anterior(self, passo):
        """O passo antes deste (None no primeiro): base dos destaques de mudança."""
        passos = self._obter_passos()
        if self._posicao is None:
            self._posicao = {id(p): k for k, p in enumerate(passos)}
        k = self._posicao.get(id(passo), 0)
        return passos[k - 1] if k > 0 else None

    def __call__(self, passo):
        return desenhar(passo, self.tipos, destaques(self.anterior(passo), passo))
