"""Árvores binárias: nós em caixas (ou compactos), e a árvore em pedaços.

Os campos de ligação são parâmetros; eles vêm da detecção
(deteccao/formas.py), não do nome dos campos.
"""
from xray.nucleo.canvas import Canvas, lado_a_lado
from xray.renderizadores.comum import nomes_por_endereco, titulo


MAX_NIVEIS_CAIXAS = 6    # mais fundo que isso, volta ao desenho compacto (2 linhas por nível)
DESVIO = 3               # pai de filho único: colunas entre o pai e o filho


def desenhar_arvore(raiz, rotulo, tag_aresta, esq, dir):
    """Cada nó numa caixa; árvore funda demais sai no desenho compacto.

    rotulo(n)          → lista de (texto, tag) para escrever o nó
    tag_aresta(pai, f) → tag da linha que liga pai ao filho f
    """
    def f_esq(n):
        return getattr(n, esq, None)      # tolera nó ainda no __init__

    def f_dir(n):
        return getattr(n, dir, None)

    ordem, prof = [], {}                  # nós em ordem in-order; nó → profundidade
    descobertos = {}                      # nó → (esq, dir) que foram visitados a partir dele

    def visitar(n, p):
        if n is None or n in prof:        # "in prof": não entra em ciclo
            return None
        prof[n] = p
        e = visitar(f_esq(n), p + 1)      # esquerda primeiro...
        ordem.append(n)                   # ...depois o nó entra na sequência
        descobertos[n] = (e, visitar(f_dir(n), p + 1))
        return n

    visitar(raiz, 0)
    niveis = 1 + max(prof.values(), default=0)
    if niveis > MAX_NIVEIS_CAIXAS:
        return _compacta(ordem, prof, rotulo, tag_aresta, f_esq, f_dir)
    return _em_caixas(raiz, descobertos, prof, rotulo, tag_aresta, f_esq, f_dir)


def _filhos(n, prof, f_esq, f_dir):
    """Filhos desenhados no nível de baixo; ligação de volta (ciclo) fica sem linha."""
    return tuple(f if f in prof and prof[f] == prof[n] + 1 else None
                 for f in (f_esq(n), f_dir(n)))


def _ligacoes(cv, lin, x, n, e, d, centro, tag_aresta):
    """Linha de conexão com os filhos: ┌───┴───┐, com a junção na coluna x."""
    if e:
        cv.escrever(lin, centro[e] + 1, "─" * (x - centro[e] - 1), tag_aresta(n, e))
        _ponta(cv, lin, centro[e], "┌", tag_aresta(n, e))
    if d:
        cv.escrever(lin, x + 1, "─" * (centro[d] - x - 1), tag_aresta(n, d))
        _ponta(cv, lin, centro[d], "┐", tag_aresta(n, d))
    cv.escrever(lin, x, "┴" if e and d else "┘" if e else "└", "fraco")


def _ponta(cv, lin, col, canto, tag):
    """Canto sobre o canto oposto (nó com dois pais) vira ┬."""
    atual = cv.celulas.get((lin, col), (" ",))[0]
    cv.escrever(lin, col, "┬" if atual in "┌┐" and atual != canto else canto, tag)


def _em_caixas(raiz, descobertos, prof, rotulo, tag_aresta, f_esq, f_dir):
    """Nó = caixa com o valor dentro; 4 linhas por nível (3 da caixa + ligação).

    Os filhos são posicionados primeiro e o pai fica no meio deles. Caixas
    do mesmo nível precisam de um espaço entre si; se o pai não cabe, a
    subárvore inteira anda para a direita. Níveis diferentes nunca se cruzam.
    """
    largura = {n: sum(len(t) for t, _ in rotulo(n)) + 4 for n in descobertos}   # "│ " + texto + " │"
    centro, fim_do_nivel = {}, {}         # fim_do_nivel: última coluna ocupada no nível

    def meio(n):                          # da borda esquerda até a junção ┴/┬
        return (largura[n] - 1) // 2

    def ocupar(n):
        fim_do_nivel[prof[n]] = max(fim_do_nivel.get(prof[n], -2),
                                    centro[n] - meio(n) + largura[n] - 1)

    def mover(n, delta):                  # a subárvore é a última de cada nível: não colide
        centro[n] += delta
        ocupar(n)
        for f in descobertos[n]:
            if f is not None:
                mover(f, delta)

    def posicionar(n):
        e, d = descobertos[n]
        for f in (e, d):
            if f is not None:
                posicionar(f)
        if e and d:
            x = (centro[e] + centro[d]) // 2
        elif e or d:                      # filho único: um pouco para o lado dele
            x = centro[e] + DESVIO if e else centro[d] - DESVIO
        else:
            x = 0
        minimo = fim_do_nivel.get(prof[n], -2) + 2 + meio(n)
        if x < minimo:
            for f in (e, d):
                if f is not None:
                    mover(f, minimo - x)
            x = minimo
        centro[n] = x
        ocupar(n)

    posicionar(raiz)

    pais = {f: n for n in descobertos                # para o ┴ no topo da caixa
            for f in _filhos(n, prof, f_esq, f_dir) if f is not None}

    cv = Canvas()
    for n in descobertos:
        y, x, w = prof[n] * 4, centro[n], largura[n]
        col = x - (w - 1) // 2
        pedacos = rotulo(n)
        borda = "novo" if pedacos[0][1] == "novo" else "fraco"   # como na lista encadeada
        cv.escrever(y, col, "┌" + "─" * (w - 2) + "┐", borda)
        if n in pais:
            cv.escrever(y, x, "┴", tag_aresta(pais[n], n))
        cv.escrever(y + 1, col, "│ ", borda)
        fim = cv.trechos(y + 1, col + 2, pedacos)
        cv.escrever(y + 1, fim, " │", borda)
        cv.escrever(y + 2, col, "└" + "─" * (w - 2) + "┘", borda)
        e, d = _filhos(n, prof, f_esq, f_dir)
        if e or d:
            cv.escrever(y + 2, x, "┬", borda)
            _ligacoes(cv, y + 3, x, n, e, d, centro, tag_aresta)
    return cv


