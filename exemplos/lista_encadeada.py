"""Lista encadeada simples.

Rode com:  xray exemplos/lista_encadeada.py
"""


class No:
    def __init__(self, valor):
        self.valor = valor
        self.prox = None       # referência ao próximo


class ListaEncadeada:
    def __init__(self):
        self.head = None

    def inserir_fim(self, valor):
        novo = No(valor)       # nasce solto no heap
        if self.head is None:
            self.head = novo
            return
        atual = self.head
        while atual.prox:      # anda até o último
            atual = atual.prox
        atual.prox = novo      # religa UMA referência


lista = ListaEncadeada()
for x in (3, 7, 9, 12):
    lista.inserir_fim(x)
