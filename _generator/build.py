#!/usr/bin/env python3
"""Generator okładki README dla github.com/z0z6.
Tworzy SVG (jasne + ciemne) z osadzonymi, przyciętymi fontami oraz README.md."""
import base64, io, json, math, os, subprocess, collections, html
from fontTools.ttLib import TTFont
from fontTools import subset as ftsubset

SRC = '/home/claude/src'
OUT = '/home/claude/out'
ASSETS = 'assets/profile'
FD = '/home/claude/build/node_modules/@fontsource'
os.makedirs(os.path.join(OUT, ASSETS), exist_ok=True)

# ---------------------------------------------------------------- fonts
FONTS = {
    'B':  ('zB',  f'{FD}/bricolage-grotesque/files/bricolage-grotesque-%s-400-normal.woff2'),
    'BM': ('zBM', f'{FD}/bricolage-grotesque/files/bricolage-grotesque-%s-600-normal.woff2'),
    'BB': ('zBB', f'{FD}/bricolage-grotesque/files/bricolage-grotesque-%s-800-normal.woff2'),
    'M':  ('zM',  f'{FD}/jetbrains-mono/files/jetbrains-mono-%s-400-normal.woff2'),
}
_tt = {}
def tt(key, sub):
    k = (key, sub)
    if k not in _tt:
        _tt[k] = TTFont(FONTS[key][1] % sub)
    return _tt[k]

def adv(key, ch):
    for sub in ('latin', 'latin-ext'):
        f = tt(key, sub); cm = f.getBestCmap()
        if ord(ch) in cm:
            return f['hmtx'][cm[ord(ch)]][0] / f['head'].unitsPerEm
    return 0.55

def width(s, key, size, ls=0):
    return sum(adv(key, c) for c in s) * size + ls * max(len(s) - 1, 0)

def wrap(s, key, size, maxw):
    lines, cur = [], ''
    for w in s.split():
        t = (cur + ' ' + w).strip()
        if width(t, key, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def font_css(used):
    css = []
    for key, chars in used.items():
        fam = FONTS[key][0]
        lat_cm = tt(key, 'latin').getBestCmap()
        for sub in ('latin', 'latin-ext'):
            cm = tt(key, sub).getBestCmap()
            cps = sorted({ord(c) for c in chars if ord(c) in cm and (sub == 'latin' or ord(c) not in lat_cm)})
            if not cps: continue
            opts = ftsubset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['kern', 'liga']
            opts.name_IDs = []; opts.notdef_outline = False; opts.hinting = False
            f = TTFont(FONTS[key][1] % sub)
            sb = ftsubset.Subsetter(opts); sb.populate(unicodes=cps); sb.subset(f)
            buf = io.BytesIO(); f.flavor = 'woff2'; f.save(buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            rng = ','.join('U+%04X' % c for c in cps)
            css.append(f"@font-face{{font-family:{fam};src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{rng}}}")
    return ''.join(css)

# ---------------------------------------------------------------- themes
THEMES = {
    'dark': dict(bg='#0b0d12', surface='#11141b', surface2='#151922', line='#242936', faint='#1d212c',
                 ink='#f1f3f7', muted='#8d93a3', dim='#5d6373',
                 A='#7b8cff', Bc='#3ad6a2', C='#ff7c5a', D='#6b7180'),
    'light': dict(bg='#ffffff', surface='#f6f7f9', surface2='#f1f3f6', line='#e3e6ec', faint='#e4e7ed',
                  ink='#12141a', muted='#5c6271', dim='#9aa0ad',
                  A='#3245e6', Bc='#0c9a70', C='#ee4f2a', D='#9aa0ad'),
}

class SVG:
    def __init__(self, w, h, theme, title):
        self.w, self.h, self.t, self.title = w, h, THEMES[theme], title
        self.parts, self.used, self.css = [], collections.defaultdict(set), []
    def add(self, s): self.parts.append(s)
    def text(self, x, y, s, key='B', size=16, fill='ink', anchor='start', ls=0, extra=''):
        self.used[key].update(s)
        fill = self.t.get(fill, fill)
        a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
        l = f' letter-spacing="{ls}"' if ls else ''
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONTS[key][0]}" font-size="{size}" fill="{fill}"{a}{l}{extra}>{html.escape(s)}</text>')
    def runs(self, x, y, segs, key='B', size=16):
        """segs: [(text, color)] — jedna linia z kolorowanymi fragmentami."""
        out = []
        for s, c in segs:
            self.used[key].update(s)
            out.append(f'<tspan fill="{self.t.get(c, c)}">{html.escape(s)}</tspan>')
        self.add(f'<text x="{x}" y="{y}" font-family="{FONTS[key][0]}" font-size="{size}" xml:space="preserve">{"".join(out)}</text>')
    def c(self, k): return self.t.get(k, k)
    def render(self):
        css = font_css(self.used) + ''.join(self.css) + '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-label="{html.escape(self.title)}">'
                f'<title>{html.escape(self.title)}</title><style>{css}</style>' + ''.join(self.parts) + '</svg>')

