"""Grafo (matriz e lista de adjacência) e BFS.

Rode com:  xray exemplos/grafo.py
"""
from collections import deque


class Grafo:
    def __init__(self, vertices):
        self.vertices = list(vertices)
        n = len(self.vertices)
        self.idx = {v: i for i, v in enumerate(vertices)}
        self.matriz = [[0] * n for _ in range(n)]
        self.adj = {v: [] for v in self.vertices}

    def aresta(self, a, b):
        i, j = self.idx[a], self.idx[b]
        self.matriz[i][j] = self.matriz[j][i] = 1
        self.adj[a].append(b)
        self.adj[b].append(a)


def bfs(g, origem):
    descobertos = {origem}
    fila = deque([origem])
    ordem = []
    while fila:
        atual = fila.popleft()     # sai da frente
        ordem.append(atual)
        for viz in g.adj[atual]:
            if viz not in descobertos:
                descobertos.add(viz)
                fila.append(viz)   # entra no fim
    return ordem


g = Grafo("ABCDEF")
for a, b in "AB AC BD CD CE DF EF".split():
    g.aresta(a, b)
ordem = bfs(g, "A")
