# Roteiro: de cenários feitos à mão para qualquer código

Hoje cada estrutura tem um `cenario.py` que conhece nomes de variáveis e
valores (`raiz`, `13`, `fila`...). Com código qualquer, nada disso é conhecido
de antemão. O fluxo alvo é:

```
inspect meu_programa.py
  → rastrear         executa o arquivo e grava cada linha
  → achatar          memória → grafo {endereço: descrição rasa}
  → detectar forma   lista? árvore? grafo? matriz? array?
  → renderizar       desenho escolhido pela forma
  → interface        código + memória + desenho
```

Os cenários atuais funcionam como **gabarito**: rodar `exemplos/avl.py` pelo
fluxo genérico deve mostrar a rotação tão bem quanto `estruturas/avl/cenario.py`.

---

## Etapa 1 — linha de comando para um arquivo qualquer ✅

- `src/xray/cli.py`: `inspect caminho/programa.py` executa o arquivo com
  `runpy.run_path` sob o rastreador.
- O filtro do rastreador passa a aceitar **o arquivo da usuária** (e, depois,
  módulos locais importados por ele), em vez de `estruturas/*/codigo.py`.
- Gravar também as **variáveis globais** do módulo (`frame.f_globals` do
  frame do arquivo), filtrando módulos, funções e classes.
- Limite de passos configurável (ex.: `--max-passos 2000`) para laços longos.
- `inspect` sem argumentos continua abrindo os cenários atuais.

Pronto quando: `inspect exemplos/bubble.py` mostra o código e o painel de
memória (mesmo sem desenho especializado).

## Etapa 2 — snapshot como heap achatado (substitui o deepcopy) ✅

Motivos: `deepcopy` falha com arquivos, geradores e conexões; pode executar
`__deepcopy__` da usuária; e duas cópias são difíceis de comparar.

Modelo (como o Python Tutor):

```python
PRIMITIVOS = (int, float, str, bool, type(None))

def ref(x):
    return ("valor", x) if isinstance(x, PRIMITIVOS) else ("ref", id(x))

def achatar(raizes):
    heap, pendentes = {}, list(raizes)
    while pendentes:
        obj = pendentes.pop()
        if isinstance(obj, PRIMITIVOS) or id(obj) in heap:
            continue
        tipo = type(obj).__name__
        if isinstance(obj, (list, tuple, deque, set)):
            itens = list(obj)
            heap[id(obj)] = ("sequencia", tipo, [ref(x) for x in itens])
            pendentes += itens
        elif isinstance(obj, dict):
            heap[id(obj)] = ("dicionario", tipo, [(ref(k), ref(v)) for k, v in obj.items()])
            pendentes += list(obj.keys()) + list(obj.values())
        elif hasattr(obj, "__dict__") and not callable(obj):
            campos = vars(obj)
            heap[id(obj)] = ("objeto", tipo, {k: ref(v) for k, v in campos.items()})
            pendentes += list(campos.values())
        else:
            heap[id(obj)] = ("opaco", tipo, repr(obj)[:40])
    return heap
```

Cada `Passo` passa a ter: `quadros` (com locais como `ref`s), `globais`,
`heap`. Tudo é JSON puro, o que simplifica testes e a exportação web.

Cuidados: `id()` pode ser reaproveitado depois que um objeto morre (tratar
como objeto novo se o tipo mudar); `set` não tem ordem estável (ordenar a
representação); objetos com `__slots__` não têm `__dict__`.

Pronto quando: os testes de snapshot passam com o novo formato e nenhum
exemplo usa `deepcopy`.

Como ficou (`nucleo/heap.py`): descrições são dicionários
(`{"forma": "objeto", "tipo": "No", "campos": {...}}`) em vez de tuplas, por
legibilidade; namedtuples viram `objeto`; instâncias de classes da
biblioteca padrão (arquivos, `date`, `Random`...) viram `opaco` com o repr.
Os cenários à mão leem `passo.vista` (objetos reconstruídos do heap) e
comparam tipos por nome. O reuso de `id()` entre passos fica para a etapa 5,
onde importa.

## Etapa 3 — renderizador genérico (caixas e setas) ✅

