"""Gera web/passo-a-passo.html: a tela do app, gravada quadro a quadro.

Roda o app de verdade num pseudo-terminal, aperta "n" em cada passo de cada
exemplo (exemplos/*.py, uma aba cada) e grava a tela inteira (caractere, cor, fundo, negrito) com o
emulador de terminal pyte. A página só reexibe essas telas.

Uso (Linux/macOS; o módulo pty não existe no Windows):
    pip install -e ".[web]"
    python web/gerar_pagina.py
"""
import fcntl
import json
import os
import pty
import select
import struct
import sys
import termios
import time

import pyte

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pasta do projeto
SRC = os.path.join(RAIZ, "src")
sys.path.insert(0, SRC)                          # funciona mesmo sem instalar o pacote
from xray.cli import cenarios_dos_exemplos      # noqa: E402  (só para saber quantos passos)

W, H = 132, 36                                   # tamanho do terminal virtual


def cor(c, padrao):
    """Cor do pyte → CSS. Truecolor vem como 'rrggbb'; 'default' usa o padrão."""
    if c == "default":
        return padrao
    hexa = len(c) == 6 and all(x in "0123456789abcdefABCDEF" for x in c)
    return "#" + c if hexa else padrao


def main():
    totais = [len(c.passos) for c in cenarios_dos_exemplos()]

    pid, fd = pty.fork()                         # filho roda o app; pai lê a saída
    if pid == 0:
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", H, W, 0, 0))  # tamanho da tela
        os.environ.update(TERM="xterm-256color", LANG="C.UTF-8", COLORTERM="truecolor",
                          PYTHONPATH=SRC)
        os.chdir(RAIZ)
        os.execvp(sys.executable, [sys.executable, "-m", "xray"])

    tela = pyte.Screen(W, H)                     # terminal emulado em memória
    fluxo = pyte.ByteStream(tela)                # interpreta os escapes que o app envia

    def drenar(max_t=1.5, silencio=0.12):
        """Lê a saída até o app ficar em silêncio (terminou de redesenhar)."""
        fim, ultimo = time.time() + max_t, time.time()
        while time.time() < fim:
            pronto, _, _ = select.select([fd], [], [], 0.02)
            if pronto:
                try:
                    fluxo.feed(os.read(fd, 65536))
                    ultimo = time.time()
                except OSError:
                    return
            elif time.time() - ultimo > silencio:
                return

    # tabelas de deduplicação: muitas linhas (cabeçalho, bordas, rodapé) se repetem
    estilos, idx_estilo = [], {}
    linhas, idx_linha = [], {}

    def estilo(fg, bg, negrito):
        chave = (fg, bg, negrito)
        if chave not in idx_estilo:
            idx_estilo[chave] = len(estilos)
            estilos.append(chave)
        return idx_estilo[chave]

    def foto():
        """Tela atual → lista de índices de linha (cada linha = trechos [texto, estilo])."""
        ids = []
        for y in range(H):
            trechos, atual, st = [], "", None
            for x in range(W):
                ch = tela.buffer[y][x]
                fg, bg = cor(ch.fg, "#e0e0e0"), cor(ch.bg, "#121212")
                if ch.reverse:
                    fg, bg = bg, fg
                s = estilo(fg, bg, bool(ch.bold))
                if s != st and atual:            # estilo mudou: fecha o trecho
                    trechos.append([atual, st])
                    atual = ""
                st, atual = s, atual + (ch.data or " ")
            trechos.append([atual, st])
            chave = json.dumps(trechos, ensure_ascii=False)
            if chave not in idx_linha:
                idx_linha[chave] = len(linhas)
                linhas.append(trechos)
            ids.append(idx_linha[chave])
        return ids

    drenar(4, 0.6)                               # espera o app abrir
    quadros = []
    for c, total in enumerate(totais):
        if c:
            os.write(fd, b"\x1b[C")              # seta para a direita: próximo exemplo
            drenar(2, 0.25)
        seq = [foto()]
        for _ in range(total - 1):
            os.write(fd, b"n")                   # próximo passo
            drenar()
            seq.append(foto())
        quadros.append(seq)
        print(f"exemplo {c + 1}/{len(totais)}: {len(seq)} quadros", flush=True)
    os.write(fd, b"q")                           # fecha o app
    drenar(0.5)

    dados = json.dumps({"W": W, "H": H, "estilos": estilos, "linhas": linhas,
                        "quadros": quadros}, ensure_ascii=False, separators=(",", ":"))
    pasta = os.path.dirname(os.path.abspath(__file__))
    modelo = open(os.path.join(pasta, "modelo.html"), encoding="utf-8").read()
    saida = os.path.join(pasta, "passo-a-passo.html")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(modelo.replace("__DADOS__", dados.replace("</", "<\\/")))  # "</" fecharia o <script>
    print("gerado:", saida)


if __name__ == "__main__":
    main()
