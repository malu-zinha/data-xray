"""Detecção de forma + desenhos especializados (etapa 4 do ROADMAP).

As snapshots do fluxo completo ficam em test_desenhos.py.
"""
import re
from pathlib import Path

import pytest

from xray.cli import cenario_do_arquivo
from xray.deteccao.formas import detectar
from xray.renderizadores.arvore import desenhar_arvore

RAIZ = Path(__file__).parent.parent


def programa(tmp_path, codigo):
    arquivo = tmp_path / "programa.py"
    arquivo.write_text(codigo)
    return cenario_do_arquivo(str(arquivo))


def formas_no_fim(c):
    """Formas detectadas no último passo do programa."""
    return [e.forma for e in detectar(c.passos[-1], c.desenhar.tipos)]


NO = "class No:\n    def __init__(s, v):\n        s.v = v\n"


@pytest.mark.parametrize("codigo, esperado", [
    # nomes propositalmente estranhos: a detecção olha o grafo, não os nomes
    (NO + "        s.zz = None\n"
          "a = No(1)\na.zz = No(2)\na.zz.zz = No(3)\nfim = 1\n", ["lista"]),
    (NO + "        s.p = None\n        s.q = None\n"
          "a = No(1)\nb = No(2)\na.p = b\nb.q = a\nfim = 1\n", ["lista_dupla"]),
    (NO + "        s.e = None\n        s.d = None\n"
          "r = No(2)\nr.e = No(1)\nr.d = No(3)\nfim = 1\n", ["arvore"]),
    ("m = [[0, 1], [1, 0]]\nfim = 1\n", ["matriz_adjacencia"]),
    ("m = [[1, 2, 3], [4, 5, 6]]\nfim = 1\n", ["matriz"]),
    ("g = {'a': ['b'], 'b': ['a', 'c'], 'c': []}\nfim = 1\n", ["lista_adjacencia"]),
    ("b = [[], ['x', 'y'], ['z']]\nfim = 1\n", ["buckets"]),
    ("v = [3, 1, 2]\nfim = 1\n", ["array"]),
    ("from collections import deque\nq = deque([1, 2])\nfim = 1\n", ["fila"]),
])
def test_detecta_cada_forma(tmp_path, codigo, esperado):
    assert formas_no_fim(programa(tmp_path, codigo)) == esperado


def test_casos_sem_forma_ficam_no_generico(tmp_path):
    c = programa(tmp_path, (
        "class Aluna:\n    def __init__(s, n):\n        s.nome = n\n        s.notas = [9]\n"
        "turma = {'a': [Aluna('Ana')]}\n"        # dict de listas de OBJETOS: sem forma
        "fim = 1\n"))
    assert formas_no_fim(c) == []


def test_lista_dentro_de_objeto_nao_vira_array(tmp_path):
    c = programa(tmp_path, "class P:\n    def __init__(s):\n        s.itens = [1, 2]\n"
                           "p = P()\nfim = 1\n")
    assert formas_no_fim(c) == []               # já sai deitada no genérico


def test_tipo_de_no_vale_para_a_linha_do_tempo_inteira(tmp_path):
    # no 1º passo com nó, ele ainda não aponta para ninguém; mesmo assim é "arvore"
    c = programa(tmp_path, NO + "        s.e = None\n        s.d = None\n"
                           "r = No(2)\nr.e = No(1)\nr.d = No(3)\nfim = 1\n")
    primeiro = next(p for p in c.passos if "r" in p.globais)
    assert [e.forma for e in detectar(primeiro, c.desenhar.tipos)] == ["arvore"]


@pytest.mark.parametrize("nome, esperado", [
    ("bubble", {"array"}), ("lista_encadeada", {"lista"}), ("bst", {"arvore"}),
    ("avl", {"arvore"}), ("grafo", {"matriz_adjacencia", "lista_adjacencia", "fila"}),
    ("hash", {"buckets"}), ("turma", set()),
])
def test_exemplos_sao_detectados(nome, esperado):
    """Os exemplos (antigos cenários à mão) ganham a forma certa, pelo grafo."""
    c = cenario_do_arquivo(str(RAIZ / "exemplos" / f"{nome}.py"))
    vistas = {e.forma for p in c.passos for e in detectar(p, c.desenhar.tipos)}
    assert esperado <= vistas and (esperado or not vistas)


def test_gabarito_avl_mostra_a_rotacao():
    """O fluxo genérico mostra a árvore em pedaços no meio da rotação, como a aba AVL."""
    c = cenario_do_arquivo(str(RAIZ / "exemplos" / "avl.py"))
    textos = [c.desenhar(p).texto_puro() for p in c.passos
              if p.topo.funcao in ("rot_esq", "rot_dir")]
    assert any("árvore em 2 pedaços" in t for t in textos)
    final = c.desenhar(c.passos[-1]).texto_puro()
    assert "pedaços" not in final and "30(3)" in final    # rebalanceada, 30 no meio


def test_arvore_rasa_em_caixas_funda_compacta(tmp_path):
    rasa = programa(tmp_path, NO + "        s.e = None\n        s.d = None\n"
                            "r = No(2)\nr.e = No(1)\nr.d = No(3)\nfim = 1\n")
    texto = rasa.desenhar(rasa.passos[-1]).texto_puro()
    assert "│ 1 │" in texto and "┌─┴─┐" in texto   # cada nó numa caixa, ligada ao pai
    funda = programa(tmp_path, NO + "        s.e = None\n        s.d = None\n"
                             "r = No(1)\nr.e = No(0)\nn = r\n"   # 7 níveis: escada à direita
                             "for v in range(2, 8):\n"
                             "    n.d = No(v)\n    n = n.d\nfim = 1\n")
    texto = funda.desenhar(funda.passos[-1]).texto_puro()
    assert "│ 7 │" not in texto and "└─┐" in texto  # sem caixas: não caberia na tela


def test_arvore_com_ciclo_desenha_sem_linha_de_volta():
    class No:
        def __init__(s, v):
            s.v, s.e, s.d = v, None, None
    a, b = No(1), No(2)
    a.e, b.e = b, a                              # b aponta de volta para a raiz
    texto = desenhar_arvore(a, lambda n: [(str(n.v), "normal")],
                            lambda p, f: "fraco", "e", "d").texto_puro()
    assert "│ 2 │" in texto and texto.endswith("└───┘")   # 2 é folha no desenho


def test_ciclo_na_lista_e_marcado(tmp_path):
    c = programa(tmp_path, NO + "        s.p = None\n"
                           "a = No(1)\na.p = No(2)\na.p.p = a\nfim = 1\n")
    assert "↺ " in c.desenhar(c.passos[-1]).texto_puro()


def test_indices_do_array(tmp_path):
    c = programa(tmp_path, "v = [5, 6, 7]\ni = 2\nfim = True\n")   # bool não é índice
    texto = c.desenhar(c.passos[-1]).texto_puro()
    assert re.search(r"▲\s*\n\s*i", texto)      # "▲" e embaixo dele o nome "i"
