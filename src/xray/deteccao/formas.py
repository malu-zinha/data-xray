"""Que forma tem a memória? Lista, árvore, matriz, array... olhando o GRAFO.

Nenhuma regra usa nomes de variáveis ou de campos: "prox", "esq" e "dir"
são descobertos pelo que os campos guardam.

| Sinal no heap                                          | Forma             |
|--------------------------------------------------------|-------------------|
| objeto com 1 campo apontando para o mesmo tipo         | lista             |
| 2 campos para o mesmo tipo, e `a.x.y is a`             | lista_dupla       |
| 2 campos para o mesmo tipo, sem volta                  | arvore            |
| lista de listas retangular (0/1 e quadrada: adjacência)| matriz            |
| dict de chave → lista de chaves do próprio dict        | lista_adjacencia  |
| lista de listas de valores (tamanhos diferentes)       | buckets           |
| lista de primitivos apontada por uma variável          | array             |
| deque apontado por uma variável                        | fila              |

Tipos de nó são decididos olhando a linha do tempo INTEIRA (tipos_de_no):
assim a forma não muda no meio da execução — num passo em que só existe
um nó, com tudo None, ainda se sabe que ele é de uma árvore.
"""
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class TipoNo:
    """Uma classe cujos objetos se ligam uns aos outros."""
    tipo: str          # nome da classe, ex.: "NoAVL"
    forma: str         # "lista", "lista_dupla" ou "arvore"
    ligacoes: tuple    # campos de ligação: ("prox",), ("prox", "ant"), ("esq", "dir")
    valor: str         # campo mostrado dentro do nó (o 1º que só guarda primitivos)


@dataclass
class Estrutura:
    """Um pedaço do heap que ganha desenho especializado."""
    forma: str
    objetos: list                 # endereços cobertos (somem do desenho genérico)
    raiz: int = None              # formas de container: o container principal
    no: TipoNo = None             # formas de nós: o tipo detectado
    ordem: int = 0                # posição na busca a partir das variáveis (ordena os desenhos)


# nome legível de cada forma (títulos e rótulos)
NOMES = {
    "lista": "lista encadeada", "lista_dupla": "lista duplamente encadeada",
    "arvore": "árvore binária", "matriz": "matriz", "matriz_adjacencia": "matriz de adjacência",
    "lista_adjacencia": "lista de adjacência", "buckets": "buckets", "array": "array",
    "fila": "fila",
}


# ───────────────────────────── tipos de nó ──────────────────────────────────

def tipos_de_no(passos):
    """{nome da classe: TipoNo} para as classes que formam listas ou árvores."""
    campos_de = {}               # tipo → campos na ordem em que apareceram
    aponta_si = {}               # tipo → campos que já apontaram para o mesmo tipo
    outra_coisa = {}             # tipo → campos que já guardaram outra coisa (não None)
    guarda_ref = {}              # tipo → campos que já guardaram alguma referência
    for p in passos:
        for e in p.heap.values():
            if e["forma"] != "objeto":
                continue
            t = e["tipo"]
            campos = campos_de.setdefault(t, [])
            for nome, r in e["campos"].items():
                if nome not in campos:
                    campos.append(nome)          # ordem de atribuição no __init__
                if r[0] == "valor":
                    if r[1] is not None:         # None é "sem ligação ainda": vale
                        outra_coisa.setdefault(t, set()).add(nome)
                    continue
                guarda_ref.setdefault(t, set()).add(nome)
                alvo = p.heap.get(r[1])
                if alvo is not None and alvo["forma"] == "objeto" and alvo["tipo"] == t:
                    aponta_si.setdefault(t, set()).add(nome)
                else:
                    outra_coisa.setdefault(t, set()).add(nome)
    tipos = {}
    for t, campos in campos_de.items():
        ligacoes = tuple(c for c in campos if c in aponta_si.get(t, ())
                         and c not in outra_coisa.get(t, ()))
        if len(ligacoes) not in (1, 2):
            continue                             # 0: não é nó; 3+: grafo de objetos
        valor = next((c for c in campos if c not in guarda_ref.get(t, ())), None)
        if len(ligacoes) == 1:
            forma = "lista"
        elif _tem_volta(passos, t, ligacoes):
            forma = "lista_dupla"
        else:
            forma = "arvore"
        tipos[t] = TipoNo(t, forma, ligacoes, valor)
    return tipos


def _tem_volta(passos, tipo, ligacoes):
    """Existe algum `a.x.y is a` (com x, y as duas ligações)? Então é lista dupla."""
    x, y = ligacoes
    for p in passos:
        for ident, e in p.heap.items():
            if e["forma"] != "objeto" or e["tipo"] != tipo:
                continue
            for ida, volta in ((x, y), (y, x)):
                r = e["campos"].get(ida)
                if r and r[0] == "ref":
                    vizinho = p.heap.get(r[1], {})
                    if vizinho.get("campos", {}).get(volta) == ("ref", ident):
                        return True
    return False


# ───────────────────────────── estruturas de um passo ───────────────────────

