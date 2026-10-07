"""Dicionário de listas de objetos.

Rode com:  xray exemplos/turma.py
"""


class Aluna:
    def __init__(self, nome, nota):
        self.nome = nome
        self.nota = nota


def aprovadas(turmas, corte):
    saida = []
    for nome_turma, alunas in turmas.items():
        for a in alunas:
            if a.nota >= corte:
                saida.append(a)    # a MESMA aluna
    return saida


turmas = {
    "manhã": [Aluna("Ana", 9), Aluna("Bia", 6)],
    "tarde": [Aluna("Caio", 8)],
}
boas = aprovadas(turmas, 7)
print([a.nome for a in boas])
