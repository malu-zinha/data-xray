"""Interface textual: código executando à esquerda, memória desenhada à direita.

Uso:
    python -m xray                      # os exemplos, uma aba cada
    python -m xray programa.py          # qualquer arquivo (ver cli.py)
Teclas: ← → aba · n/p próximo/anterior · espaço play/pausa · r reinicia · q sai
"""
import linecache
import os

from rich.syntax import Syntax
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Footer, Header, Static, Tab, Tabs

from xray.cli import cenarios_dos_exemplos

from xray.nucleo.memoria import resumo

# Tags do desenho.py → estilos rich (inclui "foco": variável do frame atual)
ESTILOS = {
    "normal": "", "titulo": "bold", "destaque": "bold yellow",
    "novo": "bold green", "ok": "bright_blue", "fronteira": "magenta",
    "ponteiro": "cyan", "fraco": "bright_black", "alerta": "bold red",
    "foco": "bold black on yellow",
}


def para_text(canvas):
    """Canvas → rich.Text, trecho a trecho com o estilo de cada tag."""
    texto = Text(no_wrap=True)
    for i, segmentos in enumerate(canvas.linhas()):
        if i:
            texto.append("\n")
        for pedaco, tag in segmentos:
            texto.append(pedaco, style=ESTILOS[tag])
    return texto


