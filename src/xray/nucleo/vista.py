"""Objetos reconstruídos a partir do heap, para quem desenha com atributos.

Alguns desenhos (árvore, lista) ficam mais simples lendo `n.esq`, `n.prox`
do que descrições do heap. `reconstruir(passo)` monta
objetos leves com os mesmos campos e a mesma identidade (dois nomes que
apontavam para o mesmo nó apontam para o mesmo objeto reconstruído).

Os objetos reconstruídos NÃO são da classe original (o heap só guarda o
nome dela): são de uma classe vazia com o mesmo nome. Por isso tipos se
comparam por nome, nunca com isinstance da classe original.
"""
from collections import deque
from dataclasses import dataclass

from xray.nucleo.heap import endereco


class Objeto:
    """Base dos objetos reconstruídos: só campos, nenhum método."""


_classes = {}                                   # nome → classe vazia com esse nome


def _classe(nome):
    if nome not in _classes:
        _classes[nome] = type(nome, (Objeto,), {})
    return _classes[nome]


# sequências que viram o próprio tipo; qualquer outra (subclasse) vira list
_MUTAVEIS = {"list": list, "deque": deque, "set": set}
_IMUTAVEIS = {"tuple": tuple, "frozenset": frozenset}


@dataclass
class QuadroVisto:
    funcao: str
    linha: int
    locais: dict       # nome → objeto reconstruído


@dataclass
class Vista:
    """O mesmo formato do Passo antigo: variáveis com objetos, não referências."""
    evento: str
    quadros: list
    estado: dict
    retorno: object
    globais: dict
    enderecos: dict    # id(objeto reconstruído) → endereço original
    objetos: dict      # endereço original → objeto reconstruído

    @property
    def topo(self):
        return self.quadros[-1]

    def endereco(self, obj):
        return endereco(self.enderecos.get(id(obj), id(obj)))


def reconstruir(passo):
    """Passo (JSON) → Vista (objetos). Um único memo para o passo inteiro."""
    heap, memo = passo.heap, {}

    # 1ª fase: uma "casca" vazia para cada objeto mutável. Como todas existem
    # antes de qualquer preenchimento, ciclos (a.prox.prox is a) não são problema.
    for ident, e in heap.items():
        if e["forma"] == "objeto":
            memo[ident] = _classe(e["tipo"])()
        elif e["forma"] == "dicionario":
            memo[ident] = {}
        elif e["forma"] == "sequencia" and e["tipo"] not in _IMUTAVEIS:
            memo[ident] = _MUTAVEIS.get(e["tipo"], list)()
        elif e["forma"] == "opaco":
            memo[ident] = _classe(e["tipo"])()  # só para ter identidade e endereço

    def valor(r):
        """Referência → objeto (ou o próprio valor, se primitivo)."""
        tipo_ref, x = r
        if tipo_ref == "valor":
            return x
        if x not in memo:
            # imutável (tuple/frozenset): só dá para criar com os itens prontos
            e = heap[x]
            itens = [valor(i) for i in e["itens"]]
            if x not in memo:                   # a recursão pode tê-lo criado
                memo[x] = _IMUTAVEIS[e["tipo"]](itens)
        return memo[x]

    # 2ª fase: preenche as cascas
    for ident, e in heap.items():
        casca = memo.get(ident)
        if e["forma"] == "objeto":
            for nome, r in e["campos"].items():
                setattr(casca, nome, valor(r))
        elif e["forma"] == "dicionario":
            for k, v in e["pares"]:
                casca[valor(k)] = valor(v)
        elif e["forma"] == "sequencia" and e["tipo"] not in _IMUTAVEIS:
            itens = [valor(i) for i in e["itens"]]
            if isinstance(casca, set):
                casca.update(itens)
            else:
                casca.extend(itens)

    def variaveis(refs):
        return {nome: valor(r) for nome, r in refs.items()}

    quadros = [QuadroVisto(q.funcao, q.linha, variaveis(q.locais)) for q in passo.quadros]
    enderecos = {id(obj): ident for ident, obj in memo.items()}
    return Vista(passo.evento, quadros, variaveis(passo.estado), valor(passo.retorno),
                 variaveis(passo.globais), enderecos, dict(memo))
