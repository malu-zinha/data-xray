"""Texto curto para mostrar valores no painel de memória (lido do heap).

Mostra o conteúdo, nunca o endereço: `[0, 1]`, `Pessoa(nome='Ana')`, `nó 3`.
"""


def resumo(r, passo, largura=34):
    """Referência → texto de no máximo `largura` caracteres."""
    return resumo_do_heap(r, passo.heap, largura)


def resumo_do_heap(r, heap, largura=34):
    """O mesmo que `resumo`, para quem tem só o heap (e não o passo)."""
    s = _texto(r, heap, frozenset(), largura)
    return s if len(s) <= largura else s[:largura - 1] + "…"


def _texto(r, heap, abertos, largura):
    """Texto de uma referência. `abertos` = containers já em volta (contra ciclos)."""
    tipo_ref, x = r
    if tipo_ref == "valor":
        return repr(x)
    e = heap[x]
    forma, tipo = e["forma"], e["tipo"]
    if forma == "opaco":
        return e["texto"]
    if forma == "objeto":
        if tipo.startswith("No"):               # nós: só o valor
            valor = e["campos"].get("valor")
            v = "?" if valor is None else _texto(valor, heap, abertos, largura)
            return f"nó {v}"
        if x in abertos:
            return f"{tipo}(…)"                 # o objeto aponta para si mesmo
        return f"{tipo}(" + junta_campos(e["campos"], heap, abertos | {x}, largura) + ")"
    if x in abertos:
        return "[...]"                          # a lista contém a si mesma
    abertos = abertos | {x}

    def junta(refs):
        pedacos, total = [], 0
        for i in refs:
            pedacos.append(_texto(i, heap, abertos, largura))
            total += len(pedacos[-1]) + 2
            if total > largura:                 # já não cabe: não precisa do resto
                pedacos.append("…")
                break
        return ", ".join(pedacos)

    if forma == "dicionario":
        corpo = "{" + junta_pares(e["pares"], heap, abertos, largura) + "}"
        return corpo if tipo == "dict" else f"{tipo}({corpo})"
    itens = e["itens"]
    if tipo == "list":
        return "[" + junta(itens) + "]"
    if tipo == "tuple":
        return "(" + junta(itens) + ("," if len(itens) == 1 else "") + ")"
    if tipo in ("set", "frozenset"):
        if not itens:
            return f"{tipo}()"
        corpo = "{" + junta(itens) + "}"        # itens já vêm ordenados do heap
        return corpo if tipo == "set" else f"frozenset({corpo})"
    return f"{tipo}([{junta(itens)}])"          # deque e subclasses de list


def junta_pares(pares, heap, abertos, largura):
    pedacos, total = [], 0
    for k, v in pares:
        pedacos.append(f"{_texto(k, heap, abertos, largura)}: "
                       f"{_texto(v, heap, abertos, largura)}")
        total += len(pedacos[-1]) + 2
        if total > largura:
            pedacos.append("…")
            break
    return ", ".join(pedacos)


def junta_campos(campos, heap, abertos, largura):
    pedacos, total = [], 0
    for nome, v in campos.items():
        pedacos.append(f"{nome}={_texto(v, heap, abertos, largura)}")
        total += len(pedacos[-1]) + 2
        if total > largura:
            pedacos.append("…")
            break
    return ", ".join(pedacos)
