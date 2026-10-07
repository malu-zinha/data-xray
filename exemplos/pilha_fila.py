"""Pilha sobre lista e fila circular sobre vetor.

Rode com:  xray exemplos/pilha_fila.py
"""


class Pilha:
    def __init__(self):
        self.itens = []

    def empilhar(self, x):
        self.itens.append(x)   # topo = fim da lista

    def desempilhar(self):
        x = self.itens.pop()   # sai pelo topo
        return x


class FilaCircular:
    def __init__(self, capacidade):
        self.dados = [None] * capacidade
        self.inicio = 0        # índice da frente
        self.fim = 0           # próxima vaga livre
        self.tamanho = 0

    def enfileirar(self, x):
        self.dados[self.fim] = x
        cap = len(self.dados)
        self.fim = (self.fim + 1) % cap  # dá a volta
        self.tamanho += 1

    def desenfileirar(self):
        x = self.dados[self.inicio]  # não apaga!
        cap = len(self.dados)
        self.inicio = (self.inicio + 1) % cap
        self.tamanho -= 1
        return x


def roteiro_pilha_fila(pilha, fila):
    pilha.empilhar(23)
    pilha.desempilhar()
    fila.enfileirar("E")   # fim volta para 0
    fila.desenfileirar()
    fila.enfileirar("F")   # reusa a vaga 0


pilha = Pilha()
for x in (4, 8, 15, 16):
    pilha.empilhar(x)
fila = FilaCircular(5)
for x in "ABCD":
    fila.enfileirar(x)
fila.desenfileirar()
fila.desenfileirar()
roteiro_pilha_fila(pilha, fila)
