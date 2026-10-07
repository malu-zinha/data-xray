"""Tabela hash com encadeamento separado.

Rode com:  xray exemplos/hash.py
"""


class TabelaHash:
    def __init__(self, m):
        self.m = m
        self.buckets = [[] for _ in range(m)]

    def h(self, chave):
        soma = 0
        for c in chave:
            soma += ord(c)     # código do caractere
        return soma % self.m

    def inserir(self, chave):
        i = self.h(chave)
        self.buckets[i].append(chave)  # colisão: cadeia


t = TabelaHash(7)
for k in ("ana", "bia", "caio", "duda", "iza"):
    t.inserir(k)