def _compacta(ordem, prof, rotulo, tag_aresta, f_esq, f_dir):
    """Layout por percurso em ordem: a ordem in-order vira a COLUNA do nó."""
    slot = max(sum(len(t) for t, _ in rotulo(n)) for n in ordem) + 1
    centro = {n: o * slot + slot // 2 for o, n in enumerate(ordem)}
    cv = Canvas()
    for n in ordem:
        y, x = prof[n] * 2, centro[n]     # nós nas linhas pares
        pedacos = rotulo(n)
        largura = sum(len(t) for t, _ in pedacos)
        cv.trechos(y, x - largura // 2, pedacos)
        e, d = _filhos(n, prof, f_esq, f_dir)
        if e or d:
            _ligacoes(cv, y + 1, x, n, e, d, centro, tag_aresta)
    return cv


def raizes_e_compartilhados(nos, esq, dir):
    """Entre os nós dados: quem ninguém aponta (raízes) e quem tem 2+ pais."""
    pais = {}                             # id(filho) → quantos nós apontam para ele
    for n in nos:
        for f in (getattr(n, esq, None), getattr(n, dir, None)):
            if f is not None:
                pais[id(f)] = pais.get(id(f), 0) + 1
    raizes = [n for n in nos if id(n) not in pais]   # ninguém aponta para elas
    compartilhados = [n for n in nos if pais.get(id(n), 0) > 1]
    return raizes, compartilhados


# ───────────────────────────── fluxo genérico ──────────────────────────────

def desenhar_estrutura(passo, est, d):
    """Árvore detectada (campos de ligação vindos de est.no), com rotação à vista.

    Cores: foco = apontado por variável do topo; novo = nó recém-criado ou
    aresta religada agora; destaque = nó seguro por uma chamada em aberto.
    """
    v, no = passo.vista, est.no
    esq, dir = no.ligacoes
    nos = [v.objetos[i] for i in est.objetos]
    raizes, compartilhados = raizes_e_compartilhados(nos, esq, dir)
    if not raizes:                                  # só ciclos: começa por qualquer um
        raizes = nos[:1]
    nomes = {id(v.objetos[i]): ns for i, ns in nomes_por_endereco(passo).items()
             if i in v.objetos}

    def ident(n):
        return v.enderecos[id(n)]

    def tag(n):
        if id(n) in nomes:
            return "foco"
        if ident(n) in d.novos:
            return "novo"
        return "destaque" if ident(n) in d.caminho else "normal"

    def tag_aresta(pai, filho):
        campo = esq if getattr(pai, esq, None) is filho else dir
        return "novo" if d.religou(ident(pai), campo) else "fraco"

    def rotulo(n):
        valor = getattr(n, no.valor, "?") if no.valor else v.endereco(n)
        pedacos = [(str(valor), tag(n))]
        # outros campos simples (ex.: altura numa AVL) aparecem entre parênteses
        extras = [str(x) for campo, x in vars(n).items()
                  if campo not in (no.valor, *no.ligacoes)
                  and isinstance(x, (int, float, str)) and not isinstance(x, bool)]
        if extras:
            pedacos.append(("(" + ",".join(extras) + ")", "fraco"))
        return pedacos

    cv = Canvas()
    titulo(cv, est.forma, detalhe=no.tipo)
    arvores = [desenhar_arvore(r, rotulo, tag_aresta, esq, dir) for r in raizes]
    cv.colar(lado_a_lado(arvores), 2, 2)
    base = cv.altura + 1
    legenda = []
    for n in nos:
        if id(n) in nomes:
            valor = getattr(n, no.valor, "?") if no.valor else v.endereco(n)
            legenda += [(", ".join(nomes[id(n)]), "foco"), (f" → {valor}    ", "fraco")]
    if legenda:
        cv.trechos(base, 2, [("variáveis: ", "titulo")] + legenda)
        base += 1
    if len(raizes) > 1:
        cv.escrever(base, 2, f"árvore em {len(raizes)} pedaços: nó ainda sem pai"
                    " ou rotação em andamento", "fraco")
        base += 1
    for k, n in enumerate(compartilhados):
        valor = getattr(n, no.valor, "?") if no.valor else v.endereco(n)
        cv.escrever(base + k, 2, f"o nó {valor} tem DOIS pais agora", "alerta")
    return cv
