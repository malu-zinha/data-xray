# xray

Visualizador de execução Python no terminal. O produto se chama **xray**:
comando `xray`, pacote `src/xray/`, projeto `xray` no `pyproject.toml`.
Nomes antigos (`vized`, `inspect`, `inspetor`) não devem voltar. O
repositório ainda se chama `data-visualizer` e vai virar `data-xray`;
quando isso acontecer, atualizar a URL do `git clone` e os caminhos de
pasta no README.

## Commits

- **Nunca** colocar autoria do Claude: nada de `Co-Authored-By: Claude`,
  nem "Generated with Claude Code" em commit ou PR. A autoria é só da
  dona do repositório. O `.claude/settings.json` já desliga isso; não
  reativar.
- Commits pequenos, um por unidade coerente (núcleo, desenho, interface,
  cli, testes, exemplos, docs, web). Nunca juntar tudo num commit só.
- Cada commit passa no `pytest` sozinho.
- Mensagens em português, minúsculas, no formato `área: o que mudou`
  (ex.: `desenho: valores no meio das células`, `docs: ...`).
- Push só quando pedido.

## Ambiente

- O ambiente virtual fica **fora** do repositório, em `../.venv`
  (não em `.venv`, como o README ensina para quem instala do zero).
  Rodar os testes com `../.venv/bin/pytest -q`.
- Depois de mudar `[project.scripts]` ou o nome do pacote, reinstalar com
  `../.venv/bin/pip install -e .` para o comando `xray` acompanhar.

## Gotchas

- O código usa o módulo `inspect` da biblioteca padrão
  (`nucleo/heap.py`, `nucleo/rastreador.py`): nenhum pacote ou arquivo
  do projeto pode se chamar `inspect`.
- `tests/snapshots/` guarda o desenho esperado de cada exemplo. Só
  regravar (`XRAY_ATUALIZAR=1 pytest tests/test_desenhos.py`) quando a
  mudança no desenho for intencional, e dizer isso no commit.
- `web/passo-a-passo.html` é gerado. Quando a tela ou os exemplos mudam,
  regerar com `../.venv/bin/python web/gerar_pagina.py` (precisa de
  `pip install -e ".[web]"`; leva uns 3 a 4 minutos) e commitar à parte.

## Documentação

- Tudo em português: código, comentários, mensagens e docs.
- O README é para iniciantes que nunca usaram terminal: frases curtas,
  passo a passo, sem jargão. Mudou comando, tecla ou tela → atualizar o
  README no mesmo trabalho (em commit de docs separado).
- As telas e desenhos do README são saídas reais do programa, não
  inventadas.
- `docs/ROADMAP.md` é o histórico das etapas (tags `etapa-1` a
  `etapa-6`).
