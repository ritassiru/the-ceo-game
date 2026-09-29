"""Gera o jogo (../index.html) a partir dos dados desta pasta.

Uso:  python3 fonte/build.py

O arquivo gerado é autossuficiente: as fontes vão embutidas, então ele funciona
no GitHub Pages, aberto direto do computador ou do celular, com ou sem internet.
"""
import base64, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
path = lambda *p: os.path.join(HERE, *p)
load = lambda f: json.load(open(path(f), encoding="utf-8"))

FACES = [
    ("Fraunces", 600, "normal", "fraunces-latin-600-normal.woff2"),
    ("Fraunces", 800, "normal", "fraunces-latin-800-normal.woff2"),
    ("Atkinson Hyperlegible", 400, "normal", "atkinson-hyperlegible-latin-400-normal.woff2"),
    ("Atkinson Hyperlegible", 400, "italic", "atkinson-hyperlegible-latin-400-italic.woff2"),
    ("Atkinson Hyperlegible", 700, "normal", "atkinson-hyperlegible-latin-700-normal.woff2"),
]

# palavras que o glossário Beginner não traduz de propósito: básicas demais ou nomes próprios
SEM_A1 = {"a", "an", "the", "i", "you", "it", "is", "are", "am", "to", "and", "of", "in", "on", "at",
          "argentina", "brazil", "costa", "ifal"}

def palavras_sem_a1(D, A1):
    """Palavras das falas e resultados que não têm tradução no nível A1."""
    irr = set()
    for b, p, pp, _ in load("irreg.json"):
        irr |= {b, b + "s", b + "es"} | set(p.split(" / ")) | set(pp.split(" / "))
        irr |= {b + "ing", b[:-1] + "ing", b + b[-1] + "ing", b[:-2] + "ying"}   # formas em -ing
    irr |= {"didn't", "wasn't", "weren't", "hadn't"}   # o jogo já trata como verbos irregulares
    textos = [d["text"] for d in D] + [d[k]["result"] for d in D for k in "ab"]
    ws = {w.lower() for s in textos for w in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", re.sub(r"\[\[[^\]]+\]\]|\{name\}", " ", s))}
    return sorted(w for w in ws if w not in A1 and w not in irr and w not in SEM_A1)

def main():
    D = load("decisions.json")
    # conferências rápidas nos dados antes de gerar
    ids = [d["id"] for d in D]
    assert len(ids) == len(set(ids)), "há dois 'id' iguais em decisions.json"
    for d in D:
        assert d["who"] in ("ana", "lee", "costa"), f"{d['id']}: conselheiro desconhecido"
        for k in "ab":
            o = d[k]
            for campo in ("label", "cash", "rep", "result", "phrase", "phrasePt"):
                assert campo in o, f"{d['id']}.{k}: falta o campo '{campo}'"
            assert "[[" not in o["label"], f"{d['id']}.{k}: rótulo de botão não pode ter [[glossário]]"
    A1 = {k: v for k, v in load("a1.json").items() if not k.startswith("_")}
    faltam = palavras_sem_a1(D, A1)
    if faltam:
        print("AVISO: palavras sem tradução no glossário Beginner (A1); acrescente em a1.json:")
        print("  " + ", ".join(faltam))

    css = "\n".join(
        f'@font-face {{ font-family: "{fam}"; font-weight: {w}; font-style: {st}; font-display: swap; '
        f'src: url(data:font/woff2;base64,{base64.b64encode(open(path("fonts", f), "rb").read()).decode()}) format("woff2"); }}'
        for fam, w, st, f in FACES)
    t = open(path("template.html"), encoding="utf-8").read()
    t = re.sub(r'<link rel="preconnect" href="https://fonts.googleapis.com">.*?display=swap" rel="stylesheet">',
               lambda m: "<style>\n" + css + "\n</style>", t, flags=re.S)
    assert "googleapis" not in t, "não foi possível embutir as fontes"
    html = (t.replace("__DECISIONS__", json.dumps(D, ensure_ascii=False))
             .replace("__IRREG__", json.dumps(load("irreg.json"), ensure_ascii=False))
             .replace("__PARAMS__", json.dumps(load("endings_params.json")))
             .replace("__A1__", json.dumps(A1, ensure_ascii=False)))
    out = os.path.join(HERE, "..", "index.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"index.html gerado: {len(D)} decisões, {len(html.encode()) // 1024} KB")

if __name__ == "__main__":
    main()
