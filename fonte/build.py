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
             .replace("__PARAMS__", json.dumps(load("endings_params.json"))))
    out = os.path.join(HERE, "..", "index.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"index.html gerado: {len(D)} decisões, {len(html.encode()) // 1024} KB")

if __name__ == "__main__":
    main()