def save(name, theme, svg):
    p = os.path.join(OUT, ASSETS, f'{name}-{theme}.svg')
    open(p, 'w').write(svg.render())
    return p

# ---------------------------------------------------------------- data
LANG = {'.gd': 'GDScript', '.gdshader': 'GDScript', '.kt': 'Kotlin', '.kts': 'Kotlin', '.dart': 'Dart',
        '.js': 'JavaScript', '.mjs': 'JavaScript', '.ts': 'JavaScript', '.py': 'Python', '.rs': 'Rust',
        '.java': 'Kotlin', '.cpp': 'C++', '.html': 'HTML/CSS', '.css': 'HTML/CSS'}
loc, langtot = {}, collections.Counter()
for d in sorted(os.listdir(SRC)):
    fs = subprocess.run(['git', '-C', os.path.join(SRC, d), 'ls-files'], capture_output=True, text=True).stdout.split('\n')
    n = 0
    for f in fs:
        if not f or any(x in f for x in ['node_modules', '/dist/', '.min.', 'vendor', 'three.module']): continue
        if d == 'TRON' and f.startswith('3d/'): continue
        e = os.path.splitext(f)[1]
        if e not in LANG: continue
        try: k = sum(1 for _ in open(os.path.join(SRC, d, f), errors='ignore'))
        except Exception: continue
        if k > 20000: continue
        n += k; langtot[LANG[e]] += k
    loc[d] = max(n, 50)

