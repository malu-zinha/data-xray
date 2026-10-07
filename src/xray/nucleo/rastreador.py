"""Executa uma operação sob sys.settrace e grava um snapshot a cada linha.

É o que liga "linha do código" e "estado da memória": cada Passo guarda
qual linha VAI executar, a pilha de chamadas e a memória daquele instante
achatada num heap (ver heap.py). Um Passo é JSON puro: nada nele aponta
para objetos vivos do programa.
"""
import functools
import inspect
import os
import sys
from dataclasses import dataclass, field
from functools import cached_property

from xray.nucleo.heap import achatar, endereco, ref
from xray.nucleo.vista import reconstruir

def filtro_arquivos(*caminhos):
    """Filtro que aceita só os arquivos dados (ex.: o programa da usuária).

    Compara caminhos absolutos: o runpy compila o arquivo com o caminho
    do jeito que foi digitado ("exemplos/bubble.py"), que pode ser relativo.
    """
    alvos = {os.path.abspath(c) for c in caminhos}

    @functools.lru_cache(maxsize=None)  # um filtro por execução, cache próprio
    def filtro(caminho):
        return os.path.abspath(caminho) in alvos
    return filtro


class LimiteDePassos(BaseException):
    """Levantada pelo tracer quando a linha do tempo chega ao limite.

    Herda de BaseException (e não de Exception) de propósito: um
    `try/except Exception` no programa da usuária não a engole, então a
    execução realmente para, mesmo num `while True`.
    """


@dataclass
class Quadro:
    """Um frame da pilha de chamadas."""
    funcao: str          # nome da função ("<module>" = nível do arquivo)
    linha: int           # linha atual dentro dela
    locais: dict         # nome → ref (("valor", 3) ou ("ref", endereço))
    arquivo: str         # de onde vem o código...
    primeira_linha: int  # ...e onde a função começa


@dataclass
class Passo:
    evento: str        # "line" = vai executar a linha; "return" = está retornando
    quadros: list      # pilha de chamadas, da base para o topo
    estado: dict       # nome → ref dos objetos extras que o cenário pediu
    retorno: tuple     # ref do valor retornado (só quando evento == "return")
    heap: dict         # endereço → descrição rasa de cada objeto alcançável
    globais: dict = field(default_factory=dict)   # nome → ref das globais do arquivo
    saida: int = 0     # quantos caracteres de print() já tinham saído até aqui

    @property
    def topo(self):
        return self.quadros[-1]                 # frame que está executando

    def endereco(self, r):
        """Rótulo '@xxxx' de uma referência. O endereço é o id() do objeto
        original, então o mesmo nó mostra o mesmo @xxxx em todos os passos."""
        return endereco(r[1])

    @cached_property
    def vista(self):
        """Os mesmos dados como objetos (n.esq, g.adj[v]...), para os desenhos."""
        return reconstruir(self)


@dataclass
class Rastreio:
    """Tudo que uma execução rastreada produziu."""
    passos: list                   # a linha do tempo
    resultado: object = None       # o que chamada() devolveu
    erro: Exception = None         # exceção do programa, se ele quebrou
    cortado: bool = False          # True = parou no limite de passos


def global_visivel(nome, valor):
    """As globais que interessam: sem __dunder__, módulos, funções, classes e tipos.

    Módulos, funções, classes e anotações de tipo (List, Optional... do
    typing) não são "dados" do programa, só poluiriam o painel e o heap.
    """
    if nome.startswith("__") and nome.endswith("__"):
        return False                            # __name__, __builtins__, __file__...
    return not (inspect.ismodule(valor) or inspect.isroutine(valor)
                or inspect.isclass(valor) or type(valor).__module__ == "typing")


def rastrear(chamada, filtro, capturar=dict, pular=(), max_passos=None,
             com_globais=False, medir_saida=None):
    """Roda `chamada()` e devolve um Rastreio.

    filtro       recebe o caminho do arquivo de um frame; só grava se devolver True
    capturar     função sem argumentos que devolve {nome: objeto} extras a fotografar
    pular        nomes de funções tratadas como "step over" (não entra nelas)
    max_passos   limite da linha do tempo (None = sem limite)
    com_globais  grava também as variáveis globais do arquivo observado
    medir_saida  função sem argumentos que diz quanto de stdout já saiu
    """
    passos = []

    def interessa(frame):
        codigo = frame.f_code
        return filtro(codigo.co_filename) and codigo.co_name not in pular

    def registrar(frame, evento, retorno=None):
        if max_passos is not None and len(passos) >= max_passos:
            raise LimiteDePassos                # interrompe o programa observado
        pilha = []
        f = frame
        while f is not None:                    # sobe pela cadeia de chamadas
            if interessa(f):
                pilha.append(f)
            f = f.f_back
        pilha.reverse()                         # base primeiro, topo por último
        # no nível do arquivo, f_locals É o dicionário de globais: deixa vazio
        # para não mostrar tudo duas vezes (as globais vêm à parte)
        locais = [{} if f.f_code.co_name == "<module>" else dict(f.f_locals)
                  for f in pilha]
        globais = {}
        if com_globais:                         # globais do frame mais perto da base
            globais = {k: v for k, v in pilha[0].f_globals.items()
                       if global_visivel(k, v)}
        estado = capturar()
        # um único heap com tudo que qualquer variável alcança
        raizes = [v for loc in locais for v in loc.values()]
        raizes += list(globais.values()) + list(estado.values()) + [retorno]
        heap = achatar(raizes)

        def refs(variaveis):
            return {nome: ref(v) for nome, v in variaveis.items()}

        quadros = [Quadro(f.f_code.co_name, f.f_lineno, refs(loc),
                          f.f_code.co_filename, f.f_code.co_firstlineno)
                   for f, loc in zip(pilha, locais)]
        saida = medir_saida() if medir_saida else 0
        passos.append(Passo(evento, quadros, refs(estado), ref(retorno), heap,
                            refs(globais), saida))

    def tracer(frame, evento, arg):
        if not interessa(frame):
            return None                         # não rastreia este frame
        if evento == "line":
            registrar(frame, "line")            # dispara ANTES de a linha executar
        elif evento == "return":
            registrar(frame, "return", arg)     # arg = valor retornado
        return tracer                           # continua rastreando este frame

    rastreio = Rastreio(passos)
    sys.settrace(tracer)                        # liga o rastreio
    try:
        rastreio.resultado = chamada()
    except LimiteDePassos:
        rastreio.cortado = True                 # parou de propósito no limite
    except Exception as erro:
        rastreio.erro = erro                    # o programa quebrou: os passos ficam
    finally:
        sys.settrace(None)                      # desliga mesmo se der erro
    return rastreio
