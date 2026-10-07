"""O desenho de cada exemplo continua igual? (testes de snapshot)

Cada arquivo de exemplos/ roda pelo fluxo completo (rastrear → achatar →
detectar forma → desenhar) e cinco pontos da linha do tempo são comparados
com tests/snapshots/<exemplo>_<passo>.txt.

Para (re)gerar os arquivos esperados depois de uma mudança INTENCIONAL:
    XRAY_ATUALIZAR=1 pytest tests/test_desenhos.py
"""
import os
import re
from pathlib import Path

import pytest

from xray.cli import cenario_do_arquivo

RAIZ = Path(__file__).parent.parent
EXEMPLOS = sorted((RAIZ / "exemplos").glob("*.py"))
PASTA = Path(__file__).parent / "snapshots"
ATUALIZAR = os.environ.get("XRAY_ATUALIZAR") == "1"


def normalizar(texto):
    # endereços @xxxx vêm do id() e mudam a cada execução: não fazem parte do teste
    return re.sub(r"@[0-9a-f]{4}", "@····", texto) + "\n"


@pytest.mark.parametrize("arquivo", EXEMPLOS, ids=lambda a: a.stem)
def test_todos_os_passos_desenham(arquivo):
    c = cenario_do_arquivo(str(arquivo))
    assert c.erro is None and not c.cortado     # o exemplo roda até o fim
    for passo in c.passos:                      # nenhum passo pode quebrar o desenho
        c.desenhar(passo)


@pytest.mark.parametrize("arquivo", EXEMPLOS, ids=lambda a: a.stem)
def test_snapshots(arquivo):
    c = cenario_do_arquivo(str(arquivo))
    n = len(c.passos)
    for k in sorted({0, n // 4, n // 2, 3 * n // 4, n - 1}):   # cinco pontos da linha do tempo
        atual = normalizar(c.desenhar(c.passos[k]).texto_puro())
        caminho = PASTA / f"{arquivo.stem}_{k:03d}.txt"
        if ATUALIZAR or not caminho.exists():
            PASTA.mkdir(parents=True, exist_ok=True)
            caminho.write_text(atual)
        assert atual == caminho.read_text(), f"desenho mudou: {caminho.name}"
