"""Gera o jogo (../index.html) a partir dos dados desta pasta.

Uso:  python3 fonte/build.py

O arquivo gerado é autossuficiente: as fontes vão embutidas, então ele funciona
no GitHub Pages, aberto direto do computador ou do celular, com ou sem internet.
Gera também manifest.webmanifest e sw.js, que deixam instalar o jogo no celular
e abri-lo sem internet depois da primeira visita (os ícones vêm de icones.py).
"""
import base64, hashlib, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
path = lambda *p: os.path.join(HERE, *p)
load = lambda f: json.load(open(path(f), encoding="utf-8"))
URL = "https://ritassiru.github.io/the-ceo-game/"   # endereço publicado (GitHub Pages), usado no QR code

FACES = [
    ("Fraunces", 600, "normal", "fraunces-latin-600-normal.woff2"),
    ("Fraunces", 800, "normal", "fraunces-latin-800-normal.woff2"),
    ("Atkinson Hyperlegible", 400, "normal", "atkinson-hyperlegible-latin-400-normal.woff2"),
    ("Atkinson Hyperlegible", 400, "italic", "atkinson-hyperlegible-latin-400-italic.woff2"),
    ("Atkinson Hyperlegible", 700, "normal", "atkinson-hyperlegible-latin-700-normal.woff2"),
]

# palavras que o glossário Beginner não traduz de propósito: básicas demais ou nomes próprios
SEM_A1 = {"a", "an", "the", "i", "you", "it", "is", "are", "am", "to", "and", "of", "in", "on", "at",
          "alagoas", "argentina", "brazil", "costa", "ifal"}

def palavras_sem_a1(D, A1, cognatos):
    """Palavras das falas e resultados que não têm tradução no nível A1."""
    irr = set()
    for b, p, pp, _ in load("irreg.json"):
        irr |= {b, b + "s", b + "es"} | set(p.split(" / ")) | set(pp.split(" / "))
        irr |= {b + "ing", b[:-1] + "ing", b + b[-1] + "ing", b[:-2] + "ying"}   # formas em -ing
    irr |= {"didn't", "wasn't", "weren't", "hadn't"}   # o jogo já trata como verbos irregulares
    textos = [d["text"] for d in D] + [d[k]["result"] for d in D for k in "ab"]
    ws = {w.lower() for s in textos for w in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", re.sub(r"\[\[[^\]]+\]\]|\{name\}", " ", s))}
    return sorted(w for w in ws if w not in A1 and w not in irr and w not in SEM_A1 and w not in cognatos)

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
    a1 = load("a1.json")
    A1 = {k: v for k, v in a1.items() if not k.startswith("_")}
    faltam = palavras_sem_a1(D, A1, set(a1.get("_cognatos", [])))
    if faltam:
        print("AVISO: palavras sem tradução no glossário Beginner (A1); acrescente em a1.json (ou em _cognatos, se for cognato):")
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
    arquivos_do_app(os.path.join(HERE, ".."), "ceo-game", "The CEO Game", "CEO Game",
                    "Choose your own adventure: be the CEO of a startup and practice the first and second conditional.", html)
    # página do professor com o QR code do jogo (para imprimir ou projetar)
    from qr import pagina_professor
    pag = pagina_professor("The CEO Game", "2º ano · First and second conditional · Ensino Médio Integrado (IFAL)",
                           [("The CEO Game", "2º ano · First and second conditional", URL)])
    open(os.path.join(HERE, "..", "professor.html"), "w", encoding="utf-8", newline="\n").write(pag)
    print("professor.html gerado (QR code do jogo)")

# ---------------- aplicativo (PWA): instalar no celular e abrir sem internet ----------------
ICONES = ["icon-192.png", "icon-512.png", "apple-touch-icon.png"]
SW = r"""// GERADO por fonte/build.py. Nunca edite à mão.
// Guarda o jogo no aparelho na primeira visita; depois ele abre mesmo sem internet.
// A versão muda a cada build: o celular baixa o jogo novo na próxima vez que abrir com internet.
const CACHE = "__PREFIXO__-__VERSAO__";
const ARQUIVOS = __ARQUIVOS__;
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(ARQUIVOS.map(f => new Request(f, { cache: "reload" }))))
    .then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  // apaga só as versões antigas deste jogo (o outro projeto no mesmo site tem outro prefixo)
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith("__PREFIXO__-") && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET" || new URL(r.url).origin !== location.origin) return;
  e.respondWith(caches.open(CACHE).then(c => c.match(r, { ignoreSearch: true }).then(achou => achou ||
    // sem internet, só a página inicial vira o jogo guardado (professor.html, por exemplo, não)
    fetch(r).catch(() => r.mode === "navigate" && /\/(index\.html)?$/.test(new URL(r.url).pathname) ? c.match("index.html") : Response.error()))));
});
"""

def arquivos_do_app(raiz, prefixo, nome, curto, descricao, html):
    """Grava manifest.webmanifest e sw.js ao lado do index.html."""
    manifest = {"name": nome, "short_name": curto, "description": descricao, "lang": "en",
                "start_url": "./", "scope": "./", "display": "standalone",
                "background_color": "#F6F0E6", "theme_color": "#6D2E46",
                "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                          {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                          {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
    man = json.dumps(manifest, ensure_ascii=False, indent=1) + "\n"
    open(os.path.join(raiz, "manifest.webmanifest"), "w", encoding="utf-8", newline="\n").write(man)
    # a versão sai do conteúdo (e não do arquivo gravado), para dar o mesmo resultado no Windows e no GitHub
    versao = hashlib.sha256((html + man).encode()).hexdigest()[:12]
    arquivos = ["./", "index.html", "manifest.webmanifest"] + ICONES
    sw = SW.replace("__PREFIXO__", prefixo).replace("__VERSAO__", versao).replace("__ARQUIVOS__", json.dumps(arquivos))
    open(os.path.join(raiz, "sw.js"), "w", encoding="utf-8", newline="\n").write(sw)
    print(f"aplicativo: manifest.webmanifest e sw.js (versão {versao})")

if __name__ == "__main__":
    main()
