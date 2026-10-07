"""Renderizador genérico (etapa 3 do ROADMAP): qualquer heap vira caixas e setas.

Snapshots em tests/snapshots/generico/. Para regravar após mudança INTENCIONAL:
    INSPECT_ATUALIZAR=1 pytest tests/test_generico.py
"""
import os
import re
from pathlib import Path

import pytest

from xray.cli import cenario_do_arquivo
from xray.renderizadores.generico import MAX_ITENS, MAX_OBJETOS, desenhar, montar

RAIZ = Path(__file__).parent.parent
EXEMPLOS = sorted((RAIZ / "exemplos").glob("*.py"))
PASTA = Path(__file__).parent / "snapshots" / "generico"
ATUALIZAR = os.environ.get("INSPECT_ATUALIZAR") == "1"


def todos_os_passos():
    """Passos de todos os exemplos: o genérico tem de aguentar todos."""
    for arquivo in EXEMPLOS:
        yield from cenario_do_arquivo(str(arquivo)).passos


def programa(tmp_path, codigo):
    arquivo = tmp_path / "programa.py"
    arquivo.write_text(codigo)
    return cenario_do_arquivo(str(arquivo))


def test_todos_os_passos_desenham():
    for p in todos_os_passos():
        desenhar(p)


def test_setas_nao_se_confundem():
    """Regras que mantêm as setas legíveis, em todos os passos conhecidos."""
    for p in todos_os_passos():
        m = montar(p)
        raias = [raia for _, _, raia, _, _ in m.setas]
        assert len(raias) == len(set(raias))            # cada seta tem sua raia vertical
        for lin, _, _, alvo, _ in m.setas:
            for _, _, _, outro, _ in m.setas:
                destino = m.caixa_de[outro]
                if outro != alvo and destino.x == m.caixa_de[alvo].x:
                    # nenhuma seta sai na linha onde OUTRA seta entra
                    assert lin != destino.y


def test_seta_de_variavel_para_lista(tmp_path):
    texto = desenhar(programa(tmp_path, "a = [1, 2]\nfim = 1\n").passos[-1]).texto_puro()
    assert re.search(r"│ a +●─+▶ list$", texto, re.M)   # seta reta até a lista (sem @)
    assert "│ 1 │ 2 │" in texto                      # lista de primitivos deitada


def test_ciclo_e_auto_referencia_mostram_o_conteudo(tmp_path):
    c = programa(tmp_path, (
        "class Anel:\n"
        "    def __init__(self):\n"
        "        self.eu = self\n"             # aponta para si mesmo
        "a = Anel()\n"
        "x = [1]\n"
        "x.append(x)\n"
        "fim = 1\n"))
    texto = desenhar(c.passos[-1]).texto_puro()
    assert "eu  Anel(eu=Anel(…))" in texto           # auto-referência: o conteúdo, sem @
    assert "1  [1, [...]]" in texto


def test_variavel_mostra_o_array_e_nao_o_endereco(tmp_path):
    c = programa(tmp_path, "nums = [2, 7, 11, 15]\nresposta = [0, 1]\nfim = 1\n")
    texto = c.desenhar(c.passos[-1]).texto_puro()
    assert re.search(r"resposta +\[0, 1\]", texto)
    assert re.search(r"nums +\[2, 7, 11, 15\]", texto)
    assert "array  ← resposta" in texto              # título sem endereço
    assert "@" not in texto


def test_variavel_mostra_o_no_sem_endereco(tmp_path):
    c = programa(tmp_path, (
        "class No:\n"
        "    def __init__(self, valor, prox=None):\n"
        "        self.valor = valor\n"
        "        self.prox = prox\n"
        "lista = No(3, No(4))\n"
        "fim = 1\n"))
    texto = c.desenhar(c.passos[-1]).texto_puro()
    assert re.search(r"lista +nó 3 +│", texto)


def test_lista_longa_e_truncada(tmp_path):
    c = programa(tmp_path, "grande = [[i] for i in range(30)]\nfim = 1\n")
    texto = desenhar(c.passos[-1]).texto_puro()
    assert f"+{30 - MAX_ITENS}" in texto


def test_muitos_objetos_param_no_limite(tmp_path):
    c = programa(tmp_path, (
        "class No:\n    def __init__(self, p):\n        self.p = p\n"
        "cabeca = None\n"
        "for i in range(100):\n    cabeca = No(cabeca)\n"
        "fim = 1\n"), )
    assert f"só os {MAX_OBJETOS} primeiros" in desenhar(c.passos[-1]).texto_puro()


def test_sem_variaveis(tmp_path):
    c = programa(tmp_path, "pass\n")
    assert "nenhuma variável" in desenhar(c.passos[0]).texto_puro()


def normalizar(texto):
    # endereços vêm do id() e mudam a cada execução: não fazem parte do teste
    return re.sub(r"@[0-9a-f]{4}", "@····", texto) + "\n"


@pytest.mark.parametrize("arquivo", EXEMPLOS, ids=lambda a: a.stem)
def test_snapshots(arquivo):
    passos = cenario_do_arquivo(str(arquivo)).passos
    n = len(passos)
    for k in sorted({0, n // 4, n // 2, 3 * n // 4, n - 1}):   # cinco pontos da linha do tempo
        atual = normalizar(desenhar(passos[k]).texto_puro())
        caminho = PASTA / f"{arquivo.stem}_{k:03d}.txt"
        if ATUALIZAR or not caminho.exists():
            PASTA.mkdir(parents=True, exist_ok=True)
            caminho.write_text(atual)
        assert atual == caminho.read_text(), f"desenho mudou: {caminho.name}"
