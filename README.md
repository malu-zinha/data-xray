# inspect

Execute um arquivo Python. Avance linha por linha. Veja a memória.

```
┌────┬───┐     ┌────┬───┐     ┌────┬───┐
│  1 │ ●─┼────▶│  2 │ ●─┼────▶│  3 │ ∅ │
└────┴───┘     └────┴───┘     └────┴───┘
```

Programa de terminal que executa um arquivo Python e mostra, linha por
linha:

- a linha que vai ser executada;
- a pilha de chamadas de função;
- o valor de todas as variáveis;
- um desenho da memória: objetos, listas, dicionários e as referências
  entre eles.

O programa é executado uma vez, do início ao fim, e cada linha executada
é gravada. Depois a tela abre e você navega pela gravação, avançando e
voltando um passo de cada vez.

Listas encadeadas, árvores binárias, matrizes, grafos (matriz ou lista de
adjacência), tabelas hash, arrays e filas são reconhecidos pela forma como
os objetos se ligam e ganham um desenho próprio. O resto é desenhado como
caixas (objetos) e setas (referências).

## Requisitos

- Python 3.10 ou mais novo
- git (só para baixar o projeto)
- Terminal com pelo menos 130 colunas de largura (deixe a janela larga)

Os comandos abaixo são para macOS e Linux. No Windows, as diferenças estão
indicadas nos comentários.

## Instalação

Uma vez só.

1. Abra o Terminal. No macOS: `Cmd + Espaço`, digite `Terminal` e
   aperte Enter.

2. Confira a versão do Python:

   ```bash
   python3 --version
   ```

   Tem que aparecer `Python 3.10` ou maior. Se aparecer um número menor
   ou um erro, instale o Python pelo site https://www.python.org/downloads/
   e repita o comando.

3. Entre na pasta do projeto. Se você ainda não tem o projeto no
   computador, baixe e entre na pasta:

   ```bash
   git clone https://github.com/malu-zinha/data-visualizer.git
   cd data-visualizer
   ```

   Se já tem, só entre na pasta dele. Por exemplo:

   ```bash
   cd ~/projetos/data-visualizer-repo/data-visualizer
   ```

   A partir daqui, todos os comandos são digitados **dentro dessa pasta**.

4. Crie o ambiente virtual. É uma pasta `.venv` onde ficam as
   dependências do projeto, separadas do resto do sistema:

   ```bash
   python3 -m venv .venv
   ```

5. Ative o ambiente virtual:

   ```bash
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   ```

   O começo da linha do terminal passa a mostrar `(.venv)`.

6. Instale o programa e as dependências:

   ```bash
   pip install -e .
   ```

7. Teste com um dos exemplos que vêm no projeto:

   ```bash
   inspect exemplos/bubble.py
   ```

   A tela do visualizador abre. Aperte `n` algumas vezes para avançar e
   `q` para sair. A instalação está pronta.

## Toda vez que abrir um terminal novo

O ambiente virtual precisa ser ativado de novo em cada janela de terminal:

```bash
cd ~/projetos/data-visualizer-repo/data-visualizer    # a pasta do projeto
source .venv/bin/activate                            # Windows: .venv\Scripts\activate
```

## Como o programa precisa estar

O visualizador executa o arquivo do começo ao fim, como
`python3 arquivo.py`, e mostra o que aconteceu. Se o arquivo só **define**
funções e classes e nunca as **chama**, nada é executado dentro delas, e a
tela mostra só as definições.

Para funcionar, o arquivo precisa:

1. **Chamar o código no final.** Depois das definições, escreva a entrada
   e faça a chamada, no nível do arquivo (sem indentação):

   ```python
   def soma(a, b):
       return a + b

   resultado = soma(2, 3)      # sem esta linha, soma() nunca roda
   print(resultado)
   ```

   Um bloco `if __name__ == "__main__":` também funciona.

