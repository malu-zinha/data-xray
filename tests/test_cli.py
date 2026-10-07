"""`inspect arquivo.py`: rastrear um programa qualquer (etapa 1 do ROADMAP)."""
import asyncio
from pathlib import Path

from textual.widgets import Static

from xray.cli import cenario_do_arquivo
from xray.interface.app_textual import VisualizadorApp

BUBBLE = Path(__file__).parent.parent / "exemplos" / "bubble.py"


def programa(tmp_path, codigo):
    """Grava um programa de teste e devolve o caminho."""
    arquivo = tmp_path / "programa.py"
    arquivo.write_text(codigo)
    return str(arquivo)


def test_bubble_roda_do_comeco_ao_fim():
    c = cenario_do_arquivo(str(BUBBLE))
    assert c.passos and c.erro is None and not c.cortado
    assert c.passos[-1].vista.globais["numeros"] == [1, 2, 5, 7, 9]
    # só linhas do próprio arquivo: nada do runpy nem do xray
    assert {q.funcao for p in c.passos for q in p.quadros} == {"<module>", "bubble_sort"}


def test_globais_sem_modulos_funcoes_classes_e_dunders(tmp_path):
    c = cenario_do_arquivo(programa(tmp_path, (
        "import math\n"
        "from typing import List, Optional\n"   # anotações de tipo (código do LeetCode)
        "Pares = List[int]\n"
        "class No:\n    pass\n"
        "def f():\n    return 1\n"
        "x = 10\n"
        "fim = True\n")))
    assert set(c.passos[-1].globais) == {"x", "fim"}


def test_global_e_local_sao_o_mesmo_objeto():
    c = cenario_do_arquivo(str(BUBBLE))
    p = next(p for p in c.passos if p.topo.funcao == "bubble_sort")
    assert p.globais["numeros"] == p.topo.locais["v"]   # mesma referência no heap
    vista = p.vista
    assert vista.globais["numeros"] is vista.topo.locais["v"]   # e na reconstrução


def test_quadro_do_modulo_nao_repete_as_globais():
    c = cenario_do_arquivo(str(BUBBLE))
    assert all(p.quadros[0].locais == {} for p in c.passos)


def test_laco_infinito_para_no_limite(tmp_path):
    c = cenario_do_arquivo(programa(tmp_path, (
        "i = 0\n"
        "while True:\n"
        "    try:\n"
        "        i += 1\n"
        "    except Exception:\n"       # não pode engolir o limite
        "        pass\n")), max_passos=50)
    assert c.cortado and len(c.passos) == 50 and c.erro is None


def test_erro_no_programa_preserva_os_passos(tmp_path):
    c = cenario_do_arquivo(programa(tmp_path, "x = [1, 2]\ny = x[5]\nz = 3\n"))
    assert isinstance(c.erro, IndexError)
    # linha 1, linha 2 (quebra), e o "return" do módulo quando o erro escapa dele
    assert [(p.evento, p.topo.linha) for p in c.passos] == [
        ("line", 1), ("line", 2), ("return", 2)]


def test_arquivo_e_gerador_viram_opaco(tmp_path):
    c = cenario_do_arquivo(programa(tmp_path, (
        "arq = open(__file__)\n"
        "gen = (x for x in range(3))\n"
        "lista = [1, 2]\n"
        "fim = 1\n")))
    p = c.passos[-1]
    assert p.heap[p.globais["arq"][1]]["forma"] == "opaco"
    assert p.heap[p.globais["gen"][1]]["forma"] == "opaco"
    assert p.vista.globais["lista"] == [1, 2]   # o resto continua descrito de verdade


def test_saida_cresce_passo_a_passo():
    c = cenario_do_arquivo(str(BUBBLE))
    assert c.saida == "antes:  [5, 2, 9, 1, 7]\ndepois: [1, 2, 5, 7, 9]\n"
    marcas = [p.saida for p in c.passos]
    assert marcas[0] == 0 and marcas[-1] == len(c.saida)
    assert marcas == sorted(marcas)             # nunca diminui


def test_input_nao_trava(tmp_path):
    c = cenario_do_arquivo(programa(tmp_path, "nome = input('nome? ')\n"))
    assert isinstance(c.erro, EOFError)         # sem teclado: fim de arquivo


def test_import_de_modulo_ao_lado_do_arquivo(tmp_path):
    (tmp_path / "ajudante.py").write_text("DOBRO = 2\n")
    c = cenario_do_arquivo(programa(tmp_path, "import ajudante\nx = ajudante.DOBRO\nfim = 1\n"))
    assert c.erro is None and c.passos[-1].globais["x"] == ("valor", 2)


def texto(app, seletor):
    """Conteúdo de um Static como texto puro."""
    return str(app.query_one(seletor, Static).render())


def test_interface_modo_arquivo():
    async def roteiro():
        app = VisualizadorApp([cenario_do_arquivo(str(BUBBLE))])
        async with app.run_test(size=(132, 36)) as piloto:
            for _ in range(6):                  # entra em bubble_sort
                await piloto.press("n")
            memoria = texto(app, "#memoria")
            assert "variáveis globais" in memoria and "numeros" in memoria
            assert "variáveis locais" in memoria and "v = [5, 2, 9, 1, 7]" in memoria
            assert "antes:" in texto(app, "#saida")
            assert "passo 7/" in texto(app, "#status")
    asyncio.run(roteiro())


def test_interface_sem_argumentos_abre_os_exemplos():
    async def roteiro():
        app = VisualizadorApp()
        async with app.run_test(size=(132, 36)) as piloto:
            assert [c.nome for c in app.cenarios][:2] == ["bubble.py", "lista_encadeada.py"]
            await piloto.press("right")          # próxima aba: a lista encadeada
            for _ in range(40):
                await piloto.press("n")
            assert "lista encadeada" in texto(app, "#desenho")
    asyncio.run(roteiro())


def test_atalho_pelo_nome_do_exemplo(monkeypatch):
    abertos = []
    monkeypatch.setattr("xray.interface.app_textual.VisualizadorApp.run",
                        lambda self: abertos.append(self.cenarios))
    from xray.cli import main
    main(["avl"])                                # = inspect exemplos/avl.py
    assert [c.nome for c in abertos[0]] == ["avl.py"]
