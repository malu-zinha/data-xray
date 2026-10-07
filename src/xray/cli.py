"""Linha de comando: `inspect programa.py` rastreia um arquivo; `inspect` abre os exemplos.

Uso:
    inspect                               # os exemplos de exemplos/, uma aba cada
    inspect exemplos/bubble.py            # qualquer arquivo Python
    inspect avl                           # atalho para exemplos/avl.py
    inspect exemplos/bubble.py --max-passos 500
"""
import argparse
import os
import runpy
import sys

from xray.nucleo.cenario import Cenario
from xray.nucleo.rastreador import filtro_arquivos
from xray.renderizadores.automatico import Desenhista

MAX_PASSOS = 2000                  # laços longos: a linha do tempo para aqui

# exemplos/ fica na raiz do repositório (src/xray/cli.py → ../../exemplos);
# existe quando o pacote foi instalado em modo editável (pip install -e .)
PASTA_EXEMPLOS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              os.pardir, os.pardir, "exemplos")
# ordem das abas: do mais simples ao mais elaborado; os demais vêm depois
ORDEM = ["bubble", "lista_encadeada", "pilha_fila", "bst", "avl", "grafo", "hash", "turma"]


def executar_arquivo(caminho):
    """Roda o arquivo como se fosse `python caminho`."""
    path_antigo = list(sys.path)
    # `python arquivo.py` põe a pasta do arquivo no começo do sys.path;
    # sem isso, um `import meu_modulo` ao lado do arquivo não funcionaria
    sys.path.insert(0, os.path.dirname(os.path.abspath(caminho)))
    try:
        # run_name="__main__" faz o bloco `if __name__ == "__main__":` rodar;
        # o run_path também troca sys.argv[0] pelo caminho durante a execução
        runpy.run_path(caminho, run_name="__main__")
    finally:
        sys.path[:] = path_antigo      # devolve o sys.path como estava


def _curto(caminho):
    """Caminho relativo à pasta atual, se ficar mais curto (exemplos/avl.py)."""
    relativo = os.path.relpath(caminho)
    return caminho if relativo.startswith(os.pardir) else relativo


def cenario_do_arquivo(caminho, max_passos=MAX_PASSOS):
    """Um Cenario que rastreia o arquivo inteiro, do começo ao fim."""
    cenario = Cenario(
        nome=os.path.basename(caminho),
        operacao=f"python {_curto(caminho)}",
        preparar=dict,                         # nada a preparar: o arquivo faz tudo
        executar=lambda _estado: executar_arquivo(caminho),
        desenhar=None,                         # definido logo abaixo
        filtro=filtro_arquivos(caminho),       # grava só as linhas deste arquivo
        max_passos=max_passos,
        com_globais=True,                      # num script, quase tudo é global
        arquivo=os.path.abspath(caminho),
    )
    # detecta as formas (lista, árvore...) olhando TODOS os passos, e desenha
    # cada uma com o renderizador especializado; o resto fica em caixas e setas
    cenario.desenhar = Desenhista(lambda: cenario.passos)
    return cenario


def exemplos():
    """Caminhos dos exemplos, na ordem das abas."""
    if not os.path.isdir(PASTA_EXEMPLOS):
        return []
    nomes = sorted(f[:-3] for f in os.listdir(PASTA_EXEMPLOS) if f.endswith(".py"))
    nomes.sort(key=lambda n: ORDEM.index(n) if n in ORDEM else len(ORDEM))
    return [os.path.join(PASTA_EXEMPLOS, n + ".py") for n in nomes]


def cenarios_dos_exemplos(max_passos=MAX_PASSOS):
    return [cenario_do_arquivo(c, max_passos) for c in exemplos()]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="inspect",
        description="Mostra no terminal, passo a passo, o código rodando e a memória.")
    parser.add_argument("arquivo", nargs="?",
                        help="programa Python a visualizar, ou o nome de um exemplo "
                             "(sem ele: todos os exemplos)")
    parser.add_argument("--max-passos", type=int, default=MAX_PASSOS, metavar="N",
                        help=f"para depois de N passos (padrão: {MAX_PASSOS})")
    args = parser.parse_args(argv)

    atalho = os.path.join(PASTA_EXEMPLOS, f"{args.arquivo}.py")
    if args.arquivo is None:
        cenarios = cenarios_dos_exemplos(args.max_passos)
        if not cenarios:
            parser.error("pasta exemplos/ não encontrada (instale com pip install -e .) "
                         "— ou passe um arquivo: inspect programa.py")
    elif os.path.isfile(args.arquivo):
        cenarios = [cenario_do_arquivo(args.arquivo, args.max_passos)]
    elif os.path.isfile(atalho):                   # `inspect avl` → exemplos/avl.py
        cenarios = [cenario_do_arquivo(atalho, args.max_passos)]
    else:
        parser.error(f"arquivo não encontrado: {args.arquivo}")

    # importado aqui: `inspect --help` responde sem carregar o textual
    from xray.interface.app_textual import VisualizadorApp
    VisualizadorApp(cenarios).run()
