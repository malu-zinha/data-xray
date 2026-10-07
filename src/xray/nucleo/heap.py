"""A memória de um instante como um grafo achatado: {endereço: descrição rasa}.

Substitui o deepcopy (modelo do Python Tutor). Em vez de copiar objetos,
cada objeto vira uma descrição que só contém valores primitivos e
REFERÊNCIAS para outros endereços:

    numeros = [5, 2]        →  heap = {4412: {"forma": "sequencia", "tipo": "list",
                                              "itens": [("valor", 5), ("valor", 2)]}}
                                numeros = ("ref", 4412)

Por que não deepcopy: ele falha com arquivos, geradores e conexões, pode
executar o __deepcopy__ da usuária, e duas cópias são difíceis de comparar.
Descrições rasas não executam nada da usuária (a não ser um repr() protegido),
são JSON puro e se comparam com ==.
"""
import enum
import inspect
import sys
from collections import deque

# Tipos EXATOS guardados por valor. Subclasses (um Enum de int, por exemplo)
# não entram: podem ter campos próprios e merecem descrição.
PRIMITIVOS = (int, float, str, bool, type(None))


def e_primitivo(x):
    return type(x) in PRIMITIVOS


def ref(x):
    """Como um valor aparece dentro de outra descrição."""
    return ("valor", x) if e_primitivo(x) else ("ref", id(x))


def endereco(ident):
    """id() → rótulo curto '@xxxx' (os 4 últimos dígitos hexadecimais)."""
    return f"@{ident & 0xFFFF:04x}"


def achatar(raizes):
    """Descreve tudo que é alcançável a partir das raízes. Devolve o heap.

    Percorre com uma pilha de pendentes (e não com recursão): uma lista
    encadeada de 5000 nós estouraria o limite de recursão do Python.
    """
    heap, pendentes = {}, list(raizes)
    while pendentes:
        obj = pendentes.pop()
        if e_primitivo(obj) or id(obj) in heap:
            continue                            # valor simples ou já descrito
        descricao, filhos = _descrever(obj)
        heap[id(obj)] = descricao
        pendentes += filhos                     # o que ele referencia, a descrever
    return heap


def _descrever(obj):
    """(descrição rasa, objetos referenciados por ela)."""
    tipo = type(obj).__name__
    try:
        if isinstance(obj, tuple) and hasattr(type(obj), "_fields"):
            # namedtuple: os nomes dos campos dizem mais que posições
            campos = dict(zip(type(obj)._fields, obj))
            return _objeto(tipo, campos), list(campos.values())
        if isinstance(obj, (set, frozenset)):
            itens = _ordenar(obj)               # set não tem ordem: fixa uma
            return _sequencia(tipo, itens), itens
        if isinstance(obj, (list, tuple, deque)):
            itens = list(obj)
            return _sequencia(tipo, itens), itens
        if isinstance(obj, dict):
            pares = list(obj.items())
            descricao = {"forma": "dicionario", "tipo": tipo,
                         "pares": [[ref(k), ref(v)] for k, v in pares]}
            return descricao, [x for par in pares for x in par]
        if _e_objeto(obj):
            campos = _campos(obj)
            return _objeto(tipo, campos), list(campos.values())
    except Exception:
        pass                                    # não deu para listar o conteúdo
    # todo o resto: arquivos, geradores, funções, módulos, classes...
    return {"forma": "opaco", "tipo": tipo, "texto": _repr_curto(obj)}, []


def _sequencia(tipo, itens):
    return {"forma": "sequencia", "tipo": tipo, "itens": [ref(x) for x in itens]}


def _objeto(tipo, campos):
    return {"forma": "objeto", "tipo": tipo,
            "campos": {nome: ref(v) for nome, v in campos.items()}}


def _e_objeto(obj):
    """Instância "de dados": tem campos e não é função, classe, módulo ou Enum."""
    if (inspect.ismodule(obj) or inspect.isclass(obj) or callable(obj)
            or isinstance(obj, enum.Enum) or _da_biblioteca_padrao(type(obj))):
        return False
    return hasattr(obj, "__dict__") or bool(_nomes_de_slots(type(obj)))


def _da_biblioteca_padrao(classe):
    """Classes do Python (io, random, datetime...) são mostradas pelo repr:
    `datetime(2026, 9, 28)` diz mais que os campos internos, e um arquivo
    aberto não é um "objeto de dados" da usuária."""
    modulo = (classe.__module__ or "").split(".")[0].lstrip("_")   # "_io" → "io"
    return modulo == "builtins" or modulo in sys.stdlib_module_names


def _nomes_de_slots(classe):
    """Campos declarados em __slots__ (em toda a hierarquia de classes)."""
    nomes = []
    for c in classe.__mro__:
        slots = c.__dict__.get("__slots__", ())
        if isinstance(slots, str):              # __slots__ = "x" também vale
            slots = (slots,)
        nomes += [s for s in slots if s not in ("__dict__", "__weakref__")]
    return nomes


def _campos(obj):
    campos = dict(vars(obj)) if hasattr(obj, "__dict__") else {}
    for nome in _nomes_de_slots(type(obj)):     # objetos com __slots__ não têm __dict__
        if hasattr(obj, nome):                  # slot ainda não atribuído: fica de fora
            campos[nome] = getattr(obj, nome)
    return campos


def _ordenar(conjunto):
    try:
        return sorted(conjunto)                 # {3, 1, 2} → [1, 2, 3]
    except TypeError:                           # tipos misturados: ordena pelo texto
        return sorted(conjunto, key=lambda x: (type(x).__name__, _repr_curto(x)))


def _repr_curto(obj, limite=40):
    try:
        texto = repr(obj)
    except Exception:                           # o __repr__ da usuária pode quebrar
        texto = f"<{type(obj).__name__}>"
    return texto if len(texto) <= limite else texto[:limite - 1] + "…"