# repo, nazwa, opis, platformy, stos
P = {
 'A': dict(no='01', title='Szkoła i terapia', sub='Dokumentacja, komunikacja i codzienna praca w SOSW i WTZ.', items=[
   ('ipet-wopfu-helper', 'Asystent IPET', 'Dokumentacja ucznia z orzeczeniem: od skanu orzeczenia do gotowego IPET i WOPFU w .docx.', 'Windows · Linux · Android', 'Electron · Capacitor · Tesseract'),
   ('gwarek', 'Gwarek', 'Komunikator AAC na tablety i komputery. Działa w pełni offline.', 'Android · Windows', 'Kotlin · C++'),
   ('dziennik', 'Dziennik WTZ', 'Dziennik psychologa w stałym formacie, prowadzony razem z agentem AI.', 'Windows · Linux', 'Electron · Claude'),
   ('skryba', 'Skryba', 'Opinie psychologiczne pisane według jednego, stałego wzoru.', 'Windows · Linux', 'Electron'),
   ('minitor', 'Monitor prawa', 'Codziennie wyławia nowe akty prawne, które dotyczą placówki.', 'Windows · Linux · Android', 'Electron · JS'),
   ('lista', 'Listy obecności', 'Ujednolicone listy obecności pracowników generowane do .docx.', 'Windows', 'Python'),
   ('inglisz', 'English Buddy', 'Rozmowy po angielsku z awatarem AI na wybranym poziomie.', 'Android', 'Kotlin · Gemini'),
 ]),
 'B': dict(no='02', title='Narzędzia, które działają lokalnie', sub='Twoje dane zostają na urządzeniu. Bez kont tam, gdzie się da.', items=[
   ('szept', 'Szept', 'Szyfrowany komunikator P2P: bez kont, bez numeru telefonu, bez serwera.', 'Android · Linux · Win · macOS', 'Rust · Kotlin'),
   ('tax', 'Asystent PIT', 'Z pasków wypłat liczy podatek za rok i przewiduje dopłatę lub zwrot.', 'Windows · Linux · Android', 'Electron · OCR'),
   ('watcher', 'WatchPL', 'Monitor zdarzeń w płn.-wsch. Polsce z oceną wiarygodności doniesień.', 'Android', 'Flutter · Python'),
   ('Tracko', 'Tracko', 'Tracker aktywności z GPS: ranking, wyścig duchów i planer tras.', 'Android · Web', 'Kotlin · Supabase'),
   ('cointracko', 'CoinTracko', 'Notowania kryptowalut na żywo, alerty i wykresy z jednego kodu.', 'Linux · Windows · Android', 'Electron · Capacitor'),
   ('cinemaker', 'Kadr Studio', 'Edytor wideo z osią czasu, wieloma torami i eksportem przez FFmpeg.', 'Windows · Linux', 'Electron · FFmpeg'),
   ('melodico', 'Sampler', 'Sampler, looper i mini-deck w estetyce konsolety DJ.', 'Android', 'Kotlin · Compose'),
   ('steps', 'Dot Steps', 'Licznik kroków w stylu matrycy kropek, z trybem E-ink.', 'Android', 'Kotlin · Compose'),
   ('vr', 'VR Player', 'Odtwarzacz wideo 360° do gogli typu Cardboard.', 'Android', 'Kotlin · OpenGL'),
 ]),
 'C': dict(no='03', title='Gry, w które sam chcę grać', sub='Od pościgu po prawdziwym mieście po kosmos w przeglądarce.', items=[
   ('GTA26', 'Uciekaj przed windykatorem', 'Pościg z widokiem z góry po prawdziwym Makowie Mazowieckim, odtworzonym z OpenStreetMap.', 'Android · Web', 'Godot 4.4 · GDScript'),
   ('Teegarden-B', 'Teegarden-B', 'Gra kosmiczna budowana krok po kroku, każdy etap działa osobno.', 'Web', 'Three.js'),
   ('8w1', 'Retro Arcade', 'Hub gier na telefon. Na start Marble Maze sterowany przechyłem.', 'Android', 'Godot 4.4 · Jolt'),
   ('TRON', 'Light Cycles', 'Świetlne motocykle w 2D i 3D: AI, multiplayer online, power-upy.', 'Web', 'Three.js · Vite'),
   ('SuperMayoBros', 'Łąkowa Przygoda', 'Platformówka z jednym plikiem gry dla przeglądarki i Androida.', 'Web · Android', 'HTML5 · WebView'),
   ('metaverse', 'Galeria', 'Wirtualna sala wystawowa w przeglądarce, z trybem VR (WebXR).', 'Web · VR', 'Three.js · WebXR'),
   ('brawl', 'Arena Brawl', 'Arena offline: Ty kontra sześć botów w trybie Showdown.', 'Android', 'Kotlin'),
 ]),
 'D': dict(no='04', title='Drobiazgi', sub='', items=[
   ('foto', 'foto', 'galeria zdjęć', '', ''), ('odliczanie', 'odliczanie', 'licznik z panelem', '', ''),
   ('rotacja', 'rotacja', 'obracany model 3D', '', ''), ('z0z6', 'z0z6', 'strona z projektami', '', ''),
 ]),
}
PCOL = {'A': 'A', 'B': 'Bc', 'C': 'C', 'D': 'D'}
NREPO = sum(len(p['items']) for p in P.values())
lmin, lmax = math.log(min(loc.values())), math.log(max(loc.values()))
def lnorm(r): return (math.log(loc[r]) - lmin) / (lmax - lmin)
TOTAL = sum(langtot.values())