class VisualizadorApp(App):
    TITLE = "Visualizador de execução Python"
    SUB_TITLE = "código e memória, passo a passo"
    CSS = """
    #corpo { height: 1fr; }
    #lateral { width: 68; }
    #codigo {
        height: 1fr;
        border: round $accent;
        border-title-color: $accent;
        padding: 0 1;
    }
    #memoria {
        height: auto;
        max-height: 16;
        border: round $secondary;
        border-title-color: $secondary;
        padding: 0 1;
    }
    #saida {
        height: auto;
        max-height: 8;
        border: round $success;
        border-title-color: $success;
        padding: 0 1;
    }
    #palco { border: round $primary; border-title-color: $primary; padding: 1 2; }
    #desenho { width: auto; }
    #status { height: 1; padding: 0 1; background: $boost; }
    """
    BINDINGS = [
        Binding("right", "aba(1)", "aba", priority=True),
        Binding("left", "aba(-1)", "", show=False, priority=True),
        Binding("n", "passo(1)", "próximo"),
        Binding("p", "passo(-1)", "anterior"),
        Binding("space", "play", "play/pausa"),
        Binding("r", "reiniciar", "reinicia"),
        Binding("q", "quit", "sair"),
    ]

    def __init__(self, cenarios=None):
        super().__init__()
        # padrão: uma aba por exemplo de exemplos/
        self.cenarios = cenarios_dos_exemplos() if cenarios is None else cenarios
        for c in self.cenarios:
            _ = c.passos                         # grava as linhas do tempo antes de abrir
        self.atual = 0                           # cenário (aba) ativo
        self.indice = 0                          # passo dentro da linha do tempo
        self.tocando = False                     # modo play ligado?

    def compose(self) -> ComposeResult:
        yield Header()
        yield Tabs(*[Tab(c.nome, id=f"c{i}") for i, c in enumerate(self.cenarios)],
                   id="abas")
        with Horizontal(id="corpo"):
            with Vertical(id="lateral"):
                yield Static(id="codigo")        # função atual com a linha destacada
                yield Static(id="memoria")       # pilha de chamadas + variáveis
                yield Static(id="saida")         # o que o print() escreveu até aqui
            with ScrollableContainer(id="palco"):
                yield Static(id="desenho")       # a memória naquele instante
        yield Static(id="status")
        yield Footer()

    def on_mount(self):
        # timer do modo play: começa pausado e chama avancar() a cada 0,45 s
        self.timer = self.set_interval(0.45, self.avancar, pause=True)
        self.redesenhar()

    def on_resize(self):
        self.redesenhar()                        # a janela do código depende da altura

    # ── troca de aba ──────────────────────────────────────────────────────
    def on_tabs_tab_activated(self, evento: Tabs.TabActivated):
        self.atual = int(evento.tab.id[1:])      # "c3" → 3
        self.indice = 0
        self.pausar()
        self.redesenhar()

    def action_aba(self, delta):
        proximo = (self.atual + delta) % len(self.cenarios)
        self.query_one(Tabs).active = f"c{proximo}"   # dispara on_tabs_tab_activated

    # ── navegação no tempo ───────────────────────────────────────────────
    def action_passo(self, delta):
        self.pausar()
        self.mover(delta)

    def mover(self, delta):
        ultimo = len(self.cenarios[self.atual].passos) - 1
        self.indice = max(0, min(ultimo, self.indice + delta))   # não sai da linha do tempo
        self.redesenhar()

    def action_play(self):
        if self.tocando:
            self.pausar()
        else:
            if self.indice == len(self.cenarios[self.atual].passos) - 1:
                self.indice = 0                   # no fim, play recomeça
            self.tocando = True
            self.timer.resume()
        self.redesenhar()

    def pausar(self):
        self.tocando = False
        if hasattr(self, "timer"):
            self.timer.pause()

    def avancar(self):
        if self.indice >= len(self.cenarios[self.atual].passos) - 1:
            self.pausar()                         # chegou ao fim da linha do tempo
            self.redesenhar()
        else:
            self.mover(1)

    def action_reiniciar(self):
        self.pausar()
        self.indice = 0
        self.redesenhar()

    # ── desenho das áreas ────────────────────────────────────────────────
    def redesenhar(self):
        cenario = self.cenarios[self.atual]
        passo = cenario.passos[self.indice]
        topo = passo.topo
        no_modulo = topo.funcao == "<module>"   # executando no nível do arquivo

        # 1) código: o arquivo inteiro, com a linha atual destacada
        codigo = self.query_one("#codigo", Static)
        codigo.update(self.janela_do_arquivo(cenario.arquivo, topo.linha, codigo))
        codigo.border_title = (os.path.basename(cenario.arquivo) if no_modulo
                               else f"{os.path.basename(cenario.arquivo)} · {topo.funcao}()")
        if passo.evento == "return" and no_modulo:
            # o módulo também "retorna" quando uma exceção escapa dele
            codigo.border_subtitle = (f"parou com erro na linha {topo.linha}"
                                      if cenario.erro is not None else "fim do programa")
        elif passo.evento == "return":
            codigo.border_subtitle = f"retornando na linha {topo.linha}"
        else:
            codigo.border_subtitle = f"vai executar a linha {topo.linha}"

        # 2) memória: pilha de chamadas (base → topo), globais e locais do topo
        mem = Text(no_wrap=True, overflow="ellipsis")
        mem.append("pilha de chamadas\n", style="bold")
        for k, q in enumerate(passo.quadros):
            no_topo = k == len(passo.quadros) - 1
            mem.append(f"{'▶ ' if no_topo else '  '}{'  ' * k}{q.funcao}()",
                       style="bold yellow" if no_topo else "")
            mem.append(f"  linha {q.linha}\n", style="bright_black")
        if passo.globais:                        # só existe no modo arquivo
            mem.append("\nvariáveis globais\n", style="bold")
            self.escrever_variaveis(mem, passo.globais, passo)
        if not no_modulo:                        # no nível do arquivo, locais = globais
            mem.append("\nvariáveis locais\n", style="bold")
            self.escrever_variaveis(mem, topo.locais, passo)
        if passo.evento == "return" and not no_modulo:
            mem.append("  retorna", style="bold green")
            mem.append(f" {resumo(passo.retorno, passo)}\n")
        memoria = self.query_one("#memoria", Static)
        memoria.update(mem)
        memoria.border_title = "memória"

        # 3) saída do print(): só o que já tinha sido escrito NESTE passo
        saida = self.query_one("#saida", Static)
        saida.display = bool(cenario.saida)      # painel some se o programa não imprime
        if cenario.saida:
            ate_aqui = cenario.saida[:passo.saida].splitlines()[-6:]   # últimas linhas
            saida.update(Text("\n".join(ate_aqui)) if ate_aqui
                         else Text("(nada ainda)", style="bright_black"))
            saida.border_title = "saída"

        # 4) memória desenhada, a partir do heap daquele passo
        self.query_one("#desenho", Static).update(para_text(cenario.desenhar(passo)))
        self.query_one("#palco").border_title = cenario.operacao

        # 5) barra de status, com avisos de como a execução terminou
        estado = "▶ tocando" if self.tocando else "❚❚ pausado"
        status = Text(f"passo {self.indice + 1}/{len(cenario.passos)}     {estado}")
        if cenario.cortado:
            status.append(f"     ⚠ parou no limite de {cenario.max_passos} passos"
                          " (--max-passos)", style="bold yellow")
        if cenario.erro is not None:
            status.append(f"     ✖ o programa terminou com erro: "
                          f"{type(cenario.erro).__name__}: {cenario.erro}", style="bold red")
        self.query_one("#status", Static).update(status)

    @staticmethod
    def escrever_variaveis(mem, variaveis, passo):
        for nome, valor in variaveis.items():
            mem.append(f"  {nome}", style="bold cyan")
            mem.append(f" = {resumo(valor, passo)}\n")

    @staticmethod
    def janela_do_arquivo(caminho, linha, widget):
        """O arquivo inteiro não cabe: mostra a janela de linhas em volta da atual."""
        linhas = linecache.getlines(caminho)     # lê (e guarda) o arquivo
        altura = widget.content_size.height or 30   # 0 antes do primeiro layout
        # centraliza a linha atual, sem passar do começo nem do fim do arquivo
        inicio = max(1, min(linha - altura // 2, len(linhas) - altura + 1))
        fim = min(len(linhas), inicio + altura - 1)
        return Syntax("".join(linhas), "python", theme="monokai",
                      line_numbers=True, line_range=(inicio, fim),
                      highlight_lines={linha}, background_color="default")