`renderizadores/generico.py`: desenha qualquer heap como caixas de objeto com
seus campos, e setas para referências. É a rede de segurança: qualquer
programa fica visualizável, mesmo que feio.

Pronto quando: um programa arbitrário (ex.: dicionário de listas de objetos)
é desenhado sem erro.

Como ficou: colunas por profundidade na busca em largura; cada objeto tenta
ficar na altura da primeira seta que chega nele; cada seta tem sua raia
vertical e as junções (`┼`, `┴`...) saem das direções acumuladas por célula.
Seta só para a coluna seguinte — ciclos, auto-referências e alvos na mesma
coluna viram `@xxxx` escrito. Um título nunca fica na linha de onde sai a
seta de outra caixa (senão as duas se fundiriam). Limites: 60 objetos,
12 itens por caixa. Exemplo novo: `exemplos/turma.py`.

## Etapa 4 — detecção de forma + renderizadores especializados ✅

`deteccao/formas.py`, olhando o grafo, não os nomes:

| Sinal no heap | Forma |
|---|---|
| objeto com 1 campo apontando para o mesmo tipo | lista encadeada |
| 2 campos para o mesmo tipo, e `a.x.y is a` | lista duplamente encadeada |
| 2 campos para o mesmo tipo, sem volta | árvore binária |
| lista de listas quadrada com 0/1 | matriz de adjacência |
| dict de chave → lista de chaves do próprio dict | lista de adjacência |
| lista de listas de valores | buckets (tabela hash) |
| lista de primitivos | array |
| `deque` | fila |

Os renderizadores vêm do código atual, desacoplados dos nomes:

| Origem atual | Vira |
|---|---|
| `lista_encadeada/cenario.py: caixa_no` | `renderizadores/lista.py` |
| `nucleo/layout.py: desenhar_arvore, floresta` | `renderizadores/arvore.py` (campos de ligação vindos da detecção, não `esq`/`dir` fixos) |
| `array/cenario.py: desenhar_array` | `renderizadores/array.py` |
| `pilha_fila/cenario.py` (vetor circular) | `renderizadores/sequencia.py` |
| `grafo/cenario.py` (matriz + lista) | `renderizadores/grafo.py` |
| `hash/cenario.py` (buckets) | `renderizadores/buckets.py` |

Casos ambíguos continuam no genérico.

## Etapa 5 — destaques por diferença entre passos ✅

Os destaques feitos à mão têm equivalentes genéricos:

| Hoje (à mão) | Genérico |
|---|---|
| "nó novo" | endereço que não existia no passo anterior |
| "seta religada" | campo cujo `ref` mudou entre passos |
| "caminho da BST" | objetos referenciados por frames mais abaixo na pilha |
| "variável do frame atual" (`foco`) | igual ao atual |

Como ficou (`nucleo/diferenca.py`): cada campo tem uma chave (atributo,
índice, chave do dict, item do set; variáveis: `("var", nome)`); `mudados`
são as chaves cujo ref mudou, `religados` as que passaram a apontar para
outro objeto. Endereço com tipo/forma diferente do passo anterior conta como
objeto novo (id reaproveitado). Na fila (deque) só o item que entrou fica
verde: um popleft desloca todos os índices. As tags não mudam o texto, então
nenhuma snapshot foi regravada; `tests/test_diferenca.py` verifica as tags.

## Etapa 6 — exemplos como corpus de teste ✅

- Mover `estruturas/*/codigo.py` para `exemplos/` como programas completos
  (com o `preparar` e a chamada no fim do arquivo).
- `tests/test_desenhos.py` passa a rodar os exemplos pelo fluxo genérico.
- Quando o genérico cobrir todos os exemplos, `estruturas/` pode sair.

Como ficou: `inspect` sem argumentos abre os `exemplos/` como abas (`inspect avl`
é atalho para `exemplos/avl.py`); `estruturas/`, `nucleo/layout.py` e o
filtro de `codigo.py` saíram. As snapshots dos cenários à mão foram
substituídas pelas do fluxo completo sobre os exemplos (regravação
intencional). `tests/test_codigo.py` testa as funções dos próprios exemplos.