def bg_grid(s, pid, pitch=24, r=1.1, fade=True):
    s.add(f'<defs><pattern id="{pid}" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse">'
          f'<circle cx="{pitch/2}" cy="{pitch/2}" r="{r}" fill="{s.c("line")}"/></pattern>'
          f'<radialGradient id="{pid}f" cx="0.3" cy="0.35" r="0.85"><stop offset="0" stop-color="#fff"/>'
          f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
          f'<mask id="{pid}m"><rect width="100%" height="100%" fill="url(#{pid}f)"/></mask></defs>')
    s.add(f'<rect width="{s.w}" height="{s.h}" fill="url(#{pid})" mask="url(#{pid}m)"/>')

# ---------------------------------------------------------------- hero
GLYPH = {
 'z': ['.....', '.....', '#####', '...#.', '..#..', '.#...', '#####'],
 '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
 '6': ['..##.', '.#...', '#....', '####.', '#...#', '#...#', '.###.'],
}
def hero(theme):
    W, H = 1200, 560
    s = SVG(W, H, theme, 'z0z6 — szkoła i terapia, narzędzia lokalne, gry')
    s.css.append('.w{animation:w 4.8s ease-in-out infinite}@keyframes w{0%,100%{opacity:1}50%{opacity:.28}}'
                 '.p{animation:p 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}'
                 '@keyframes p{0%,100%{transform:scale(1)}50%{transform:scale(1.35)}}'
                 '.b{animation:b 1.6s steps(1) infinite}@keyframes b{50%{opacity:0}}')
    s.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="30" fill="{s.c("bg")}" stroke="{s.c("line")}"/>')
    bg_grid(s, 'hg')
    # górny pasek
    s.text(64, 64, 'z0z6', 'M', 14, 'ink')
    s.text(108, 64, '/ github.com/z0z6', 'M', 14, 'dim')
    s.add(f'<circle class="p" cx="{W-246}" cy="59" r="4" fill="{s.c("Bc")}"/>')
    s.text(W-232, 64, 'open source · Polska', 'M', 14, 'muted')
    # wordmark z kropek
    pitch, r, x0, y0 = 25, 8.6, 64 + 12.5, 112
    word = 'z0z6'
    accents = {(0, 6, 4): 'A', (1, 3, 2): 'Bc', (3, 0, 3): 'C'}
    for gi, ch in enumerate(word):
        g = GLYPH[ch]
        for ry, row in enumerate(g):
            for cx_, v in enumerate(row):
                col = gi * 6 + cx_
                x, y = x0 + col * pitch, y0 + ry * pitch
                if v == '#':
                    acc = accents.get((gi, ry, cx_))
                    fill = s.c(acc) if acc else s.c('ink')
                    cls = 'p' if acc else 'w'
                    s.add(f'<circle class="{cls}" style="animation-delay:{col*0.11 + ry*0.04:.2f}s" cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')
                else:
                    s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*0.42:.1f}" fill="{s.c("faint")}"/>')
    # kursor
    cxp = x0 + 23 * pitch + 4
    s.add(f'<rect class="b" x="{cxp:.1f}" y="{y0 + 6*pitch - r:.1f}" width="{r*1.6:.1f}" height="{r*2}" rx="2" fill="{s.c("ink")}"/>')
    # bio
    by, bs = 344, 27
    s.runs(64, by, [('Buduję aplikacje dla ', 'ink'), ('szkół specjalnych', 'A')], 'BM', bs)
    s.runs(64, by + 38, [('i warsztatów terapii', 'A'), (', ', 'ink'), ('narzędzia, które', 'Bc')], 'BM', bs)
    s.runs(64, by + 76, [('działają lokalnie', 'Bc'), (', i ', 'ink'), ('gry, w które sam', 'C')], 'BM', bs)
    s.runs(64, by + 114, [('chcę grać', 'C'), ('.', 'ink')], 'BM', bs)
    s.text(64, H - 48, 'Android · Windows · Linux · Web', 'M', 14, 'muted')
    s.text(64 + width('Android · Windows · Linux · Web', 'M', 14) + 18, H - 48, '//  JavaScript · Kotlin · Godot · Rust', 'M', 14, 'dim')
    # panel matrycy
    px, py, pw, ph = 708, 96, 436, 412
    s.add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="22" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
    s.text(px + 28, py + 42, 'MATRYCA REPOZYTORIÓW', 'M', 12, 'dim', ls=2)
    s.text(px + pw - 28, py + 42, f'{NREPO:02d}', 'M', 12, 'ink', anchor='end', ls=2)
    ry_ = py + 82
    labels = {'A': 'szkoła i terapia', 'B': 'narzędzia lokalne', 'C': 'gry', 'D': 'drobiazgi'}
    for key in 'ABCD':
        items = sorted(P[key]['items'], key=lambda it: -loc[it[0]])
        s.text(px + 28, ry_, P[key]['no'], 'M', 13, PCOL[key])
        s.text(px + 58, ry_, labels[key], 'M', 13, 'muted')
        s.text(px + pw - 28, ry_, f'{len(items):02d}', 'M', 13, 'dim', anchor='end')
        for i, it in enumerate(items):
            rr = 3.6 + 11.4 * lnorm(it[0])
            cx = px + 28 + 15 + i * 42
            s.add(f'<circle cx="{cx}" cy="{ry_ + 30}" r="15" fill="none" stroke="{s.c("line")}"/>')
            s.add(f'<circle cx="{cx}" cy="{ry_ + 30}" r="{rr:.1f}" fill="{s.c(PCOL[key])}"><title>{it[0]} · ~{loc[it[0]]} linii</title></circle>')
        ry_ += 76
    s.text(px + 28, py + ph - 22, 'wielkość kropki = ilość kodu', 'M', 12, 'dim')
    return s

