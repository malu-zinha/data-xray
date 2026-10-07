"""Grade de caracteres com tags semânticas.

O desenho diz "este trecho é 'novo'", "este é 'destaque'"; quem mostra
na tela (a interface) decide qual cor cada tag recebe.
"""

TAGS = {
    "normal":    "texto comum",
    "titulo":    "legendas e rótulos",
    "destaque":  "em foco agora (comparando, caminho, atual)",
    "novo":      "acabou de ser criado ou religado",
    "ok":        "concluído (ordenado, processado)",
    "fronteira": "esperando (na fila da BFS)",
    "ponteiro":  "referências: head, topo, setas",
    "fraco":     "detalhes: índices, endereços, linhas",
    "alerta":    "desbalanceado / problema",
    "foco":      "variável do frame atual aponta para cá",
}


class Canvas:
    """Grade 2D de (caractere, tag) que cresce conforme se escreve."""

    def __init__(self):
        self.celulas = {}                         # (linha, coluna) → (char, tag)

    def escrever(self, lin, col, texto, tag="normal"):
        for i, ch in enumerate(texto):            # um caractere por célula
            self.celulas[(lin, col + i)] = (ch, tag)
        return col + len(texto)                   # coluna seguinte, para encadear

    def trechos(self, lin, col, pedacos):
        for texto, tag in pedacos:                # vários (texto, tag) em sequência
            col = self.escrever(lin, col, texto, tag)
        return col

    def colar(self, outro, lin, col):
        for (l, c), cel in outro.celulas.items(): # copia outro canvas deslocado
            self.celulas[(lin + l, col + c)] = cel

    @property
    def altura(self):
        return 1 + max((l for l, _ in self.celulas), default=-1)

    @property
    def largura(self):
        return 1 + max((c for _, c in self.celulas), default=-1)

    def linhas(self):
        """Lista de linhas; cada linha é uma lista de segmentos (texto, tag)."""
        saida = []
        for l in range(self.altura):
            segs, atual_txt, atual_tag = [], "", None
            ultima = max((c for ll, c in self.celulas if ll == l), default=-1)
            for c in range(ultima + 1):
                ch, tag = self.celulas.get((l, c), (" ", "normal"))  # buraco = espaço
                if tag != atual_tag and atual_txt:     # tag mudou: fecha o segmento
                    segs.append((atual_txt, atual_tag))
                    atual_txt = ""
                atual_txt += ch
                atual_tag = tag
            if atual_txt:
                segs.append((atual_txt, atual_tag))
            saida.append(segs)
        return saida

    def texto_puro(self):
        """Só os caracteres, sem tags: usado nos testes de snapshot."""
        return "\n".join("".join(t for t, _ in segs).rstrip() for segs in self.linhas())


def lado_a_lado(canvases, espaco=6):
    """Cola os canvases um ao lado do outro, com `espaco` colunas entre eles."""
    cv, col = Canvas(), 0
    for c in canvases:
        cv.colar(c, 0, col)               # cola cada desenho à direita do anterior
        col += c.largura + espaco
    return cv