2. **Ter os valores de entrada escritos no código.** `input()` não
   funciona, porque o programa é executado sem teclado (ver
   [Limitações](#limitações)).

3. **Rodar sem erro com `python3 arquivo.py`.** Se der erro no Python, dá
   o mesmo erro no visualizador. A gravação vai até a linha do erro.

4. **Terminar em até 2000 passos.** Use entradas pequenas (5 a 10
   elementos).

### Código copiado do LeetCode (ou de sites parecidos)

O LeetCode entrega só a classe `Solution`. Quem chama o método é o site,
por fora. Por isso, colado sozinho no arquivo, o código não mostra nada.
Faça três ajustes:

1. **Chame o método no final do arquivo**, com um exemplo do enunciado:

   ```python
   class Solution(object):
       def twoSum(self, nums, target):
           ...

   nums = [2, 7, 11, 15]
   resposta = Solution().twoSum(nums, 9)
   print(resposta)
   ```

2. **Importe os tipos usados nas anotações.** O modelo em Python 3 usa
   `List[int]`, `Optional[...]` etc. sem importar. No site funciona; no
   arquivo dá `NameError: name 'List' is not defined`. Coloque no começo
   do arquivo:

   ```python
   from typing import List, Optional
   ```

3. **Crie as classes auxiliares.** Em problemas de lista encadeada ou
   árvore, o LeetCode deixa `ListNode` e `TreeNode` num comentário no topo
   do código. Tire o `#` dessas linhas para que as classes existam, e
   monte a estrutura de entrada à mão:

   ```python
   class ListNode:
       def __init__(self, val=0, next=None):
           self.val = val
           self.next = next

   cabeca = ListNode(1, ListNode(2, ListNode(3)))
   resposta = Solution().reverseList(cabeca)
   ```

O exemplo completo está em `exemplos/twosum.py`.

## Como executar o seu próprio código

1. Crie um arquivo `.py` com o código.

   O arquivo pode ficar em qualquer pasta. O mais simples é criá-lo
   **dentro da pasta do projeto**, ao lado da pasta `exemplos/`.

   Use um editor de código, como o VS Code. Não use o TextEdit do macOS:
   ele troca as aspas e o Python não entende.

   Outra opção é criar o arquivo direto pelo terminal. Copie e cole o
   bloco inteiro abaixo (da linha `cat` até a linha `FIM`) e aperte Enter:

   ```bash
   cat > meu_programa.py <<'FIM'
   class No:
       def __init__(self, valor):
           self.valor = valor
           self.prox = None


   def inserir_no_inicio(cabeca, valor):
       novo = No(valor)
       novo.prox = cabeca
       return novo


   lista = None
   for x in [3, 2, 1]:
       lista = inserir_no_inicio(lista, x)
   print("pronto!")
   FIM
   ```

   Isso cria o arquivo `meu_programa.py` na pasta atual. Para conferir:
   `cat meu_programa.py`.

   O arquivo é um programa Python normal: não precisa importar nada do
   visualizador e também roda com `python3 meu_programa.py`.

2. Execute com o visualizador. Com o ambiente virtual ativado:

   ```bash
   inspect meu_programa.py
   ```

   Se o arquivo estiver em outra pasta, passe o caminho completo:

   ```bash
   inspect /Users/seu_usuario/Documentos/aula/exercicio.py
   ```

   No macOS, dá para arrastar o arquivo do Finder para dentro da janela
   do Terminal: o caminho completo é colado sozinho.

3. Navegue pela execução com as teclas abaixo e saia com `q`.

## Teclas

| Tecla | Ação |
|---|---|
| `n` | próximo passo |
| `p` | passo anterior |
| `espaço` | avança sozinho (um passo a cada ~0,5 s); de novo, pausa |
| `r` | volta ao primeiro passo |
| `←` `→` | troca de aba (quando há mais de um arquivo aberto) |
| `q` | sai |

Se o desenho não couber no painel da direita, role com o mouse ou o
trackpad.

## O que aparece na tela

Tela real do `meu_programa.py` acima, no passo 22 de 36. O programa está
dentro de `inserir_no_inicio`, inserindo o valor 2, e a próxima linha a
executar é `novo.prox = cabeca`:

```
 ⭘                              Visualizador de execução Python — código e memória, passo a passo
 meu_programa.py
╸━━━━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
╭─ meu_programa.py · inserir_no_inicio() ──────────────────────────╮╭─ python meu_programa.py ─────────────────────────────────────╮
│    4         self.prox = None                                    ││                                                              │
│    5                                                             ││  lista encadeada · No                                        │
│    6                                                             ││                                                              │
│    7 def inserir_no_inicio(cabeca, valor):                       ││  ┌────┬───┐                                                  │
│    8     novo = No(valor)                                        ││  │  3 │ ∅ │                                                  │
│ ❱  9     novo.prox = cabeca                                      ││  └────┴───┘                                                  │
│   10     return novo                                             ││   @ee70                                                      │
│   11                                                             ││   prox=None                                                  │
│   12                                                             ││   ▲ lista, cabeca                                            │
│   13 lista = None                                                ││                                                              │
│                                                                  ││  soltos (a cadeia acima não os alcança):                     │
╰───────────────────────────────────────── vai executar a linha 9 ─╯│  ┌────┬───┐                                                  │
╭─ memória ────────────────────────────────────────────────────────╮│  │  2 │ ∅ │                                                  │
│ pilha de chamadas                                                ││  └────┴───┘                                                  │
│   <module>()  linha 15                                           ││   @f4a0                                                      │
│ ▶   inserir_no_inicio()  linha 9                                 ││   prox=None                                                  │
│                                                                  ││   ▲ novo                                                     │
│ variáveis globais                                                ││                                                              │
│   lista = nó 3                                                   ││  variáveis globais                                           │
│   x = 2                                                          ││  ┌─────────────┐                                             │
│                                                                  ││  │ lista  nó 3 │                                             │
│ variáveis locais                                                 ││  │ x      2    │                                             │
│   cabeca = nó 3                                                  ││  └─────────────┘                                             │
│   valor = 2                                                      ││                                                              │
│   novo = nó 2                                                    ││  inserir_no_inicio()                                         │
│                                                                  ││  ┌──────────────┐                                            │
╰──────────────────────────────────────────────────────────────────╯│  │ cabeca  nó 3 │                                            │
╭─ saída ──────────────────────────────────────────────────────────╮│  │ valor   2    │                                            │
│ (nada ainda)                                                     ││                                                              │
╰──────────────────────────────────────────────────────────────────╯╰──────────────────────────────────────────────────────────────╯
 passo 22/36     ❚❚ pausado
 → aba  n próximo  p anterior  space play/pausa  r reinicia  q sair
```

| Painel | Conteúdo |
|---|---|
| Código (esquerda, em cima) | O arquivo. A linha marcada com `❱` é a que **vai** ser executada; ainda não foi. O título mostra a função atual. |
| Memória (esquerda, no meio) | A pilha de chamadas (`▶` marca a função atual), as variáveis globais e as variáveis locais da função atual. |
| Saída (esquerda, embaixo) | O que o `print()` já escreveu até este passo. |
| Desenho (direita) | A memória. Aqui, a lista com o nó 3 e o nó 2 recém-criado, ainda solto (nenhum nó aponta para ele). `▲` indica as variáveis que apontam para cada nó. Mais abaixo, as variáveis de cada função em aberto. |
| Barra de baixo | Número do passo e avisos (erro no programa, limite de passos). |

Nas variáveis aparece o conteúdo (`nó 3`, `[0, 1]`), não o endereço.
O endereço só aparece embaixo de cada nó de lista encadeada (`@ee70`),
para ligar o `prox=@ee70` de um nó ao nó para onde ele aponta. Os
endereços mudam a cada execução.

Um passo depois (passo 23), `novo.prox = cabeca` foi executada e o nó 2
passou a apontar para o nó 3. A seta nova aparece em verde:

```
lista encadeada · No

┌────┬───┐     ┌────┬───┐
│  2 │ ●─┼────▶│  3 │ ∅ │
└────┴───┘     └────┴───┘
 @f4a0          @ee70
 prox=@ee70     prox=None
 ▲ novo         ▲ lista, cabeca
```

No último passo (36), a lista está completa e a saída mostra `pronto!`:

```
lista encadeada · No

┌────┬───┐     ┌────┬───┐     ┌────┬───┐
│  1 │ ●─┼────▶│  2 │ ●─┼────▶│  3 │ ∅ │
└────┴───┘     └────┴───┘     └────┴───┘
 @b9b0          @f4a0          @ee70
 prox=@f4a0     prox=@ee70     prox=None
 ▲ lista
```

### Cores

| Cor | Significado |
|---|---|
| verde | criado ou alterado neste passo (objeto novo, valor alterado, seta religada) |
| amarelo | objeto usado por uma chamada de função ainda em aberto (por exemplo, o caminho de uma recursão); em arrays, a posição indicada por uma variável inteira (`▲ j`) |
| fundo amarelo | objeto apontado por uma variável da função atual; nome da função atual |
| ciano | referências (setas, `nó 3`) |
| cinza | endereços dos nós, índices e bordas |
| vermelho | alerta (por exemplo, um nó de árvore com dois pais durante uma rotação) |

## Estruturas reconhecidas

O reconhecimento usa só a forma dos objetos. O nome das classes e dos
campos não importa (`prox`, `next`, `esq`, `left`...).

| Estrutura | Critério | Desenho |
|---|---|---|
| lista encadeada | objeto com um campo que aponta para outro objeto da mesma classe | caixas `[valor│●]` ligadas por setas |
| lista duplamente encadeada | dois campos assim, com ida e volta (`a.x.y is a`) | caixas com setas `◀───▶` |
| árvore binária | dois campos assim, sem volta | cada nó numa caixa, ligada ao pai; outros campos do nó entre parênteses (ex.: altura); com mais de 6 níveis, volta ao desenho compacto, sem caixas |
| matriz | lista de listas, todas do mesmo tamanho | grade com índices |
| matriz de adjacência | matriz quadrada só com 0 e 1 | grade com o nome dos vértices, se houver uma lista deles no mesmo objeto |
| lista de adjacência | dicionário `vértice → lista de vértices` | `A → [B] [C]` |
| tabela hash (buckets) | lista de listas de tamanhos diferentes | `[0] ─▶ [ana] ─▶ [leo]` |
| array | lista de números ou textos apontada diretamente por uma variável | células com índice; variáveis inteiras aparecem como `▲ i` embaixo da posição |
| fila | `collections.deque` apontado diretamente por uma variável | células com `frente` e `fim` |
| outros | — | caixas e setas |

## Limitações

- **`input()` não funciona.** O programa é executado antes de a tela
  abrir, sem teclado; `input()` gera `EOFError`. Coloque os valores
  direto no código.
- **Só as linhas do arquivo informado aparecem.** Módulos importados são
  executados, mas as linhas deles não são mostradas.
- **Limite de 2000 passos.** Depois disso a gravação para e a barra de
  baixo avisa. Laços infinitos também param aí. Para mudar:
  `inspect meu_programa.py --max-passos 5000`. Prefira entradas pequenas
  (5 a 10 elementos): cada volta de laço gera vários passos.
- **Erros no programa:** a gravação vai até a linha do erro, e a mensagem
  aparece na barra de baixo.
- **Objetos da biblioteca padrão** (arquivos, datas, `random`...) aparecem
  como texto (ex.: `datetime.date(2026, 9, 28)`), sem os campos internos.
- **Tamanho do desenho:** até 60 objetos em caixas e setas, 12 itens por
  caixa e 30 células por array.
- **Definição de classes:** o corpo de uma `class` também é executado, por
  isso nos primeiros passos a pilha mostra, por exemplo, `No()`.
- Argumentos de linha de comando para o programa (`sys.argv`) não são
  repassados.

## Exemplos

Ficam na pasta `exemplos/`.

```bash
inspect                          # abre todos, um por aba (← → troca de aba)
inspect exemplos/avl.py          # abre um só
inspect avl                      # o mesmo, pelo nome
```

| Arquivo | Conteúdo |
|---|---|
| `bubble.py` | bubble sort num array |
| `lista_encadeada.py` | inserção no fim de uma lista encadeada |
| `pilha_fila.py` | pilha sobre lista e fila circular sobre vetor |
| `bst.py` | inserção recursiva em árvore binária de busca |
| `avl.py` | inserção em árvore AVL, com rotações |
| `grafo.py` | busca em largura (BFS) com matriz e lista de adjacência |
| `hash.py` | tabela hash com encadeamento |
| `turma.py` | dicionário de listas de objetos (caixas e setas) |
| `twosum.py` | Two Sum do LeetCode, com a chamada que o site faz por fora |

## Problemas comuns

| Problema | Solução |
|---|---|
| `command not found: inspect` | O ambiente virtual não está ativado. Entre na pasta do projeto e rode `source .venv/bin/activate`. |
| `No such file or directory` / `arquivo não encontrado` | O caminho do arquivo está errado. Confira com `ls` se o arquivo está na pasta atual, ou use o caminho completo. |
| Tela espremida ou cortada | Aumente a janela do terminal (130 colunas ou mais) ou diminua a fonte (`Cmd -` no macOS). |
| Barra de baixo diz "parou no limite de passos" | Use uma entrada menor ou aumente o limite com `--max-passos`. |
| Barra de baixo mostra `EOFError` | O programa usa `input()`. Troque por um valor fixo. |
| A tela só mostra as definições (`class`, `def`) e nada acontece | O arquivo não chama o código. Faça a chamada no final; ver [Como o programa precisa estar](#como-o-programa-precisa-estar). |
| `NameError: name 'List' is not defined` | Código do LeetCode sem o import. Coloque `from typing import List, Optional` no começo do arquivo. |
| Aparecem arquivos com " 2" no nome (ex.: `hash 2.py`) | A pasta está sincronizada com o iCloud (Mesa/Documentos). Apague as cópias ou mova o projeto para uma pasta fora do iCloud. |

## Desenvolvimento

Instalação com as ferramentas de teste:

```bash
pip install -e ".[dev]"
pytest                                            # todos os testes
INSPECT_ATUALIZAR=1 pytest tests/test_desenhos.py   # regrava os desenhos esperados (só após mudança intencional)
```

Os testes em `tests/test_desenhos.py` executam cada arquivo de `exemplos/`
e comparam o desenho com os arquivos em `tests/snapshots/`. Um arquivo
novo em `exemplos/` entra automaticamente nos testes e nas abas.

`python web/gerar_pagina.py` (requer `pip install -e ".[web]"`, só
macOS/Linux) grava a tela de todos os exemplos e gera
`web/passo-a-passo.html`, que abre no navegador.

O histórico do desenvolvimento está em `docs/ROADMAP.md`.

## Estrutura do código

O código fica em `src/xray/`.

| Arquivo | O quê |
|---|---|
| `cli.py` | Linha de comando. |
| `nucleo/rastreador.py` | Executa o programa com `sys.settrace` e grava um passo por linha. |
| `nucleo/heap.py` | Registra a memória de cada passo: `{endereço: descrição do objeto}`. |
| `nucleo/diferenca.py` | Compara um passo com o anterior (cores). |
| `deteccao/formas.py` | Reconhece as estruturas. |
| `renderizadores/` | Desenha cada estrutura. `generico.py` desenha caixas e setas. |
| `interface/app_textual.py` | A tela (biblioteca textual). |