# ---------------------------------------------------------------- language strip
LCOL = {'JavaScript': 'ink', 'Kotlin': 'A', 'GDScript': 'C', 'HTML/CSS': 'dim', 'Rust': 'Bc', 'Python': '#a58bff', 'Dart': '#2fb6d8', 'C++': 'line'}
def langs(theme):
    W, H = 1200, 150
    s = SVG(W, H, theme, 'Języki w repozytoriach z0z6')
    items = langtot.most_common()
    s.text(4, 30, 'KOD', 'M', 12, 'dim', ls=2)
    tot_k = round(TOTAL / 1000)
    s.text(W - 4, 30, f'≈ {tot_k} tys. linii · {NREPO} repozytoriów', 'M', 12, 'dim', anchor='end', ls=1)
    # pasek z kropek: 96 kolumn x 2 wiersze
    cols, pitch = 96, 1192 / 96
    counts, acc = [], 0.0
    for name, v in items:
        acc += v / TOTAL * cols; counts.append((name, acc))
    ci, prev = 0, 0
    for name, edge in counts:
        e = round(edge)
        for c in range(prev, e):
            for row in range(2):
                s.add(f'<circle cx="{4 + pitch/2 + c*pitch:.1f}" cy="{58 + row*14}" r="4.6" fill="{s.c(LCOL[name])}"/>')
        prev = e
    x = 4
    for name, v in items:
        pct = v / TOTAL * 100
        lab = f'{name} {pct:.0f}%' if pct >= 1 else f'{name} <1%'
        s.add(f'<circle cx="{x+5}" cy="{119}" r="5" fill="{s.c(LCOL[name])}"/>')
        s.text(x + 16, 124, lab, 'M', 13, 'muted')
        x += 16 + width(lab, 'M', 13) + 30
    return s

# ---------------------------------------------------------------- section header
def section(key, theme):
    p = P[key]; W, H = 1200, 150
    s = SVG(W, H, theme, f'{p["no"]} {p["title"]}')
    s.add(f'<line x1="4" y1="20" x2="{W-4}" y2="20" stroke="{s.c("line")}"/>')
    s.text(4, 62, p['no'], 'M', 15, PCOL[key], ls=1)
    s.text(40, 62, f'/ 03', 'M', 15, 'dim', ls=1)
    s.text(2, 112, p['title'], 'BB', 46, 'ink', ls=-0.8)
    s.text(4, 142, p['sub'], 'B', 19, 'muted')
    n = len(p['items'])
    for i in range(n):
        s.add(f'<circle cx="{W - 10 - i*20}" cy="57" r="6" fill="{s.c(PCOL[key])}" opacity="{1 - i*0.09:.2f}"/>')
    s.text(W - 4, 112, f'{n} repo', 'M', 15, 'dim', anchor='end')
    return s

