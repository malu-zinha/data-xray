"""O heap achatado (etapa 2 do ROADMAP): descrições rasas no lugar do deepcopy."""
import json
from collections import deque, namedtuple
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pytest

from xray.cli import cenario_do_arquivo
from xray.nucleo.heap import achatar, ref
from xray.nucleo.memoria import resumo
from xray.nucleo.rastreador import Passo

RAIZ = Path(__file__).parent.parent


class No:
    def __init__(self, valor, prox=None):
        self.valor = valor
        self.prox = prox


class ComSlots:
    __slots__ = ("x", "y")

    def __init__(self):
        self.x = 1                              # y fica sem valor de propósito


def descricao(obj):
    return achatar([obj])[id(obj)]


def test_primitivos_ficam_por_valor():
    assert ref(3) == ("valor", 3) and ref("a") == ("valor", "a") and ref(None) == ("valor", None)
    assert achatar([1, "x", 2.5, True, None]) == {}   # nada vai para o heap


def test_lista_dict_e_objeto():
    no = No(7)
    lista = [1, no]
    heap = achatar([{"k": lista}])
    assert heap[id(lista)] == {"forma": "sequencia", "tipo": "list",
                               "itens": [("valor", 1), ("ref", id(no))]}
    assert heap[id(no)] == {"forma": "objeto", "tipo": "No",
                            "campos": {"valor": ("valor", 7), "prox": ("valor", None)}}


def test_referencia_compartilhada_aparece_uma_vez():
    comum = [1]
    heap = achatar([[comum, comum]])
    assert list(heap).count(id(comum)) == 1


def test_ciclo_nao_trava():
    a = No(1)
    a.prox = No(2, a)                           # a → b → a
    heap = achatar([a])
    assert heap[id(a.prox)]["campos"]["prox"] == ("ref", id(a))


def test_lista_encadeada_longa_nao_estoura_recursao():
    cabeca = None
    for i in range(5000):
        cabeca = No(i, cabeca)
    assert len(achatar([cabeca])) == 5000


def test_set_tem_ordem_estavel():
    assert descricao({3, 1, 2})["itens"] == [("valor", 1), ("valor", 2), ("valor", 3)]
    misturado = descricao({1, "a"})             # tipos que não se comparam
    assert misturado["itens"] == [("valor", 1), ("valor", "a")]


def test_slots_namedtuple_e_deque():
    assert descricao(ComSlots())["campos"] == {"x": ("valor", 1)}
    Ponto = namedtuple("Ponto", "x y")
    assert descricao(Ponto(1, 2))["campos"] == {"x": ("valor", 1), "y": ("valor", 2)}
    assert descricao(deque([1]))["tipo"] == "deque"


def test_opacos():
    with open(__file__) as arq:
        assert descricao(arq)["forma"] == "opaco"
    assert descricao(x for x in [])["forma"] == "opaco"          # gerador
    assert descricao(len)["forma"] == "opaco"                    # função
    assert descricao(date(2026, 9, 28))["texto"] == "datetime.date(2026, 9, 28)"


def test_nao_executa_deepcopy_e_sobrevive_a_repr_quebrado():
    class Chato:
        def __deepcopy__(self, memo):
            raise AssertionError("não devia ser chamado")

    class ReprQuebrado:
        __slots__ = ()                          # sem campos: vira objeto vazio

        def __repr__(self):
            raise ValueError

    achatar([Chato(), ReprQuebrado()])          # não levanta nada


def test_passos_sao_json_puro():
    for arquivo in sorted((RAIZ / "exemplos").glob("*.py")):
        c = cenario_do_arquivo(str(arquivo))
        for p in c.passos:
            json.dumps(asdict(p))               # levantaria TypeError se não fosse


def test_mesmo_objeto_mesmo_endereco_em_todos_os_passos():
    c = cenario_do_arquivo(str(RAIZ / "exemplos" / "bubble.py"))
    enderecos = {p.endereco(p.globais["numeros"]) for p in c.passos if "numeros" in p.globais}
    assert len(enderecos) == 1


def test_vista_preserva_identidade_e_ciclos():
    a = No(1)
    a.prox = No(2, a)
    p = Passo("line", [], {"a": ref(a), "b": ref(a.prox)}, ref(None), achatar([a]))
    v = p.vista
    assert v.estado["a"].prox is v.estado["b"] and v.estado["b"].prox is v.estado["a"]
    assert type(v.estado["a"]).__name__ == "No"      # classe vazia com o mesmo nome
    assert v.endereco(v.estado["a"]) == p.endereco(ref(a))


def test_vista_reconstroi_tuplas_sets_e_dicts():
    dado = {"t": (1, [2]), "s": {3, 4}, (5, 6): deque(["x"])}
    p = Passo("line", [], {"d": ref(dado)}, ref(None), achatar([dado]))
    assert p.vista.estado["d"] == dado


@pytest.mark.parametrize("valor, texto", [
    ([1, [2, 3]], "[1, [2, 3]]"),
    ((1,), "(1,)"),
    (set(), "set()"),
    ({2, 1}, "{1, 2}"),
    ({"a": 1}, "{'a': 1}"),
    (deque(["A"]), "deque(['A'])"),
    (list(range(100)), "[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10…"),
])
def test_resumo(valor, texto):
    p = Passo("line", [], {}, ref(None), achatar([valor]))
    assert resumo(ref(valor), p) == texto


def test_resumo_de_lista_que_contem_a_si_mesma():
    x = [1]
    x.append(x)
    p = Passo("line", [], {}, ref(None), achatar([x]))
    assert resumo(ref(x), p) == "[1, [...]]"


class Pessoa:
    def __init__(self, nome, idade):
        self.nome = nome
        self.idade = idade


def test_resumo_de_objeto_mostra_os_campos():
    ana = Pessoa("Ana", 20)
    p = Passo("line", [], {}, ref(None), achatar([ana]))
    assert resumo(ref(ana), p) == "Pessoa(nome='Ana', idade=20)"


def test_resumo_de_no_mostra_o_valor_sem_endereco():
    n = No(3, No(4))
    p = Passo("line", [], {}, ref(None), achatar([n]))
    assert resumo(ref(n), p) == "nó 3"


def test_resumo_de_objeto_que_aponta_para_si_mesmo():
    class Anel:
        pass
    a = Anel()
    a.eu = a
    p = Passo("line", [], {}, ref(None), achatar([a]))
    assert resumo(ref(a), p) == "Anel(eu=Anel(…))"


def test_nenhum_deepcopy_no_pacote():
    fontes = (RAIZ / "src" / "xray").rglob("*.py")
    assert not [f for f in fontes if "deepcopy(" in f.read_text()]
