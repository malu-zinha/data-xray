"""Cenario: o que a interface mostra numa aba (uma execução rastreada).

A interface só conhece `Cenario`: nada de árvores, filas ou grafos.
A linha de comando (cli.py) monta um Cenario para cada arquivo.
"""
import io
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Any, Callable

from xray.nucleo.rastreador import rastrear


@dataclass
class Cenario:
    nome: str                                  # texto da aba
    operacao: str                              # ex.: "inserir_avl(raiz, 25)"
    preparar: Callable[[], dict]               # monta o estado inicial (NÃO rastreado)
    executar: Callable[[dict], Any]            # a operação rastreada, recebe o estado
    desenhar: Callable[[Any], Any]             # Passo → Canvas
    pular: tuple = ()                          # funções tratadas como "step over"
    filtro: Callable[[str], bool] = None       # quais arquivos gravar (obrigatório)
    max_passos: int = None                     # None = sem limite
    com_globais: bool = False                  # grava as globais do arquivo?
    arquivo: str = None                        # arquivo inteiro no painel de código
    _passos: list = field(default=None, repr=False)
    _rastreio: object = field(default=None, repr=False)
    _saida: str = field(default="", repr=False)

    @property
    def passos(self):
        """Linha do tempo, gerada na primeira vez que alguém pede."""
        if self._passos is None:
            estado = self.preparar()                     # estrutura pronta, fora do rastreio
            buffer = io.StringIO()                       # recebe o print() do programa
            stdin_antigo = sys.stdin
            # sem entrada: um input() recebe fim de arquivo (EOFError) em vez de
            # travar esperando o teclado antes de a interface abrir
            sys.stdin = io.StringIO()
            try:
                with redirect_stdout(buffer):            # não suja o terminal
                    rastreio = rastrear(
                        lambda: self.executar(estado),   # só isto é gravado
                        capturar=lambda: estado,         # o estado vai em cada foto
                        pular=self.pular,
                        filtro=self.filtro,
                        max_passos=self.max_passos,
                        com_globais=self.com_globais,
                        medir_saida=buffer.tell,         # posição = caracteres já escritos
                    )
            finally:
                sys.stdin = stdin_antigo
            self._passos, self._rastreio = rastreio.passos, rastreio
            self._saida = buffer.getvalue()
        return self._passos

    # Os três abaixo também disparam o rastreio: perguntar "cortou?" antes
    # de pedir os passos não pode responder com um valor de antes da execução.
    @property
    def erro(self):
        """Exceção que encerrou o programa, ou None."""
        _ = self.passos
        return self._rastreio.erro

    @property
    def cortado(self):
        """True se a linha do tempo parou no limite de passos."""
        _ = self.passos
        return self._rastreio.cortado

    @property
    def saida(self):
        """Tudo que o programa escreveu com print()."""
        _ = self.passos
        return self._saida