# ---------------------------------------------------------------- cards
def meter(s, xr, y, repo, key, n=10, r=3.2, pitch=10):
    lit = max(1, round(n * (0.15 + 0.85 * lnorm(repo))))
    for i in range(n):
        cx = xr - (n - 1 - i) * pitch
        s.add(f'<circle cx="{cx:.1f}" cy="{y}" r="{r}" fill="{s.c(PCOL[key]) if i < lit else s.c("faint")}"/>')

def arrow(s, x, y, col):
    s.add(f'<path d="M{x} {y+10} L{x+10} {y} M{x+2} {y} H{x+10} V{y+8}" stroke="{s.c(col)}" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')

def card(key, it, theme):
    repo, name, desc, plat, stack = it
    W, H = 400, 270
    s = SVG(W, H, theme, f'{name} — {desc}')
    s.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="24" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
    s.add(f'<circle cx="34" cy="40" r="5" fill="{s.c(PCOL[key])}"/>')
    s.text(48, 45, plat.upper(), 'M', 12, 'dim', ls=1.2)
    arrow(s, W - 42, 33, 'dim')
    size = 34
    while width(name, 'BB', size, -0.5) > W - 60 and size > 22: size -= 1
    s.text(27, 102, name, 'BB', size, 'ink', ls=-0.5)
    ds = 20
    lines = wrap(desc, 'B', ds, W - 58)
    if len(lines) > 3:
        ds = 18; lines = wrap(desc, 'B', ds, W - 58)
    for i, l in enumerate(lines[:3]):
        s.text(28, 138 + i * 26, l, 'B', ds, 'muted')
    s.add(f'<line x1="28" y1="{H-58}" x2="{W-28}" y2="{H-58}" stroke="{s.c("line")}"/>')
    s.text(28, H - 26, stack, 'M', 13, 'ink')
    meter(s, W - 31, H - 30, repo, key)
    return s

def featured_ipet(it, theme):
    repo, name, desc, plat, stack = it
    W, H = 1200, 340
    s = SVG(W, H, theme, f'{name} — {desc}')
    s.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="28" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
    s.add(f'<circle cx="44" cy="50" r="6" fill="{s.c("A")}"/>')
    s.text(60, 55, 'FLAGOWY · ' + plat.upper(), 'M', 13, 'dim', ls=1.4)
    s.text(38, 128, name, 'BB', 62, 'ink', ls=-1.2)
    for i, l in enumerate(wrap(desc, 'B', 24, 560)):
        s.text(40, 176 + i * 33, l, 'B', 24, 'muted')
    s.text(40, H - 40, stack, 'M', 14, 'ink')
    meter(s, 640, H - 45, repo, 'A', n=14, r=3.6, pitch=11)
    # prawa strona: pseudonimizacja
    bx, byy, bw, bh = 700, 36, 464, 268
    s.add(f'<rect x="{bx}" y="{byy}" width="{bw}" height="{bh}" rx="20" fill="{s.c("bg")}" stroke="{s.c("line")}"/>')
    s.text(bx + 26, byy + 38, 'PSEUDONIMIZACJA · PRZED WYSŁANIEM DO AI', 'M', 11.5, 'dim', ls=1.3)
    rows = [
        [('{{UCZEN}}', 'A'), (' funkcjonuje na poziomie', 'muted')],
        [('niepełnosprawności w stopniu', 'muted')],
        [('umiarkowanym. Orzeczenie ', 'muted'), ('{{NR}}', 'A')],
        [('z poradni ', 'muted'), ('{{PORADNIA}}', 'A'), (',', 'muted')],
        [('PESEL ', 'muted'), ('{{PESEL}}', 'A'), (' · OCR lokalny', 'muted')],
    ]
    for i, segs in enumerate(rows):
        s.runs(bx + 26, byy + 76 + i * 28, segs, 'M', 15)
    # pigułki dokumentów
    pills = ['WOPFU', 'IPET', 'ICF ×9', 'KES', 'AAC', '.docx']
    x = bx + 26; y = byy + bh - 34
    for ptxt in pills:
        w = width(ptxt, 'M', 12.5) + 24
        s.add(f'<rect x="{x}" y="{y-17}" width="{w:.1f}" height="26" rx="13" fill="none" stroke="{s.c("A")}" stroke-opacity="0.55"/>')
        s.text(x + 12, y + 1, ptxt, 'M', 12.5, 'A')
        x += w + 8
    return s

