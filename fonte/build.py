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
             .replace("__A1__", json.dumps(A1, ensure_ascii=False))
             .replace("__TURMAS__", json.dumps(load("turmas.json"), ensure_ascii=False)))
    out = os.path.join(HERE, "..", "index.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"index.html gerado: {len(D)} decisões, {len(html.encode()) // 1024} KB")
    arquivos_do_app(os.path.join(HERE, ".."), "ceo-game", "The CEO Game", "CEO Game",
                    "Choose your own adventure: be the CEO of a startup and practice the first and second conditional.", html)
    # página do professor com o QR code do jogo (para imprimir ou projetar)
    from qr import pagina_professor
    pag = pagina_professor("The CEO Game", "2º ano · First and second conditional · Ensino Médio Integrado (IFAL)",
                           [("The CEO Game", "2º ano · First and second conditional", URL)])
    # o decodificador dos códigos de resultado entra depois do QR code (sem mexer no qr.py, que é o mesmo nos projetos)
    assert "</main>" in pag and "</head>" in pag
    pag = pag.replace("</main>", decodificador(t, load("turmas.json")) + "</main>", 1).replace("</head>", DEC_CSS + "</head>", 1)
    open(os.path.join(HERE, "..", "professor.html"), "w", encoding="utf-8", newline="\n").write(pag)
    print("professor.html gerado (QR code do jogo e decodificador)")

# ---------------- decodificador do código de resultado (na professor.html) ----------------
# O código é CG-TUR-final-caixa-reputação-ajudas-X (o mesmo resultCode() do template): X é a letra de conferência,
# 65 + (soma dos códigos dos caracteres do corpo) mod 26. Se mudar lá, mude aqui.
DEC_CSS = """<style>
.dec { margin-top: 26px; }
.dec textarea { width: 100%; box-sizing: border-box; min-height: 120px; font: 1rem ui-monospace, Consolas, monospace; color: var(--ink); background: var(--panel); border: 2px solid var(--line); border-radius: 10px; padding: 10px; }
.dec table { width: 100%; border-collapse: collapse; margin: 12px 0; background: var(--panel); font-size: .95rem; }
.dec th, .dec td { border: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }
.dec th { color: var(--berry); }
.dec .err { color: #B0413E; font-weight: 700; }
.dec .tab { overflow-x: auto; }
@media print { .dec { display: none; } }
</style>
"""

def decodificador(template, turmas):
    """Os nomes dos 9 finais saem do próprio template (ENDINGS e ENDING_ORDER), para não ficarem em dois lugares."""
    ordem = json.loads(re.search(r"const ENDING_ORDER = (\[[^\]]+\]);", template).group(1))
    bloco = template[template.index("const ENDINGS = {"):template.index("const ENDING_ORDER")]
    fins = []
    for k in ordem:
        m = re.search(r'\b' + k + r':\s*\{ tier: (\d), emoji: "([^"]+)", short: "([^"]+)"', bloco)
        assert m, f"final {k} não encontrado em ENDINGS"
        fins.append({"tier": int(m.group(1)), "nome": f"{m.group(2)} {m.group(3)}"})
    nomes = {x["id"]: x["nome"] for x in turmas}; nomes["OUT"] = "Outra turma · visitante"
    return DEC_HTML.replace("__ENDS__", json.dumps(fins, ensure_ascii=False)).replace("__TURMAS__", json.dumps(nomes, ensure_ascii=False))

DEC_HTML = r"""  <section class="dec" id="decoder">
    <h2>Decodificador dos códigos de resultado</h2>
    <p class="hint">No fim da partida, quando as três frases passam, o aluno recebe um código. Cole os códigos aqui, <b>um por linha</b>;
      pode pôr o nome antes (<i>Ana CG-I2M-7-064-071-1-K</i>). A turma vem dentro do código, e cada turma ganha a sua tabela.
      Tudo é calculado aqui mesmo, sem internet, e nada é enviado.</p>
    <textarea id="dec-in" spellcheck="false" placeholder="Ana CG-I2M-7-064-071-1-K"></textarea>
    <p><button type="button" id="dec-copy" style="font:inherit;font-weight:700;color:#fff;background:var(--berry);border:0;border-radius:10px;padding:8px 14px;cursor:pointer" hidden>📋 Copiar a tabela (para planilha)</button>
      <span class="hint" id="dec-msg"></span></p>
    <div class="tab" id="dec-out"></div>
  </section>
<script>
const ENDS = __ENDS__, TURMAS = __TURMAS__;
const DEC_RX = /CG\s*-\s*([A-Za-z0-9]{3})\s*-\s*(\d)\s*-\s*(\d{3})\s*-\s*(\d{3})\s*-\s*(\d)\s*-\s*([A-Za-z])/i;
const decCheck = body => String.fromCharCode(65 + [...body].reduce((s, c) => s + c.charCodeAt(0), 0) % 26);
const decEsc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function decLine(line) {
  const m = line.match(DEC_RX); if (!m) return line.trim() ? { bad: line.trim() } : null;
  const tur = m[1].toUpperCase(), fim = +m[2], body = `CG-${tur}-${fim}-${m[3]}-${m[4]}-${m[5]}`;
  const name = line.replace(m[0], "").replace(/^[\s:;,|–-]+|[\s:;,|–-]+$/g, "");
  return { name, tur, fim, cash: +m[3], rep: +m[4], aj: +m[5], ok: decCheck(body) === m[6].toUpperCase(), E: ENDS[fim - 1] };
}
let decRows = [];
function decRender() {
  const lines = document.getElementById("dec-in").value.split("\n").map(decLine).filter(Boolean);
  const out = document.getElementById("dec-out"), msg = document.getElementById("dec-msg");
  decRows = [];
  if (!lines.length) { out.innerHTML = ""; msg.textContent = ""; document.getElementById("dec-copy").hidden = true; return; }
  const turNome = t => TURMAS[t] || "turma " + t, FAIXA = ["fracasso", "meio-termo", "sucesso"];
  const turmas = [...new Set(lines.filter(r => r.E).map(r => r.tur))].sort();
  out.innerHTML = turmas.map(tur => {
    const rows = lines.filter(r => r.E && r.tur === tur);
    const body = rows.map(r => {
      decRows.push([r.name || "—", turNome(tur), r.E.nome, FAIXA[r.E.tier] || "", r.cash, r.rep, `${3 - r.aj} de 3`, r.ok ? "ok" : "conferir"]);
      return `<tr><td>${decEsc(r.name || "—")}</td><td>${decEsc(r.E.nome)} <span class="hint">(${FAIXA[r.E.tier] || ""})</span></td><td>💰 ${r.cash}</td><td>⭐ ${r.rep}</td>
        <td>${3 - r.aj} de 3</td><td>${r.ok ? "✓" : '<span class="err">conferir a cópia</span>'}</td></tr>`;
    }).join("");
    const okRows = rows.filter(r => r.ok), n = t => okRows.filter(r => r.E.tier === t).length;   // o resumo conta só os códigos conferidos
    return `<h3>${decEsc(turNome(tur))} · ${rows.length} ${rows.length === 1 ? "partida" : "partidas"}</h3>
      <table><thead><tr><th>Aluno</th><th>Final</th><th>Caixa</th><th>Reputação</th><th>Frases escritas sem ajuda</th><th>Cópia</th></tr></thead><tbody>${body}</tbody>
      <tfoot><tr><th>Turma <span class="hint">(códigos conferidos)</span></th><td colspan="5">sucesso: ${n(2)} · meio-termo: ${n(1)} · fracasso: ${n(0)}</td></tr></tfoot></table>`;
  }).join("");
  const bad = lines.filter(r => r.bad || !r.E), wrong = lines.filter(r => r.E && !r.ok);
  msg.textContent = [bad.length ? `${bad.length} linha(s) sem código reconhecido.` : "", wrong.length ? `${wrong.length} código(s) com a letra de conferência errada: provavelmente copiados com erro.` : ""].join(" ");
  document.getElementById("dec-copy").hidden = !decRows.length;
}
document.getElementById("dec-in").addEventListener("input", decRender);
document.getElementById("dec-copy").addEventListener("click", () => {
  const tsv = [["Aluno", "Turma", "Final", "Faixa", "Caixa", "Reputação", "Frases sem ajuda", "Cópia"], ...decRows].map(r => r.join("\t")).join("\n");
  const done = () => { document.getElementById("dec-msg").textContent = "Tabela copiada: cole na planilha."; };
  if (navigator.clipboard) navigator.clipboard.writeText(tsv).then(done, () => { prompt("Copie a tabela:", tsv); });
  else prompt("Copie a tabela:", tsv);
});
</script>
"""

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
