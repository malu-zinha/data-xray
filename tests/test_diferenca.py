"""Destaques por diferença entre passos (etapa 5 do ROADMAP).

As tags não aparecem no texto (as snapshots não mudam): aqui se olha a TAG
de cada trecho desenhado.
"""
from pathlib import Path

from xray.cli import cenario_do_arquivo
from xray.nucleo.diferenca import GLOBAIS, destaques
from xray.nucleo.heap import achatar, ref
from xray.nucleo.rastreador import Passo, Quadro
from xray.renderizadores import generico

RAIZ = Path(__file__).parent.parent


def exemplo(nome):
    return cenario_do_arquivo(str(RAIZ / "exemplos" / nome))


def trechos(cv, tag):
    """Textos desenhados com uma tag."""
    return [t.strip() for linha in cv.linhas() for t, g in linha if g == tag and t.strip()]


def passo(globais, quadros=()):
    """Passo montado à mão: globais {nome: objeto}."""
    heap = achatar(list(globais.values()))
    return Passo("line", list(quadros), {}, ref(None), heap,
                 {n: ref(v) for n, v in globais.items()})


# ───────────────────────────── o cálculo ───────────────────────────────────

def test_objeto_novo_e_campo_mudado():
    a = [1, 2]
    antes = passo({"a": a})
    a[1] = 9
    b = [3]
    depois = passo({"a": a, "b": b})
    d = destaques(antes, depois)
    assert id(b) in d.novos and id(a) not in d.novos
    assert d.mudou(id(a), 1) and not d.mudou(id(a), 0)
    assert d.mudou(GLOBAIS, ("var", "b"))           # variável nova também "mudou"
    assert d.religou(GLOBAIS, ("var", "b"))         # e agora aponta para um objeto


def test_id_reaproveitado_com_outro_tipo_conta_como_novo():
    antes = passo({"x": [1]})
    depois = passo({"x": [1]})
    ident = next(iter(depois.heap))
    depois.heap[ident] = {"forma": "dicionario", "tipo": "dict", "pares": []}
    antes.heap = {ident: antes.heap[next(iter(antes.heap))]}
    assert ident in destaques(antes, depois).novos


def test_caminho_sao_os_frames_de_baixo():
    no = [0]
    q1 = Quadro("f", 1, {"raiz": ref(no)}, "x.py", 1)
    q2 = Quadro("f", 1, {"raiz": ref(None)}, "x.py", 1)
    p = passo({}, [q1, q2])
    p.heap = achatar([no])
    assert destaques(None, p).caminho == {id(no)}


def test_primeiro_passo_nao_tem_mudancas():
    d = destaques(None, passo({"a": [1]}))
    assert not d.novos and not d.mudados


# ───────────────────────────── nos desenhos ────────────────────────────────

def test_lista_seta_religada_fica_verde():
    c = exemplo("lista_encadeada.py")
    # depois de `atual.prox = novo` (linha 25) vem o return de inserir_fim,
    # ainda na linha 25: é nele que a seta acabou de ser religada
    k = next(k for k, p in enumerate(c.passos) if p.evento == "return"
             and p.topo.funcao == "inserir_fim" and p.topo.linha == 25)
    assert "●─┼────▶" in trechos(c.desenhar(c.passos[k]), "novo")


def test_lista_no_novo_fica_verde():
    c = exemplo("lista_encadeada.py")
    textos = [trechos(c.desenhar(p), "novo") for p in c.passos]
    assert any("12" in t for t in textos)           # o nó 12 nasce verde num passo


def test_bubble_celulas_trocadas_ficam_verdes():
    c = exemplo("bubble.py")
    trocas = [trechos(c.desenhar(p), "novo") for p in c.passos]
    assert ["2", "5"] in trocas                      # 5 e 2 trocaram de lugar


def test_bst_caminho_da_recursao_fica_amarelo():
    c = exemplo("bst.py")
    k = max(k for k, p in enumerate(c.passos) if len(p.quadros) >= 5)
    amarelos = trechos(c.desenhar(c.passos[k]), "destaque")
    assert {"8", "10", "14"} <= set(amarelos)        # 8 → 10 → 14: o caminho até a vaga


def test_avl_aresta_religada_na_rotacao():
    c = exemplo("avl.py")
    rotacao = [c.desenhar(p) for p in c.passos if p.topo.funcao in ("rot_esq", "rot_dir")]
    assert any(any("─" in t for t in trechos(cv, "novo")) for cv in rotacao)


def test_generico_caixa_nova_e_seta_religada(tmp_path):
    arquivo = tmp_path / "p.py"
    arquivo.write_text("class C:\n    pass\nc = C()\nc.a = [1]\nfim = True\n")
    c = cenario_do_arquivo(str(arquivo))
    k = next(k for k, p in enumerate(c.passos) if p.topo.linha == 5)   # depois de c.a = [1]
    cv = c.desenhar(c.passos[k])
    assert "list" in trechos(cv, "novo")             # título da lista nova
    assert any(t.endswith("▶") for t in trechos(cv, "novo"))   # seta c.a → lista, recém-ligada


def test_destaques_mudam_so_as_cores_nao_o_texto():
    c = exemplo("turma.py")
    p = c.passos[len(c.passos) // 2]
    assert generico.desenhar(p).texto_puro() == generico.desenhar(
        p, destaques=destaques(c.passos[0], p)).texto_puro()