def featured_gta(it, theme):
    repo, name, desc, plat, stack = it
    W, H = 1200, 340
    s = SVG(W, H, theme, f'{name} — {desc}')
    s.css.append('.m{animation:m 3.2s ease-in-out infinite}@keyframes m{0%,100%{opacity:.9}50%{opacity:.35}}')
    s.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="28" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
    s.add(f'<circle cx="44" cy="50" r="6" fill="{s.c("C")}"/>')
    s.text(60, 55, 'FLAGOWA GRA · ' + plat.upper(), 'M', 13, 'dim', ls=1.4)
    size = 62
    while width(name, 'BB', size, -1.2) > 620 and size > 30: size -= 1
    s.text(38, 126, name, 'BB', size, 'ink', ls=-1.2)
    for i, l in enumerate(wrap(desc, 'B', 24, 560)):
        s.text(40, 174 + i * 33, l, 'B', 24, 'muted')
    s.text(40, H - 40, stack, 'M', 14, 'ink')
    meter(s, 640, H - 45, repo, 'C', n=14, r=3.6, pitch=11)
    # mapa z prawdziwych budynków (data/buildings.json)
    b = json.load(open(f'{SRC}/GTA26/data/buildings.json'))
    pts = [(sum(o['p'][0::2]) / len(o['p'][0::2]), sum(o['p'][1::2]) / len(o['p'][1::2])) for o in b]
    bx, byy, bw, bh = 700, 36, 464, 268
    s.add(f'<rect x="{bx}" y="{byy}" width="{bw}" height="{bh}" rx="20" fill="{s.c("bg")}" stroke="{s.c("line")}"/>')
    cols, rows_, pitch = 50, 24, 8.6
    minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
    band = (maxx - minx) * rows_ / cols
    ys = sorted(p[1] for p in pts)
    best = max(range(0, int(ys[-1] - band), 5), key=lambda y0: sum(1 for y in ys if y0 <= y < y0 + band))
    miny, maxy = best, best + band
    pts = [p for p in pts if miny <= p[1] < maxy]
    grid = collections.Counter()
    for x, y in pts:
        gx = int((x - minx) / (maxx - minx + 1e-6) * cols)
        gy = int((y - miny) / (maxy - miny + 1e-6) * rows_)
        grid[(gx, gy)] += 1
    mx = max(grid.values())
    ox, oy = bx + (bw - cols * pitch) / 2 + pitch / 2, byy + 24 + pitch / 2
    for gy in range(rows_):
        for gx in range(cols):
            v = grid.get((gx, gy), 0)
            cx, cy = ox + gx * pitch, oy + gy * pitch
            if v:
                rr = 1.6 + 2.2 * min(1, math.sqrt(v / mx) * 1.4)
                s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="{s.c("ink")}" opacity="0.85"/>')
            else:
                s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="0.9" fill="{s.c("line")}"/>')
    # gracz i pościg
    (kx, ky), _ = max(grid.items(), key=lambda kv: kv[1] - 0.02 * ((kv[0][0] - cols/2)**2 + (kv[0][1] - rows_/2)**2))
    gxp, gyp = ox + (kx + 2) * pitch, oy + ky * pitch
    s.add(f'<circle class="m" cx="{gxp:.1f}" cy="{gyp:.1f}" r="16" fill="{s.c("C")}" opacity="0.25"/>')
    s.add(f'<circle cx="{gxp:.1f}" cy="{gyp:.1f}" r="5.5" fill="{s.c("C")}"/>')
    for dx, dy in [(-5, -3), (-6, 3), (-3, 5)]:
        s.add(f'<circle cx="{gxp + dx*pitch:.1f}" cy="{gyp + dy*pitch:.1f}" r="4" fill="none" stroke="{s.c("C")}" stroke-width="2"/>')
    s.text(bx + 24, byy + bh - 14, f'MAKÓW MAZOWIECKI · BUDYNKI Z OPENSTREETMAP', 'M', 11.5, 'dim', ls=1.3)
    return s

