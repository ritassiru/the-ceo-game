"""Gerador de QR code em Python puro (sem bibliotecas), usado pelo build.py.

Faz o suficiente para links: modo byte, correção de erros nível M, versões 1 a 10
(até 213 caracteres). Segue a norma ISO/IEC 18004.

    matriz = qr("https://exemplo.com/")      # lista de linhas com True = módulo escuro
    svg = qr_svg("https://exemplo.com/")     # SVG pronto para a página
"""

# ---------- tabelas do nível M (índice = versão) ----------
EC_POR_BLOCO = [None, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26]
BLOCOS = [None, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5]
NIVEL_M = 0  # bits do nível M no formato


def _modulos_de_dados(v):
    """Quantos módulos sobram para dados e correção, tirando os padrões fixos."""
    r = (16 * v + 128) * v + 64
    if v >= 2:
        n = v // 7 + 2
        r -= (25 * n - 10) * n - 55
        if v >= 7:
            r -= 36
    return r


def _capacidade(v):
    """Bytes de dados que cabem na versão v (nível M)."""
    return _modulos_de_dados(v) // 8 - EC_POR_BLOCO[v] * BLOCOS[v]


# ---------- Reed-Solomon em GF(256), polinômio 0x11D ----------
def _mul(a, b):
    r = 0
    for i in range(7, -1, -1):
        r = (r << 1) ^ ((r >> 7) * 0x11D)
        r ^= ((b >> i) & 1) * a
    return r & 0xFF


def _divisor(grau):
    r = [0] * (grau - 1) + [1]
    raiz = 1
    for _ in range(grau):
        for j in range(grau):
            r[j] = _mul(r[j], raiz)
            if j + 1 < grau:
                r[j] ^= r[j + 1]
        raiz = _mul(raiz, 0x02)
    return r


def _resto(dados, divisor):
    r = [0] * len(divisor)
    for b in dados:
        f = b ^ r.pop(0)
        r.append(0)
        for i, c in enumerate(divisor):
            r[i] ^= _mul(c, f)
    return r


# ---------- montagem ----------
def _codewords(texto, v):
    dados = texto.encode("utf-8")
    bits = [0, 1, 0, 0]  # modo byte
    n = 8 if v < 10 else 16
    bits += [(len(dados) >> i) & 1 for i in range(n - 1, -1, -1)]
    for b in dados:
        bits += [(b >> i) & 1 for i in range(7, -1, -1)]
    cap = _capacidade(v) * 8
    bits += [0] * min(4, cap - len(bits))
    bits += [0] * (-len(bits) % 8)
    palavras = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad, i = [0xEC, 0x11], 0  # bytes de preenchimento, alternados
    while len(palavras) < _capacidade(v):
        palavras.append(pad[i % 2]); i += 1
    # separa em blocos (os curtos primeiro), calcula a correção e intercala
    nb, ec = BLOCOS[v], EC_POR_BLOCO[v]
    total = _modulos_de_dados(v) // 8
    curtos = nb - total % nb
    tam_curto = total // nb - ec
    div = _divisor(ec)
    blocos, k = [], 0
    for i in range(nb):
        t = tam_curto + (0 if i < curtos else 1)
        d = palavras[k:k + t]; k += t
        blocos.append((d, _resto(d, div)))
    saida = []
    for i in range(tam_curto + 1):
        for d, _ in blocos:
            if i < len(d):
                saida.append(d[i])
    for i in range(ec):
        for _, e in blocos:
            saida.append(e[i])
    return saida


def _alinhamento(v):
    if v == 1:
        return []
    n = v // 7 + 2
    tam = v * 4 + 17
    passo = (v * 4 + n * 2 + 1) // (n * 2 - 2) * 2
    return [6] + sorted(tam - 7 - i * passo for i in range(n - 1))


MASCARAS = [
    lambda x, y: (x + y) % 2 == 0,
    lambda x, y: y % 2 == 0,
    lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0,
    lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: x * y % 2 + x * y % 3 == 0,
    lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
]


