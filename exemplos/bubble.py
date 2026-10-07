"""Ordenação por bolha.

Rode com:  xray exemplos/bubble.py
"""


def bubble_sort(v):
    n = len(v)
    for passada in range(n - 1):
        # a cada passada, o maior "afunda"
        for j in range(n - 1 - passada):
            if v[j] > v[j + 1]:
                v[j], v[j + 1] = v[j + 1], v[j]
    return v


numeros = [5, 2, 9, 1, 7]
print("antes: ", numeros)
bubble_sort(numeros)       # ordena a MESMA lista
print("depois:", numeros)