def footer(theme):
    W, H = 1200, 120
    s = SVG(W, H, theme, 'z0z6')
    s.css.append('.f{animation:f 3.6s ease-in-out infinite}@keyframes f{0%,100%{opacity:.2}50%{opacity:1}}')
    n = 60
    for i in range(n):
        y = 40 + 14 * math.sin(i / n * math.pi * 4)
        col = ['A', 'Bc', 'C'][int(i / n * 3)]
        s.add(f'<circle class="f" style="animation-delay:{i*0.06:.2f}s" cx="{10 + i*(1180/(n-1)):.1f}" cy="{y:.1f}" r="3.2" fill="{s.c(col)}"/>')
    s.text(W / 2, 100, 'z0z6 · działa lokalnie · zrobione w Polsce', 'M', 13, 'dim', anchor='middle', ls=1.5)
    return s

# ---------------------------------------------------------------- build
for th in ('dark', 'light'):
    save('hero', th, hero(th))
    save('langs', th, langs(th))
    save('footer', th, footer(th))
    for k in 'ABC':
        save(f'section-{P[k]["no"]}', th, section(k, th))
    save('feat-ipet-wopfu-helper', th, featured_ipet(P['A']['items'][0], th))
    save('feat-GTA26', th, featured_gta(P['C']['items'][0], th))
    for k in 'ABC':
        for it in P[k]['items']:
            save(f'card-{it[0]}', th, card(k, it, th))

def pic(name, alt, w=None, href=None):
    wa = f' width="{w}"' if w else ''
    p = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{ASSETS}/{name}-dark.svg">'
         f'<img alt="{html.escape(alt)}" src="{ASSETS}/{name}-light.svg"{wa}></picture>')
    return f'<a href="{href}">{p}</a>' if href else p

GH = 'https://github.com/z0z6/'
md = ['<!-- Okładka profilu z0z6. Grafiki: assets/profile/*.svg (jasne i ciemne). -->', '',
      '<div align="center">', '',
      pic('hero', 'z0z6 — aplikacje dla szkół specjalnych i warsztatów terapii, narzędzia działające lokalnie i gry', '100%', 'https://github.com/z0z6'),
      '', '<br>', '', pic('langs', 'Języki: JavaScript, Kotlin, GDScript, HTML/CSS, Rust, Python, Dart', '100%'), '', '<br>', '']
for k in 'ABC':
    items = P[k]['items']
    md += [pic(f'section-{P[k]["no"]}', f'{P[k]["no"]} — {P[k]["title"]}', '100%'), '', '<br>', '']
    grid = items
    if k in 'AC':
        md += [pic(f'feat-{items[0][0]}', f'{items[0][1]} — {items[0][2]}', '100%', GH + items[0][0]), '']
        grid = items[1:]
    for i in range(0, len(grid), 3):
        row = grid[i:i+3]
        md.append('\n'.join(pic(f'card-{it[0]}', f'{it[1]} — {it[2]}', '32%', GH + it[0]) for it in row))
        md.append('')
    md += ['<br>', '']
small = ' &nbsp;·&nbsp; '.join(f'<a href="{GH}{r}"><code>{r}</code></a> {d}' for r, _, d, _, _ in P['D']['items'])
md += [f'<sub>drobiazgi &nbsp;→&nbsp; {small}</sub>', '', '<br><br>', '',
       pic('footer', 'z0z6 · działa lokalnie · zrobione w Polsce', '100%'), '', '</div>', '']
open(os.path.join(OUT, 'README.md'), 'w').write('\n'.join(md))
print('ok', NREPO, TOTAL, langtot.most_common())
