# Comparação de ferramentas de terminal

Primeira versão do projeto: as mesmas estruturas desenhadas com quatro
abordagens, usada para escolher a ferramenta da interface principal (textual).
Não usa o rastreador: mostra um instante fixo de cada estrutura.

    python v1_ansi.py            # códigos ANSI puros (--animar para o bubble sort)
    python v2_rich.py            # rich (--animar usa rich.live)
    python v4_curses.py          # curses (Windows: pip install windows-curses)

A versão com textual evoluiu para o pacote `xray` (comando `inspect`) na raiz do repositório.