def raizes_das_variaveis(passo):
    """Endereços apontados direto por alguma variável (globais, locais, estado)."""
    grupos = [passo.globais, passo.estado, *(q.locais for q in passo.quadros)]
    raizes = [r[1] for g in grupos for r in g.values() if r[0] == "ref"]
    if passo.evento == "return" and passo.retorno[0] == "ref":
        raizes.append(passo.retorno[1])
    return raizes


def filhos(e):
    """Endereços referenciados por uma descrição do heap."""
    if e["forma"] == "sequencia":
        refs = e["itens"]
    elif e["forma"] == "dicionario":
        refs = [r for par in e["pares"] for r in par]
    elif e["forma"] == "objeto":
        refs = e["campos"].values()
    else:
        refs = []
    return [r[1] for r in refs if r[0] == "ref"]


def _ordem_de_busca(passo):
    """Endereços na ordem de uma busca em largura a partir das variáveis."""
    ordem, vistos = [], set()
    fila = deque(raizes_das_variaveis(passo))
    while fila:
        ident = fila.popleft()
        if ident in vistos or ident not in passo.heap:
            continue
        vistos.add(ident)
        ordem.append(ident)
        fila.extend(filhos(passo.heap[ident]))
    return ordem


def _lista_de_primitivos(e):
    return (e is not None and e["forma"] == "sequencia" and e["tipo"] == "list"
            and all(r[0] == "valor" for r in e["itens"]))


def _container(ident, heap):
    """Matriz, buckets ou lista de adjacência com raiz em `ident` (ou None)."""
    e = heap[ident]
    if e["forma"] == "sequencia" and e["tipo"] == "list" and len(e["itens"]) >= 2:
        linhas = [heap.get(r[1]) if r[0] == "ref" else None for r in e["itens"]]
        if all(_lista_de_primitivos(l) for l in linhas):
            dentro = [r[1] for r in e["itens"]]
            tamanhos = {len(l["itens"]) for l in linhas}
            if len(tamanhos) == 1 and tamanhos.pop() >= 2:          # retangular
                valores = {r[1] for l in linhas for r in l["itens"]}
                quadrada = len(linhas[0]["itens"]) == len(linhas)
                binaria = valores <= {0, 1}                        # True/False também
                forma = "matriz_adjacencia" if quadrada and binaria else "matriz"
                return Estrutura(forma, [ident, *dentro], raiz=ident)
            return Estrutura("buckets", [ident, *dentro], raiz=ident)
    if e["forma"] == "dicionario" and len(e["pares"]) >= 2:
        chaves = set()
        for k, _ in e["pares"]:
            if k[0] != "valor":
                return None
            chaves.add(k[1])
        listas = [heap.get(v[1]) if v[0] == "ref" else None for _, v in e["pares"]]
        if all(_lista_de_primitivos(l) for l in listas):
            vizinhos = [r[1] for l in listas for r in l["itens"]]
            if vizinhos and set(vizinhos) <= chaves:              # só aponta para chaves
                return Estrutura("lista_adjacencia", [ident, *(v[1] for _, v in e["pares"])],
                                 raiz=ident)
    return None


def detectar(passo, tipos):
    """Estruturas deste passo, na ordem em que são alcançadas pelas variáveis."""
    heap, ordem = passo.heap, _ordem_de_busca(passo)
    posicao = {ident: i for i, ident in enumerate(ordem)}
    estruturas, cobertos = [], set()

    # 1) nós: todas as instâncias de cada tipo de nó formam uma estrutura
    por_tipo = {}
    for ident in ordem:
        e = heap[ident]
        if e["forma"] == "objeto" and e["tipo"] in tipos:
            por_tipo.setdefault(e["tipo"], []).append(ident)
    for t, idents in por_tipo.items():
        estruturas.append(Estrutura(tipos[t].forma, idents, no=tipos[t],
                                    ordem=posicao[idents[0]]))
        cobertos.update(idents)

    # 2) containers com forma própria, em qualquer profundidade
    for ident in ordem:
        if ident in cobertos:
            continue
        est = _container(ident, heap)
        if est and not cobertos.intersection(est.objetos):
            est.ordem = posicao[ident]
            estruturas.append(est)
            cobertos.update(est.objetos)

    # 3) array e fila: só quando uma variável aponta direto para eles
    #    (uma lista de primitivos dentro de um objeto já sai deitada no genérico)
    for ident in dict.fromkeys(raizes_das_variaveis(passo)):
        if ident in cobertos or ident not in heap:
            continue
        e = heap[ident]
        if _lista_de_primitivos(e) and e["itens"]:
            estruturas.append(Estrutura("array", [ident], raiz=ident, ordem=posicao[ident]))
            cobertos.add(ident)
        elif (e["forma"] == "sequencia" and e["tipo"] == "deque"
              and all(r[0] == "valor" for r in e["itens"])):
            estruturas.append(Estrutura("fila", [ident], raiz=ident, ordem=posicao[ident]))
            cobertos.add(ident)

    estruturas.sort(key=lambda est: est.ordem)
    return estruturas
