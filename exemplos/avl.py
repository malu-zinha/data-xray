"""Árvore AVL: inserir 25 provoca uma rotação dupla.

Rode com:  xray exemplos/avl.py
"""


class NoAVL:
    def __init__(self, valor):
        self.valor = valor
        self.esq = None
        self.dir = None
        self.altura = 1


def altura(n):
    return n.altura if n else 0


def fator(n):
    return altura(n.esq) - altura(n.dir)


def atualizar(n):
    n.altura = 1 + max(altura(n.esq), altura(n.dir))


def rot_dir(y):
    x = y.esq          # x vai subir
    y.esq = x.dir      # filho de x troca de pai
    x.dir = y          # y desce à direita
    atualizar(y)
    atualizar(x)
    return x


def rot_esq(x):
    y = x.dir          # y vai subir
    x.dir = y.esq      # filho de y troca de pai
    y.esq = x          # x desce à esquerda
    atualizar(x)
    atualizar(y)
    return y


def inserir_avl(n, valor):
    if n is None:
        return NoAVL(valor)
    if valor < n.valor:
        n.esq = inserir_avl(n.esq, valor)
    else:
        n.dir = inserir_avl(n.dir, valor)
    atualizar(n)
    b = fator(n)
    if b > 1 and valor < n.esq.valor:    # LL
        return rot_dir(n)
    if b < -1 and valor >= n.dir.valor:  # RR
        return rot_esq(n)
    if b > 1:                            # LR
        n.esq = rot_esq(n.esq)
        return rot_dir(n)
    if b < -1:                           # RL
        n.dir = rot_dir(n.dir)
        return rot_esq(n)
    return n


raiz = None
for x in (10, 20, 30, 40, 50):
    raiz = inserir_avl(raiz, x)
raiz = inserir_avl(raiz, 25)   # rotação dupla (RL)
