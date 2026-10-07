"""O que mudou entre dois passos? Os destaques genéricos saem daqui.

| Hoje (à mão)          | Genérico                                          |
|-----------------------|---------------------------------------------------|
| "nó novo"             | endereço que não existia no passo anterior        |
| "seta religada"       | campo cujo ref mudou para outro objeto            |
| "caminho da BST"      | objetos apontados por frames abaixo do topo       |
| "variável do topo"    | (foco) continua vindo das variáveis do topo       |

Cada "campo" de um objeto do heap tem uma CHAVE: o nome do atributo
(objeto), o índice (lista, tupla, deque), a ref da chave (dicionário) ou
o próprio item (set). Uma variável tem a chave ("var", nome); o dono dela
é o marcador GLOBAIS ou ("quadro", posição na pilha).

Cuidado com id(): quando um objeto morre, o Python pode dar o mesmo id()
a outro. Se o tipo (ou a forma) mudou, o endereço conta como objeto NOVO.
"""
from dataclasses import dataclass, field

GLOBAIS = "globais"                       # "dono" das variáveis globais


@dataclass
class Destaques:
    novos: set = field(default_factory=set)       # endereços que acabaram de aparecer
    mudados: set = field(default_factory=set)     # (dono, chave) cujo valor mudou
    religados: set = field(default_factory=set)   # (dono, chave) que passou a apontar p/ outro
    caminho: set = field(default_factory=set)     # endereços apontados por frames abaixo do topo

    def mudou(self, dono, chave):
        return (dono, chave) in self.mudados

    def religou(self, dono, chave):
        return (dono, chave) in self.religados


def conteudo(e):
    """Descrição do heap → {chave: ref}."""
    if e["forma"] == "objeto":
        return dict(e["campos"])
    if e["forma"] == "dicionario":
        return {k: v for k, v in e["pares"]}
    if e["forma"] == "sequencia":
        if e["tipo"] in ("set", "frozenset"):
            return {r: r for r in e["itens"]}     # set: o item é a própria chave
        return dict(enumerate(e["itens"]))
    return {}


def _mesmo_objeto(antes, depois):
    """Mesmo endereço E mesmo tipo/forma: senão é um id() reaproveitado."""
    return (antes is not None and antes["tipo"] == depois["tipo"]
            and antes["forma"] == depois["forma"])


def _comparar(dono, antes, depois, d):
    for chave, r in depois.items():
        if antes.get(chave) != r:
            d.mudados.add((dono, chave))
            if r[0] == "ref":
                d.religados.add((dono, chave))


def destaques(anterior, atual):
    """Destaques do passo `atual` em relação ao `anterior` (None = primeiro passo)."""
    d = Destaques()
    # caminho: o que os frames de baixo (chamadas em aberto) estão segurando
    for q in atual.quadros[:-1]:
        d.caminho.update(r[1] for r in q.locais.values() if r[0] == "ref")
    if anterior is None:
        return d                                  # sem passado, nada "mudou"

    for ident, e in atual.heap.items():
        antes = anterior.heap.get(ident)
        if not _mesmo_objeto(antes, e):
            d.novos.add(ident)                    # não existia (ou é outro com o mesmo id)
        else:
            _comparar(ident, conteudo(antes), conteudo(e), d)

    _comparar(GLOBAIS, {("var", n): r for n, r in anterior.globais.items()},
              {("var", n): r for n, r in atual.globais.items()}, d)
    # frames: compara a posição k só se é a mesma chamada (mesma função ali)
    for k, q in enumerate(atual.quadros):
        if k < len(anterior.quadros) and anterior.quadros[k].funcao == q.funcao:
            _comparar(("quadro", k), {("var", n): r for n, r in anterior.quadros[k].locais.items()},
                      {("var", n): r for n, r in q.locais.items()}, d)
    return d