def _matriz(texto, v, mascara):
    tam = v * 4 + 17
    m = [[False] * tam for _ in range(tam)]
    fixo = [[False] * tam for _ in range(tam)]

    def poe(x, y, escuro):
        m[y][x] = escuro; fixo[y][x] = True

    # padrões de posição (com a borda clara) e de tempo
    for cx, cy in ((3, 3), (tam - 4, 3), (3, tam - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < tam and 0 <= y < tam:
                    d = max(abs(dx), abs(dy))
                    poe(x, y, d not in (2, 4))
    for i in range(tam):
        if not fixo[6][i]: poe(i, 6, i % 2 == 0)
        if not fixo[i][6]: poe(6, i, i % 2 == 0)
    pos = _alinhamento(v)
    for ay in pos:
        for ax in pos:
            if (ax, ay) in ((6, 6), (6, tam - 7), (tam - 7, 6)):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    poe(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)
    # formato (reservado agora, escrito no fim) e versão
    _formato(poe, tam, mascara)
    if v >= 7:
        r = v
        for _ in range(12):
            r = (r << 1) ^ ((r >> 11) * 0x1F25)
        bits = v << 12 | r
        for i in range(18):
            b = (bits >> i) & 1 == 1
            a, c = tam - 11 + i % 3, i // 3
            poe(a, c, b); poe(c, a, b)
    # dados em zigue-zague, de baixo para cima e de cima para baixo
    dados = _codewords(texto, v)
    i, direita = 0, tam - 1
    while direita >= 1:
        if direita == 6:
            direita = 5
        for vert in range(tam):
            for j in range(2):
                x = direita - j
                subindo = ((direita + 1) & 2) == 0
                y = tam - 1 - vert if subindo else vert
                if not fixo[y][x] and i < len(dados) * 8:
                    m[y][x] = (dados[i >> 3] >> (7 - (i & 7))) & 1 == 1
                    i += 1
        direita -= 2
    f = MASCARAS[mascara]
    for y in range(tam):
        for x in range(tam):
            if not fixo[y][x] and f(x, y):
                m[y][x] = not m[y][x]
    return m


def _formato(poe, tam, mascara):
    dados = NIVEL_M << 3 | mascara
    r = dados
    for _ in range(10):
        r = (r << 1) ^ ((r >> 9) * 0x537)
    bits = (dados << 10 | r) ^ 0x5412
    b = lambda i: (bits >> i) & 1 == 1
    for i in range(6):
        poe(8, i, b(i))
    poe(8, 7, b(6)); poe(8, 8, b(7)); poe(7, 8, b(8))
    for i in range(9, 15):
        poe(14 - i, 8, b(i))
    for i in range(8):
        poe(tam - 1 - i, 8, b(i))
    for i in range(8, 15):
        poe(8, tam - 15 + i, b(i))
    poe(8, tam - 8, True)  # módulo escuro fixo


def _penalidade(m):
    tam, p = len(m), 0
    linhas = m + [list(c) for c in zip(*m)]
    for linha in linhas:  # sequências de 5 ou mais iguais
        run = 1
        for a, b in zip(linha, linha[1:]):
            if a == b:
                run += 1
            else:
                if run >= 5: p += run - 2
                run = 1
        if run >= 5: p += run - 2
        s = "".join("1" if c else "0" for c in linha)  # padrão parecido com o de posição
        for pad in ("10111010000", "00001011101"):
            p += 40 * sum(1 for i in range(len(s) - 10) if s[i:i + 11] == pad)
    for y in range(tam - 1):  # blocos 2x2 iguais
        for x in range(tam - 1):
            if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                p += 3
    escuros = sum(map(sum, m))
    p += abs(escuros * 20 - tam * tam * 10) // (tam * tam) * 10
    return p


def qr(texto, mascara=None):
    """Matriz do QR code (sem a margem). mascara=None escolhe a melhor."""
    n = len(texto.encode("utf-8"))
    v = next((v for v in range(1, 11) if _capacidade(v) >= n + (2 if v < 10 else 3)), None)
    if v is None:
        raise ValueError("texto longo demais para o QR code (máximo ~213 bytes)")
    if mascara is not None:
        return _matriz(texto, v, mascara)
    return min((_matriz(texto, v, k) for k in range(8)), key=_penalidade)


def qr_svg(texto, titulo=""):
    """SVG com margem de 4 módulos, preto no branco (sempre, também no modo escuro)."""
    m = qr(texto)
    tam, margem = len(m), 4
    lado = tam + 2 * margem
    caminho = "".join(f"M{x + margem},{y + margem}h1v1h-1z" for y, linha in enumerate(m) for x, c in enumerate(linha) if c)
    from html import escape
    t = f"<title>{escape(titulo)}</title>" if titulo else ""
    return (f'<svg class="qr" viewBox="0 0 {lado} {lado}" role="img" aria-label="QR code: {escape(titulo or texto)}" '
            f'shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg">{t}'
            f'<rect width="{lado}" height="{lado}" fill="#fff"/><path d="{caminho}" fill="#000"/></svg>')


# ---------- página do professor (professor.html), gerada pelo build.py ----------
PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QR codes · __TITULO__</title>
<!-- GERADO por fonte/build.py (com fonte/qr.py). Nunca edite à mão. -->
<style>
:root { --bg: #F6F0E6; --panel: #FFFFFF; --ink: #2B1721; --muted: #6E5C63; --berry: #6D2E46; --line: #D9CBBE; }
@media (prefers-color-scheme: dark) { :root { --bg: #1E1318; --panel: #2A1C23; --ink: #F1E7EA; --muted: #BFA9B1; --berry: #C77A98; --line: #4A3540; } }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: "Atkinson Hyperlegible", "Segoe UI", system-ui, sans-serif; line-height: 1.45; }
.wrap { max-width: 920px; margin: 0 auto; padding: 16px; }
h1, h2 { font-family: "Fraunces", Georgia, "Times New Roman", serif; color: var(--berry); }
h1 { margin: 0 0 4px; font-size: 1.9rem; }
.hint { color: var(--muted); margin: 0 0 6px; }
.bar { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; margin: 14px 0 18px; }
.bar button { font: inherit; font-weight: 700; color: #fff; background: var(--berry); border: 0; border-radius: 10px; padding: 10px 16px; cursor: pointer; }
.bar label { cursor: pointer; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 14px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 16px; text-align: center; break-inside: avoid; }
.card h2 { margin: 0 0 2px; font-size: 1.3rem; }
.qr { display: block; width: 100%; max-width: 240px; height: auto; margin: 10px auto 8px; border-radius: 6px; }
.url { font-family: ui-monospace, Consolas, monospace; font-size: 0.85rem; word-break: break-all; margin: 0; }
.um .grid { grid-template-columns: 1fr; }
.um .qr { max-width: min(80vh, 520px); }
.um .card h2 { font-size: 2rem; }
@media print {
  @page { size: A4; margin: 12mm; }
  body { background: #fff; color: #000; }
  .bar, .hint.tela { display: none; }
  .card { border: 1px solid #bbb; }
  .varios .grid { grid-template-columns: 1fr 1fr; }
  .varios .qr { max-width: 70mm; }
  .um .card { border: 0; page-break-after: always; }
  .um .qr { max-width: 150mm; }
}
</style>
</head>
<body class="varios">
<main class="wrap">
  <h1>QR codes · __TITULO__</h1>
  <p class="hint">__SUB__</p>
  <p class="hint tela">Para imprimir ou projetar: o aluno aponta a câmera do celular para o código e abre o link. Depois da primeira vez, funciona sem internet.</p>
  <div class="bar">
    <button type="button" onclick="print()">🖨️ Imprimir</button>
    <label><input type="radio" name="layout" value="varios" checked> vários por folha</label>
    <label><input type="radio" name="layout" value="um"> um por página (para projetar)</label>
  </div>
  <div class="grid">
__CARTOES__
  </div>
</main>
<script>
document.querySelectorAll('input[name="layout"]').forEach(r => r.addEventListener("change", () => { document.body.className = r.value; }));
</script>
</body>
</html>
"""


def pagina_professor(titulo, sub, cartoes):
    """cartoes: lista de (título, subtítulo, url)."""
    import html
    e = html.escape
    blocos = "\n".join(
        f'    <article class="card"><h2>{e(t)}</h2><p class="hint">{e(s)}</p>{qr_svg(u, t)}'
        f'<p class="url">{e(u.replace("https://", ""))}</p></article>' for t, s, u in cartoes)
    return PAGINA.replace("__TITULO__", e(titulo)).replace("__SUB__", e(sub)).replace("__CARTOES__", blocos)
