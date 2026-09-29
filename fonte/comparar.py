"""Compara as partes que o the-ceo-game e o story-shelf compartilham.

Uso:  python3 fonte/comparar.py            (resumo: o que está igual e o que mudou)
      python3 fonte/comparar.py --detalhes (mostra as linhas diferentes)

Precisa das duas pastas lado a lado (…/the-ceo-game e …/story-shelf).
Algumas diferenças são de propósito (no Story Shelf: "estante" e "leitura" no
lugar de "jogo" e "partida", store.get/store.set, botões .btn.primary, verbos
com 2 ou 3 formas). O que importa é perceber quando uma correção foi feita em
um projeto e esquecida no outro.
"""
import difflib, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
PROJETOS = ("the-ceo-game", "story-shelf")
ESTE = os.path.basename(RAIZ)
OUTRO = os.path.join(os.path.dirname(RAIZ), PROJETOS[1] if ESTE == PROJETOS[0] else PROJETOS[0])

# blocos do template: começam num comentário "/* ---------------- <nome>" e vão até o próximo
BLOCOS_JS = ["configurações", "aplicativo", "My words", "áudio"]
# regras de CSS compartilhadas (pelo começo do seletor)
CSS = [".gear", "#settings", ".sheet", ".st-g", ".st-h", ".wlist", ".wcard", ".wbtns", ".wscore", ".say", ".can-speak",
       ".gloss.a1", ":root:not(.gloss-a1)", ".opt-pt", ".gloss-a1", ".no-motion", ":root[data-size"]


def ler(*p):
    with open(os.path.join(*p), encoding="utf-8") as f:
        return f.read()


def bloco_js(texto, nome):
    m = re.search(r"/\* -{10,} " + re.escape(nome) + r".*?(?=\n/\* -{10,} |\n</script>)", texto, re.S)
    return m.group(0).split("\n")[1:] if m else None   # sem a linha do título (o texto dela muda de propósito)


def regras_css(texto):
    css = texto[texto.index("<style>"):texto.index("</style>")]
    return sorted(l.strip() for l in css.split("\n") if l.strip().startswith(tuple(CSS)))


def sem_desenho(texto):
    return re.sub(r"# desenho:.*?\n\n", "", texto, flags=re.S)


def app_do_build(texto):
    i = texto.index("# ---------------- aplicativo (PWA)")
    j = texto.find('\nif __name__ == "__main__":', i)
    return texto[i:j if j > 0 else None]


def main():
    if not os.path.isdir(OUTRO):
        sys.exit(f"Não achei a pasta vizinha {OUTRO}. As duas pastas precisam estar lado a lado.")
    detalhes = "--detalhes" in sys.argv
    a, b = (RAIZ, OUTRO) if ESTE == PROJETOS[0] else (OUTRO, RAIZ)
    ta, tb = ler(a, "fonte", "template.html"), ler(b, "fonte", "template.html")
    partes = [(f"template: bloco '{n}'", bloco_js(ta, n), bloco_js(tb, n)) for n in BLOCOS_JS]
    partes += [("template: CSS compartilhado", regras_css(ta), regras_css(tb)),
               ("build.py: aplicativo (PWA)", app_do_build(ler(a, "fonte", "build.py")).split("\n"), app_do_build(ler(b, "fonte", "build.py")).split("\n")),
               ("qr.py", ler(a, "fonte", "qr.py").split("\n"), ler(b, "fonte", "qr.py").split("\n")),
               ("icones.py (sem o desenho)", sem_desenho(ler(a, "fonte", "icones.py")).split("\n"), sem_desenho(ler(b, "fonte", "icones.py")).split("\n"))]
    print(f"Comparando {PROJETOS[0]} × {PROJETOS[1]}\n")
    total = 0
    for nome, x, y in partes:
        if x is None or y is None:
            print(f"  ⚠ {nome}: não existe em {PROJETOS[0] if x is None else PROJETOS[1]}"); total += 1; continue
        diff = [l for l in difflib.unified_diff(x, y, PROJETOS[0], PROJETOS[1], lineterm="", n=0) if not l.startswith(("---", "+++", "@@"))]
        n = len(diff)
        print(f"  {'✓' if not n else '•'} {nome}: {'igual' if not n else f'{n} linhas diferentes'}")
        if n and detalhes:
            print("\n".join("      " + l for l in diff) + "\n")
        total += n > 0
    print("\n" + ("Tudo igual." if not total else f"{total} parte(s) com diferenças. Rode com --detalhes para ver; nem toda diferença é erro (veja o topo deste arquivo)."))


if __name__ == "__main__":
    main()
