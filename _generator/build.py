#!/usr/bin/env python3
"""Generator okładki README dla github.com/z0z6.

Tworzy SVG (jasne + ciemne) z osadzonymi, przyciętymi fontami oraz README.md.
Lista repozytoriów i statystyki są pobierane na bieżąco (GitHub API + git),
więc nowe repo pojawia się na okładce samo — patrz .github/workflows/profile.yml.

Zmienne środowiskowe:
  Z_USER   konto GitHub (domyślnie z0z6)
  Z_SRC    katalog ze sklonowanymi repozytoriami
  Z_OUT    katalog wyjściowy (README.md + assets/profile)
  Z_FONTS  katalog @fontsource (npm i @fontsource/{bricolage-grotesque,jetbrains-mono,instrument-serif})
  Z_CLONE  =1 → sklonuj / zaktualizuj repozytoria z API do Z_SRC
  GITHUB_TOKEN / GH_TOKEN  token do GitHub API (opcjonalny, ale bez niego limit to 60 zapytań/h)

Kategoria nowego repo: temat (topic) na GitHubie — szkola / lokalne / design / gry
(także z prefiksem z0z6-). Temat z0z6-ukryj chowa repo z okładki.
Bez tematu kategoria jest zgadywana z README i plików projektu.
"""
import base64, io, json, math, os, re, subprocess, collections, html, glob, shutil, urllib.request
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo
from fontTools.ttLib import TTFont
from fontTools import subset as ftsubset
from PIL import Image, ImageDraw, ImageFont

USER = os.environ.get('Z_USER', 'z0z6')
SRC = os.environ.get('Z_SRC', '/home/claude/srcrepos')          # sklonowane repozytoria
OUT = os.environ.get('Z_OUT', '/home/claude/out')
ASSETS = 'assets/profile'
FD = os.environ.get('Z_FONTS', '/home/claude/build/node_modules/@fontsource')
TZ = ZoneInfo('Europe/Warsaw')
NOW = datetime.now(timezone.utc)
TODAY = NOW.astimezone(TZ).date()
os.makedirs(SRC, exist_ok=True)

# ---------------------------------------------------------------- fonts
FONTS = {
    'B':  ('zB',  f'{FD}/bricolage-grotesque/files/bricolage-grotesque-%s-400-normal.woff2'),
    'BM': ('zBM', f'{FD}/bricolage-grotesque/files/bricolage-grotesque-%s-600-normal.woff2'),
    'BB': ('zBB', f'{FD}/bricolage-grotesque/files/bricolage-grotesque-%s-800-normal.woff2'),
    'BL': ('zBL', f'{FD}/bricolage-grotesque/files/bricolage-grotesque-%s-300-normal.woff2'),
    'M':  ('zM',  f'{FD}/jetbrains-mono/files/jetbrains-mono-%s-400-normal.woff2'),
    'MM': ('zMM', f'{FD}/jetbrains-mono/files/jetbrains-mono-%s-500-normal.woff2'),
    'SI': ('zSI', f'{FD}/instrument-serif/files/instrument-serif-%s-400-italic.woff2'),
}
WORDMARK = f'{FD}/jetbrains-mono/files/jetbrains-mono-latin-800-normal.woff2'
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

def fit(s, key, size, maxw):
    """Skraca tekst z wielokropkiem, żeby zmieścił się w maxw."""
    if width(s, key, size) <= maxw: return s
    while s and width(s + '…', key, size) > maxw: s = s[:-1]
    return s.rstrip() + '…'

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
# tylko czerń, biel, szarości + drobne akcenty pomarańczu
THEMES = {
    'dark': dict(bg='#0a0a0a', surface='#111111', surface2='#151515', line='#262626', faint='#1c1c1c', shadow='#2e2e2e',
                 ink='#f4f4f4', g1='#c4c4c4', g2='#9b9b9b', g3='#6e6e6e', g4='#454545', bgdot='#1f1f1f', bghi='#3a3a3a',
                 muted='#a3a3a3', dim='#6e6e6e', orange='#ff6b1a', band='#f4f4f4', bandink='#0a0a0a', bandsub='#5f5f5f',
                 A='#f4f4f4', Bc='#c4c4c4', C='#9b9b9b', D='#6e6e6e'),
    'light': dict(bg='#ffffff', surface='#f5f5f5', surface2='#efefef', line='#e3e3e3', faint='#e8e8e8', shadow='#d9d9d9',
                  ink='#0b0b0b', g1='#3b3b3b', g2='#5f5f5f', g3='#8c8c8c', g4='#b8b8b8', bgdot='#ececec', bghi='#c9c9c9',
                  muted='#555555', dim='#8c8c8c', orange='#f2560a', band='#0b0b0b', bandink='#ffffff', bandsub='#9b9b9b',
                  A='#0b0b0b', Bc='#3b3b3b', C='#5f5f5f', D='#8c8c8c'),
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
    def runs(self, x, y, segs, key='B', size=16, anchor='start', ls=0):
        """segs: [(text, color)] — jedna linia z kolorowanymi fragmentami."""
        out = []
        for s, c in segs:
            self.used[key].update(s)
            out.append(f'<tspan fill="{self.t.get(c, c)}">{html.escape(s)}</tspan>')
        a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
        l = f' letter-spacing="{ls}"' if ls else ''
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONTS[key][0]}" font-size="{size}"{a}{l} xml:space="preserve">{"".join(out)}</text>')
    def c(self, k): return self.t.get(k, k)
    def render(self):
        css = font_css(self.used) + ''.join(self.css) + '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-label="{html.escape(self.title)}">'
                f'<title>{html.escape(self.title)}</title><style>{css}</style>' + ''.join(self.parts) + '</svg>')

def save(name, theme, svg):
    p = os.path.join(OUT, ASSETS, f'{name}-{theme}.svg')
    open(p, 'w').write(svg.render())
    return p

# ================================================================ dane
def api(path):
    tok = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    h = {'Accept': 'application/vnd.github+json', 'User-Agent': 'z0z6-profile'}
    if tok: h['Authorization'] = f'Bearer {tok}'
    with urllib.request.urlopen(urllib.request.Request('https://api.github.com/' + path, headers=h), timeout=30) as r:
        return json.load(r)

def api_all(path):
    out, page = [], 1
    while True:
        chunk = api(f'{path}{"&" if "?" in path else "?"}per_page=100&page={page}')
        out += chunk
        if len(chunk) < 100: return out
        page += 1

try:
    USERINFO = api(f'users/{USER}')
    REPOS_API = {r['name']: r for r in api_all(f'users/{USER}/repos?type=owner')}
    API_OK = True
except Exception as e:                       # offline / brak dostępu → tylko to, co jest w Z_SRC
    print('GitHub API niedostępne, używam lokalnych klonów:', e)
    USERINFO, REPOS_API, API_OK = {}, {}, False

def hidden(r):
    t = set(r.get('topics') or [])
    return r.get('fork') or r.get('archived') or r.get('private') or r['name'] == USER or 'z0z6-ukryj' in t or 'ukryj' in t

if API_OK:
    REPOS = sorted((n for n, r in REPOS_API.items() if not hidden(r)), key=str.lower)
    if os.environ.get('Z_CLONE') == '1':
        for n in REPOS:
            d = os.path.join(SRC, n)
            if os.path.isdir(os.path.join(d, '.git')):
                subprocess.run(['git', '-C', d, 'fetch', '-q', '--filter=blob:none', 'origin'], check=False)
                subprocess.run(['git', '-C', d, 'reset', '-q', '--hard', 'FETCH_HEAD'], check=False)
            else:
                subprocess.run(['git', 'clone', '-q', '--filter=blob:none', REPOS_API[n]['clone_url'], d], check=False)
    REPOS = [n for n in REPOS if os.path.isdir(os.path.join(SRC, n, '.git'))]
else:
    REPOS = sorted((d for d in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, d, '.git')) and d != USER), key=str.lower)

def git(repo, *args):
    return subprocess.run(['git', '-C', os.path.join(SRC, repo), *args], capture_output=True, text=True).stdout

LANG = {'.gd': 'GDScript', '.gdshader': 'GDScript', '.kt': 'Kotlin', '.kts': 'Kotlin', '.dart': 'Dart',
        '.js': 'JavaScript', '.mjs': 'JavaScript', '.cjs': 'JavaScript', '.ts': 'JavaScript', '.jsx': 'JavaScript', '.tsx': 'JavaScript',
        '.py': 'Python', '.rs': 'Rust', '.java': 'Kotlin', '.cpp': 'C++', '.c': 'C++', '.h': 'C++',
        '.html': 'HTML/CSS', '.css': 'HTML/CSS', '.swift': 'Swift', '.go': 'Go'}
loc, files, langtot, rlang = {}, {}, collections.Counter(), {}
commits = {}                                    # repo -> [datetime w strefie PL]
for d in REPOS:
    fs = git(d, 'ls-files').split('\n')
    n, nf, rl = 0, 0, collections.Counter()
    for f in fs:
        if not f or any(x in f for x in ['node_modules', '/dist/', '.min.', 'vendor', 'three.module']): continue
        if d == 'TRON' and f.startswith('3d/'): continue
        e = os.path.splitext(f)[1]
        if e not in LANG: continue
        try: k = sum(1 for _ in open(os.path.join(SRC, d, f), errors='ignore'))
        except Exception: continue
        if k > 20000: continue
        n += k; nf += 1; langtot[LANG[e]] += k; rl[LANG[e]] += k
    loc[d] = max(n, 50); files[d] = nf
    rlang[d] = rl.most_common(1)[0][0] if rl else (REPOS_API.get(d, {}).get('language') or '—')
    commits[d] = sorted(datetime.fromtimestamp(int(t), timezone.utc).astimezone(TZ)
                        for t in git(d, 'log', '--format=%at').split() if t.strip())

def iso(s): return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(TZ)
META = {}
for d in REPOS:
    a = REPOS_API.get(d, {})
    cs = commits[d] or [NOW.astimezone(TZ)]
    META[d] = dict(
        created=iso(a['created_at']) if a.get('created_at') else cs[0],
        pushed=cs[-1],
        stars=a.get('stargazers_count', 0), forks=a.get('forks_count', 0), issues=a.get('open_issues_count', 0),
        size_kb=a.get('size') if a.get('size') is not None else
            sum(os.path.getsize(os.path.join(SRC, d, f)) for f in git(d, 'ls-files').split('\n') if f and os.path.isfile(os.path.join(SRC, d, f))) // 1024,
        topics=set(a.get('topics') or []), desc=(a.get('description') or '').strip(), homepage=a.get('homepage') or '')
def is_new(r): return (NOW.astimezone(TZ) - META[r]['created']).days < 7

# ---------------------------------------------------------------- katalog
# Kategorie w kolejności wyświetlania (Design między narzędziami a grami).
CATS = collections.OrderedDict([
    ('A', dict(title='Szkoła i terapia', short='szkoła i terapia', sub='Dokumentacja, komunikacja i codzienna praca w SOSW i WTZ.')),
    ('B', dict(title='Narzędzia, które działają lokalnie', short='narzędzia lokalne', sub='Twoje dane zostają na urządzeniu. Bez kont tam, gdzie się da.')),
    ('D', dict(title='Design', short='design', sub='Przestrzeń 3D, galerie i strony, w których forma gra pierwsze skrzypce.')),
    ('C', dict(title='Gry, w które sam chcę grać', short='gry', sub='Od pościgu po prawdziwym mieście po kosmos w przeglądarce.')),
])
for i, k in enumerate(CATS):
    CATS[k]['no'] = f'{i+1:02d}'
    CATS[k]['col'] = ['A', 'Bc', 'C', 'D'][i]
NSEC = len(CATS)

# Ręcznie opisane repo: repo → (kategoria, nazwa, opis, platformy, stos). Kolejność = kolejność kafelków.
CURATED = collections.OrderedDict([
 ('dokshelper',   ('A', 'Asystent IPET', 'Dokumentacja ucznia z orzeczeniem: od skanu orzeczenia do gotowego IPET i WOPFU w .docx.', 'Windows · Linux · Android', 'Electron · Capacitor · Tesseract')),
 ('wtzhelper',    ('A', 'WTZ Helper', 'Plany pracy pracowni i oceny uczestników WTZ, od cząstkowej po kompleksową ocenę IPR.', 'Windows · Linux', 'Electron · DOCX · PDF')),
 ('gwarek',       ('A', 'Gwarek', 'Komunikator AAC na tablety i komputery. Działa w pełni offline.', 'Android · Windows', 'Kotlin · C++')),
 ('dziennik',     ('A', 'Dziennik WTZ', 'Dziennik psychologa w stałym formacie, prowadzony razem z agentem AI.', 'Windows · Linux', 'Electron · Claude')),
 ('skryba',       ('A', 'Skryba', 'Opinie psychologiczne pisane według jednego, stałego wzoru.', 'Windows · Linux', 'Electron')),
 ('monitor',      ('A', 'Monitor prawa', 'Codziennie wyławia nowe akty prawne, które dotyczą placówki.', 'Windows · Linux · Android', 'Electron · JS')),
 ('lista',        ('A', 'Listy obecności', 'Ujednolicone listy obecności pracowników generowane do .docx.', 'Windows', 'Python')),
 ('inglisz',      ('A', 'English Buddy', 'Rozmowy po angielsku z awatarem AI na wybranym poziomie.', 'Android', 'Kotlin · Gemini')),
 ('inglisz2',     ('A', 'Mnemo', 'Słówka, które zostają w głowie: nauka oparta na badaniach nad pamięcią, talie w ~25 językach.', 'Android', 'Kotlin · WebView')),
 ('szept',        ('B', 'Szept', 'Szyfrowany komunikator P2P: bez kont, bez numeru telefonu, bez serwera.', 'Android · Linux · Win · macOS', 'Rust · Kotlin')),
 ('QR',           ('B', 'QR', 'Generator kodów QR i przesyłanie plików ruchomym kodem: bez internetu i parowania.', 'Win · Linux · macOS · Android', 'Electron · Capacitor')),
 ('tax',          ('B', 'Asystent PIT', 'Z pasków wypłat liczy podatek za rok i przewiduje dopłatę lub zwrot.', 'Windows · Linux · Android', 'Electron · OCR')),
 ('watcher',      ('B', 'WatchPL', 'Monitor zdarzeń w płn.-wsch. Polsce z oceną wiarygodności doniesień.', 'Android', 'Flutter · Python')),
 ('Tracko',       ('B', 'Tracko', 'Tracker aktywności z GPS: ranking, wyścig duchów i planer tras.', 'Android · Web', 'Kotlin · Supabase')),
 ('cryptoscaner', ('B', 'CryptoScaner', 'Notowania kryptowalut na żywo, alerty i wykresy z jednego kodu.', 'Linux · Windows · Android', 'Electron · Capacitor')),
 ('cinemaker',    ('B', 'Kadr Studio', 'Edytor wideo z osią czasu, wieloma torami i eksportem przez FFmpeg.', 'Windows · Linux', 'Electron · FFmpeg')),
 ('melodico',     ('B', 'Sampler', 'Sampler, looper i mini-deck w estetyce konsolety DJ.', 'Android', 'Kotlin · Compose')),
 ('steps',        ('B', 'Dot Steps', 'Licznik kroków w stylu matrycy kropek, z trybem E-ink.', 'Android', 'Kotlin · Compose')),
 ('vr',           ('B', 'VR Player', 'Odtwarzacz wideo 360° do gogli typu Cardboard.', 'Android', 'Kotlin · OpenGL')),
 ('metaverse',    ('D', 'Galeria', 'Wirtualna sala wystawowa w przeglądarce: spacer z widokiem z pierwszej lub trzeciej osoby i tryb VR (WebXR).', 'Web · VR', 'Three.js · WebXR')),
 ('foto',         ('D', 'Foto', 'Portfolio zdjęć z miniaturami i pełnym podglądem w lightboxie.', 'Web', 'HTML · CSS · JS')),
 ('rotacja',      ('D', 'Rotacja', 'Model 3D, który obraca się w pętli, a przeciągnięciem także ręcznie.', 'Web', 'Three.js')),
 ('odliczanie',   ('D', 'Odliczanie', 'Licznik do wydarzenia z panelem admina, który zapisuje ustawienia przez GitHub API.', 'Web', 'HTML · JS · GitHub API')),
 ('GTA26',        ('C', 'Uciekaj przed windykatorem', 'Pościg z widokiem z góry po prawdziwym Makowie Mazowieckim, odtworzonym z OpenStreetMap.', 'Android · Web', 'Godot 4.4 · GDScript')),
 ('Teegarden-B',  ('C', 'Teegarden-B', 'Gra kosmiczna budowana krok po kroku, każdy etap działa osobno.', 'Web', 'Three.js')),
 ('8w1',          ('C', 'Retro Arcade', 'Hub gier na telefon. Na start Marble Maze sterowany przechyłem.', 'Android', 'Godot 4.4 · Jolt')),
 ('TRON',         ('C', 'Light Cycles', 'Świetlne motocykle w 2D i 3D: AI, multiplayer online, power-upy.', 'Web', 'Three.js · Vite')),
 ('SuperMayoBros',('C', 'Łąkowa Przygoda', 'Platformówka z jednym plikiem gry dla przeglądarki i Androida.', 'Web · Android', 'HTML5 · WebView')),
 ('brawl',        ('C', 'Arena Brawl', 'Arena offline: Ty kontra sześć botów w trybie Showdown.', 'Android', 'Kotlin')),
])
FEATURED = {'A': 'dokshelper', 'D': 'metaverse', 'C': 'GTA26'}

TOPIC_CAT = {'szkola': 'A', 'szkoła': 'A', 'terapia': 'A', 'edukacja': 'A', 'lokalne': 'B', 'narzedzia': 'B', 'narzedzie': 'B',
             'tool': 'B', 'tools': 'B', 'design': 'D', 'portfolio': 'D', 'gra': 'C', 'gry': 'C', 'game': 'C', 'games': 'C'}

def readme(r):
    for p in sorted(glob.glob(os.path.join(SRC, r, '*'))):
        if os.path.basename(p).lower() in ('readme.md', 'readme', 'readme.txt'):
            return open(p, errors='ignore').read()
    return ''

def md_plain(s):
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', s)
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
    s = re.sub(r'[*_`]+', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def has(r, *pats):
    return any(glob.glob(os.path.join(SRC, r, p)) for p in pats)

def auto_meta(r):
    """Opis kafelka dla repo, którego nie ma w CURATED — z README, tematów i plików projektu."""
    txt = readme(r); low = txt[:5000].lower(); m = META[r]
    name = r
    h1 = re.search(r'^#\s+(.+)$', txt, re.M)
    if h1: name = re.split(r'\s+[–—-]\s+|:\s', md_plain(h1.group(1)))[0][:28] or r
    desc = ''
    for para in re.split(r'\n\s*\n', txt):
        p = para.strip()
        if not p or p[0] in '#|`!<>-*[' or re.match(r'^\d+\.', p): continue
        desc = md_plain(p); break
    if not desc and m['desc'] and m['desc'].lower() != r.lower(): desc = m['desc']
    if desc:
        first = re.split(r'(?<=[.!?])\s', desc)[0]
        desc = first if len(first) >= 40 else desc
        if len(desc) > 120: desc = desc[:118].rsplit(' ', 1)[0].rstrip(',;:–-') + '…'
        elif desc.endswith(':'): desc = desc[:-1].rstrip() + '.'
    else:
        desc = 'Nowy projekt — opis pojawi się wkrótce.'
    plat = [p for p, keys in [('Android', ['android', 'apk']), ('Windows', ['windows', '.exe']), ('Linux', ['linux', 'appimage']),
                              ('macOS', ['macos,', 'macos)', 'macos i', 'macos ·', '**macos**']), ('Web', ['przeglądar', 'github pages', 'webxr'])] if any(k in low for k in keys)]
    if not plat:
        if has(r, 'build.gradle*', 'app/build.gradle*', 'android'): plat.append('Android')
        if has(r, 'index.html') or m['homepage']: plat.append('Web')
    pk = open(os.path.join(SRC, r, 'package.json'), errors='ignore').read() if has(r, 'package.json') else ''
    stack = [s for s, ok in [('Electron', '"electron"' in pk), ('Capacitor', has(r, 'capacitor.config.*')), ('Godot', has(r, 'project.godot')),
                             ('Rust', has(r, 'Cargo.toml', '*/Cargo.toml')), ('Flutter', has(r, 'pubspec.yaml')),
                             ('Kotlin', has(r, 'build.gradle*', 'app/build.gradle*')), ('Three.js', '"three"' in pk),
                             ('Python', has(r, 'requirements.txt', 'pyproject.toml'))] if ok]
    if not stack and rlang[r] != '—': stack = [rlang[r]]
    cat = None
    for t in m['topics']:
        t = t.removeprefix('z0z6-')
        if t in TOPIC_CAT: cat = TOPIC_CAT[t]; break
    if not cat:
        if has(r, 'project.godot') or any(k in low for k in (' gra ', 'gra w', 'gry ', 'platformówk', 'game')): cat = 'C'
        elif any(k in low for k in ('szkoł', 'sosw', 'wtz', 'terapi', 'uczni', 'nauczyciel', 'psycholog', 'ipet', 'nauk')): cat = 'A'
        elif any(k in low for k in ('portfolio', 'galeri', 'three.js', 'webxr', 'design')): cat = 'D'
        else: cat = 'B'
    return (cat, name, desc, ' · '.join(plat[:4]) or 'GitHub', ' · '.join(stack[:3]) or '—')

ITEMS = {}                      # repo → (kategoria, nazwa, opis, platformy, stos)
for r in REPOS:
    ITEMS[r] = CURATED[r] if r in CURATED else auto_meta(r)
P = collections.OrderedDict()   # kategoria → lista repo (wyróżnione, potem nowe, potem reszta wg CURATED)
for k in CATS:
    rs = [r for r in REPOS if ITEMS[r][0] == k]
    order = list(CURATED)
    rs.sort(key=lambda r: (r != FEATURED.get(k), r in CURATED, order.index(r) if r in CURATED else -META[r]['created'].timestamp()))
    P[k] = rs
NREPO = len(REPOS)
PCOL = {k: CATS[k]['col'] for k in CATS}
lmin, lmax = math.log(min(loc.values())), math.log(max(loc.values()))
def lnorm(r): return (math.log(loc[r]) - lmin) / (lmax - lmin or 1)
TOTAL = sum(langtot.values())

# ---------------------------------------------------------------- statystyki
ALLC = sorted(c for r in REPOS for c in commits[r])
NCOMMITS = len(ALLC)
DAYS = collections.Counter(c.date() for c in ALLC)
HOURS = collections.Counter(c.hour for c in ALLC)
def longest_streak(ds):
    best = cur = 0; prev = None
    for d in sorted(ds):
        cur = cur + 1 if prev and (d - prev).days == 1 else 1
        best = max(best, cur); prev = d
    return best
STREAK = longest_streak(DAYS)
LAST30 = sum(1 for c in ALLC if (TODAY - c.date()).days < 30)
SINCE = iso(USERINFO['created_at']).date() if USERINFO.get('created_at') else min(m['created'] for m in META.values()).date()
LAST_REPO = max(REPOS, key=lambda r: META[r]['pushed'])
TOP_COMMITS = max(REPOS, key=lambda r: len(commits[r]))
TOP_LOC = max(REPOS, key=lambda r: loc[r])
NFILES = sum(files.values())
STARS = sum(META[r]['stars'] for r in REPOS); FORKS = sum(META[r]['forks'] for r in REPOS)
ISSUES = sum(META[r]['issues'] for r in REPOS)
SIZE_MB = sum(META[r]['size_kb'] for r in REPOS) / 1024
FOLLOWERS = USERINFO.get('followers', 0)
PEAK_H = HOURS.most_common(1)[0][0] if HOURS else 0
PLATS = collections.Counter({'Win': 'Windows'}.get(x, x) for r in REPOS for x in ITEMS[r][3].split(' · '))
WD = ['pn', 'wt', 'śr', 'cz', 'pt', 'sb', 'nd']
MONTHS = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze', 'lip', 'sie', 'wrz', 'paź', 'lis', 'gru']
def num(n): return f'{n:,}'.replace(',', ' ')
def dmy(d): return d.strftime('%d.%m.%Y')

# ================================================================ rysowanie
def dot_bg(s, pid, x, y, w, h, rx, pitch=12, r=0.9):
    """Subtelne, animowane tło z kropek: stała siatka + jaśniejsza fala przechodząca po skosie."""
    s.add(f'<defs>'
          f'<pattern id="{pid}" x="0" y="0" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse">'
          f'<circle cx="{pitch/2:g}" cy="{pitch/2:g}" r="{r}" fill="{s.c("bgdot")}"/></pattern>'
          f'<pattern id="{pid}h" x="0" y="0" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse">'
          f'<circle cx="{pitch/2:g}" cy="{pitch/2:g}" r="{r*1.35:.2f}" fill="{s.c("bghi")}"/></pattern>'
          f'<linearGradient id="{pid}g" gradientUnits="userSpaceOnUse" x1="{x}" y1="{y}" x2="{x+w}" y2="{y+w*0.3:.0f}">'
          f'<stop offset="0" stop-color="#000"/><stop offset=".36" stop-color="#000"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/>'
          f'<stop offset=".64" stop-color="#000"/><stop offset="1" stop-color="#000"/>'
          f'<animateTransform attributeName="gradientTransform" type="translate" values="{-w*0.75:.0f} 0;{w*0.75:.0f} 0" dur="14s" repeatCount="indefinite"/>'
          f'</linearGradient>'
          f'<radialGradient id="{pid}r" gradientUnits="userSpaceOnUse" cx="{x+w*0.2:.0f}" cy="{y+h*0.7:.0f}" r="{max(w, h)*0.28:.0f}">'
          f'<stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
          f'<animate attributeName="cx" values="{x+w*0.2:.0f};{x+w*0.8:.0f};{x+w*0.2:.0f}" dur="31s" repeatCount="indefinite"/>'
          f'<animate attributeName="cy" values="{y+h*0.7:.0f};{y+h*0.25:.0f};{y+h*0.7:.0f}" dur="23s" repeatCount="indefinite"/>'
          f'</radialGradient>'
          f'<mask id="{pid}m"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid}g)"/>'
          f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid}r)"/></mask>'
          f'<clipPath id="{pid}c"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath></defs>')
    s.add(f'<g clip-path="url(#{pid}c)"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})">'
          f'<animate attributeName="opacity" values=".7;1;.7" dur="9s" repeatCount="indefinite"/></rect>'
          f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid}h)" mask="url(#{pid}m)"/></g>')

def board(s, pid, rx=30):
    s.add(f'<rect x="1" y="1" width="{s.w-2}" height="{s.h-2}" rx="{rx}" fill="{s.c("bg")}" stroke="{s.c("line")}"/>')
    dot_bg(s, pid, 1, 1, s.w - 2, s.h - 2, rx)

def leader(s, x1, x2, y, pitch=6):
    """Kropkowany „leader” typograficzny między etykietą a wartością."""
    n = int((x2 - x1) // pitch)
    if n > 0:
        s.add(f'<path d="M{x1:.1f} {y} H{x1 + n*pitch:.1f}" stroke="{s.c("g4")}" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="0 {pitch}"/>')

# ---------------------------------------------------------------- hero
_wm = None
def _wordmark_ttf():
    """PIL potrzebuje TTF — konwersja woff2 → ttf do pliku tymczasowego."""
    global _wm
    if _wm is None:
        import tempfile
        f = TTFont(WORDMARK); f.flavor = None
        _wm = os.path.join(tempfile.gettempdir(), 'z0z6-wordmark.ttf'); f.save(_wm)
    return _wm

def coverage(text, cols, rows, k=8):
    """Rasteryzuje tekst i rozciąga go dokładnie na siatkę cols×rows; zwraca pokrycie 0..1 każdej komórki."""
    f = ImageFont.truetype(_wordmark_ttf(), 400)
    bb = f.getbbox(text)
    img = Image.new('L', (bb[2] + 40, bb[3] + 40), 0)
    ImageDraw.Draw(img).text((20, 20), text, font=f, fill=255)
    img = img.crop(img.getbbox())             # dokładnie do krawędzi liter
    img = img.resize((cols * k, rows * k), Image.LANCZOS).resize((cols, rows), Image.BOX)
    px = img.load()
    return [[px[x, y] / 255 for x in range(cols)] for y in range(rows)]

def hero(theme):
    W, H = 1200, 600
    s = SVG(W, H, theme, 'z0z6 — aplikacje customowe, praktyczne rozwiązania, design, eksperymentalnie, vib3c0DinG')
    s.css.append('.p{animation:p 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}'
                 '@keyframes p{0%,100%{transform:scale(1)}50%{transform:scale(1.5)}}'
                 '.b{animation:b 1.1s steps(1) infinite}@keyframes b{50%{opacity:0}}')
    board(s, 'hg')

    # górny pasek
    s.text(56, 60, USER, 'M', 14, 'ink')
    s.text(56 + width(USER + ' ', 'M', 14), 60, f'/ github.com/{USER}', 'M', 14, 'g3')
    s.add(f'<circle class="p" cx="{W-56-width("open source · Polska", "M", 14)-14:.1f}" cy="55" r="3.5" fill="{s.c("orange")}"/>')
    s.text(W - 56, 60, 'open source · Polska', 'M', 14, 'g2', anchor='end')

    # wordmark: halftone rozciągnięty od lewej do prawej krawędzi (z kursorem)
    PT = 6.0
    L, R = 56, W - 56
    total = int((R - L) // PT)               # kolumny na całą szerokość
    kw, kg = 8, 4                           # kursor: szerokość i odstęp (w kolumnach)
    cols, rows = total - kw - kg, 46
    x0 = L + PT / 2 + ((R - L) - total * PT) / 2
    y0 = 92 + PT / 2
    cov = coverage(USER, cols, rows)
    rmax = PT * 0.47
    main, shade = [], []
    dx, dy = 2, 2
    for y in range(rows + dy):
        for x in range(cols + dx):
            c = cov[y][x] if y < rows and x < cols else 0
            sy, sx = y - dy, x - dx
            sc_ = cov[sy][sx] if 0 <= sy < rows and 0 <= sx < cols else 0
            cx, cy = x0 + x * PT, y0 + y * PT
            if c > 0.06:
                t = y / rows
                r = rmax * math.sqrt(c) * (1 - 0.38 * t)
                main.append(f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:.2f}"/>')
            elif sc_ > 0.25:
                shade.append(f'<circle cx="{cx:g}" cy="{cy:g}" r="{rmax*0.62*math.sqrt(sc_):.2f}"/>')
    s.add(f'<defs><linearGradient id="sc" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1200" y2="0">'
          f'<stop offset="0" stop-color="{s.c("ink")}"/><stop offset=".485" stop-color="{s.c("ink")}"/>'
          f'<stop offset=".495" stop-color="{s.c("orange")}"/><stop offset=".505" stop-color="{s.c("orange")}"/>'
          f'<stop offset=".515" stop-color="{s.c("ink")}"/><stop offset="1" stop-color="{s.c("ink")}"/>'
          f'<animateTransform attributeName="gradientTransform" type="translate" values="-700 0;-700 0;700 0" keyTimes="0;.5;1" dur="8s" repeatCount="indefinite"/>'
          f'</linearGradient></defs>')
    s.add(f'<g fill="{s.c("shadow")}">{"".join(shade)}</g>')
    s.add(f'<g fill="url(#sc)">{"".join(main)}</g>')
    kc = cols + kg
    cur = [f'<circle cx="{x0 + xx*PT:g}" cy="{y0 + yy*PT:g}" r="{rmax*0.82:.2f}"/>'
           for yy in range(rows - 3, rows) for xx in range(kc, kc + kw)]
    s.add(f'<g class="b" fill="{s.c("orange")}">{"".join(cur)}</g>')

    # chmura tagów
    TX = 56
    def tag_line(y, items):
        x = TX
        for it in items:
            if it[0] == 'gap':
                x += it[1]; continue
            kind, txt, key, size, fill = it
            if kind == 'outline':
                s.text(x, y, txt, key, size, 'none', extra=f' stroke="{s.c(fill)}" stroke-width="1.1"')
            else:
                s.text(x, y, txt, key, size, fill)
            x += width(txt, key, size)
        return x
    ya = 440
    tag_line(ya, [('t', 'aplikacje customowe', 'BB', 40, 'ink'), ('gap', 16), ('t', 'design', 'SI', 50, 'g2')])
    yb = ya + 50
    xb = tag_line(yb, [('t', 'praktyczne rozwiązania', 'BL', 31, 'g1')])
    vs, vk = 18, 'MM'
    px0 = xb + 18
    pw_ = width('vib3c0DinG', vk, vs) + 46
    s.add(f'<rect x="{px0:.1f}" y="{yb-25}" width="{pw_:.1f}" height="32" rx="16" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
    s.add(f'<circle class="p" cx="{px0+17:.1f}" cy="{yb-9}" r="2.6" fill="{s.c("orange")}"/>')
    s.runs(px0 + 30, yb - 3, [('vib', 'ink'), ('3', 'orange'), ('c', 'ink'), ('0', 'orange'), ('DinG', 'ink')], vk, vs)
    yc = yb + 48
    xc = tag_line(yc, [('outline', 'eksperymentalnie', 'BB', 31, 'g2')])
    s.text(xc + 18, yc - 2, '#tagi · 05', 'M', 12, 'g3', ls=1)

    # prawa kolumna: platformy, języki, liczby
    plats = [p for p, _ in PLATS.most_common() if p in ('Android', 'Windows', 'Linux', 'Web', 'macOS')][:4]
    topl = [n for n, _ in langtot.most_common(4)]
    s.text(R, yb - 8, ' · '.join(plats), 'M', 14, 'g2', anchor='end')
    s.text(R, yb + 18, '//  ' + ' · '.join(topl), 'M', 14, 'g3', anchor='end')
    s.runs(R, yc - 2, [(f'{NREPO}', 'orange'), (' repozytoriów · ≈ ', 'g3'), (f'{round(TOTAL/1000)}', 'orange'),
                       (' tys. linii · ', 'g3'), (num(NCOMMITS), 'orange'), (' commitów', 'g3')], 'M', 14, anchor='end')
    return s

# ---------------------------------------------------------------- matryca repozytoriów (przeniesiona z okładki)
def matrix(s, px, py, pw, ph):
    s.add(f'<defs><pattern id="pg" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r=".55" fill="{s.c("line")}"/></pattern></defs>')
    s.add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="22" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
    s.add(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="22" fill="url(#pg)" opacity=".6"/>')
    s.text(px + 28, py + 42, 'MATRYCA REPOZYTORIÓW', 'M', 12, 'g3', ls=2)
    s.text(px + pw - 28, py + 42, f'{NREPO:02d}', 'M', 12, 'orange', anchor='end', ls=2)
    gcol = ['ink', 'g1', 'g2', 'g3']
    step = (ph - 104) / len(CATS)
    ry_ = py + 84
    for gi, key in enumerate(CATS):
        repos = sorted(P[key], key=lambda r: -loc[r])
        s.text(px + 28, ry_, CATS[key]['no'], 'M', 13, 'g3')
        s.text(px + 58, ry_, CATS[key]['short'], 'M', 13, 'g2')
        s.text(px + pw - 28, ry_, f'{len(repos):02d}', 'M', 13, 'g3', anchor='end')
        sp = min(42, (pw - 56) / max(len(repos), 1))
        R = min(15, sp / 2 - 2)
        for i, r in enumerate(repos):
            rr = (3.6 + 11.4 * lnorm(r)) * R / 15
            cx = px + 28 + R + i * sp
            s.add(f'<circle cx="{cx:.1f}" cy="{ry_+30}" r="{R:.1f}" fill="{s.c("bg")}" stroke="{s.c("orange") if is_new(r) else s.c("line")}"/>')
            s.add(f'<circle cx="{cx:.1f}" cy="{ry_+30}" r="{rr:.1f}" fill="{s.c(gcol[gi])}"><title>{r} · ~{loc[r]} linii</title></circle>')
        ry_ += step
    s.runs(px + 28, py + ph - 22, [('wielkość kropki = ilość kodu · ', 'g3'), ('○', 'orange'), (' nowe', 'g3')], 'M', 12)

# ---------------------------------------------------------------- statystyki: przegląd
def stats_overview(theme):
    W, H = 1200, 800
    s = SVG(W, H, theme, f'Statystyki konta {USER}: {NREPO} repozytoriów, {NCOMMITS} commitów, ≈{round(TOTAL/1000)} tys. linii kodu')
    s.css.append('.p{animation:p 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}'
                 '@keyframes p{0%,100%{transform:scale(1)}50%{transform:scale(1.6)}}')
    board(s, 'sg')
    s.text(40, 54, f'STATYSTYKI KONTA · github.com/{USER}', 'M', 12, 'g3', ls=2)
    upd = f'aktualizacja {dmy(TODAY)}'
    s.text(W - 40, 54, upd, 'M', 12, 'g3', anchor='end', ls=1)
    s.add(f'<circle class="p" cx="{W-40-width(upd, "M", 12, 1)-14:.1f}" cy="50" r="3.2" fill="{s.c("orange")}"/>')

    # kafelki KPI
    days_on = (TODAY - SINCE).days
    kpi = [
        ('REPOZYTORIA', f'{NREPO}', '', 'publiczne, bez forków'),
        ('LINIE KODU', f'{round(TOTAL/1000)}', 'tys.', f'{num(NFILES)} plików źródłowych'),
        ('COMMITY', num(NCOMMITS), '', f'{num(LAST30)} w ciągu 30 dni'),
        ('AKTYWNE DNI', f'{len(DAYS)}', '', f'seria: {STREAK} dni z rzędu'),
        ('JĘZYKI', f'{len(langtot)}', '', f'najwięcej: {langtot.most_common(1)[0][0]}' if langtot else ''),
        ('NA GITHUBIE', f'{days_on}', 'dni', f'od {dmy(SINCE)}'),
    ]
    gx, gy, gap, th = 40, 80, 14, 136
    tw = (W - 2 * gx - gap * (len(kpi) - 1)) / len(kpi)
    for i, (lab, val, unit, sub) in enumerate(kpi):
        x = gx + i * (tw + gap)
        s.add(f'<rect x="{x:.1f}" y="{gy}" width="{tw:.1f}" height="{th}" rx="18" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
        s.add(f'<circle cx="{x+22:.1f}" cy="{gy+27}" r="3" fill="{s.c("orange") if i == 0 else s.c("g3")}"/>')
        s.text(x + 32, gy + 31, lab, 'M', 11, 'g3', ls=1.4)
        size = 46
        while width(val, 'BB', size, -1) + (width(' ' + unit, 'B', 18) if unit else 0) > tw - 36: size -= 2
        s.text(x + 18, gy + 90, val, 'BB', size, 'ink', ls=-1)
        if unit: s.text(x + 18 + width(val, 'BB', size, -1) + 6, gy + 90, unit, 'B', 18, 'g2')
        s.text(x + 19, gy + 118, fit(sub, 'M', 11, tw - 34), 'M', 11, 'g2')

    # fakty z kropkowanymi „leaderami”
    facts = [
        [('gwiazdki', num(STARS)), ('forki', num(FORKS))],
        [('obserwujący', num(FOLLOWERS)), ('otwarte zgłoszenia', num(ISSUES))],
        [('najwięcej commitów', f'{TOP_COMMITS} · {len(commits[TOP_COMMITS])}'), ('najwięcej kodu', TOP_LOC)],
        [('ostatni commit', f'{META[LAST_REPO]["pushed"].strftime("%d.%m")} · {LAST_REPO}'), ('ulubiona pora', f'{PEAK_H:02d}:00–{(PEAK_H+1)%24:02d}:00')],
    ]
    fw = (W - 2 * gx - 3 * 28) / 4
    for ci, col in enumerate(facts):
        x = gx + ci * (fw + 28)
        for ri, (lab, val) in enumerate(col):
            y = 262 + ri * 28
            val = fit(val, 'M', 13, fw * 0.62)
            s.text(x, y, lab, 'M', 12, 'g3')
            s.text(x + fw, y, val, 'M', 13, 'ink', anchor='end')
            leader(s, x + width(lab, 'M', 12) + 8, x + fw - width(val, 'M', 13) - 8, y - 4)

    # aktywność: 26 tygodni × 7 dni
    top = 352
    s.add(f'<line x1="{gx}" y1="{top-22}" x2="{W-gx}" y2="{top-22}" stroke="{s.c("line")}"/>')
    s.text(gx, top + 12, 'AKTYWNOŚĆ · OSTATNIE 26 TYGODNI', 'M', 12, 'g3', ls=2)
    weeks, pitch = 26, 22
    hx, hy = gx + 30, top + 56
    start = TODAY - timedelta(days=TODAY.weekday()) - timedelta(weeks=weeks - 1)
    mx = max([DAYS.get(start + timedelta(days=i), 0) for i in range(weeks * 7)] + [1])
    for di in range(7):
        if di % 2 == 0: s.text(gx, hy + di * pitch + 4, WD[di], 'M', 11, 'g3')
    lastm = None
    for w in range(weeks):
        wd0 = start + timedelta(weeks=w)
        if wd0.month != lastm and (w < weeks - 2):
            s.text(hx + w * pitch - 4, hy - 18, MONTHS[wd0.month - 1], 'M', 11, 'g3')
            lastm = wd0.month
        for di in range(7):
            d = wd0 + timedelta(days=di)
            if d > TODAY: continue
            cx, cy = hx + w * pitch, hy + di * pitch
            v = DAYS.get(d, 0)
            if v:
                q = math.sqrt(v / mx)
                col = 'ink' if q > 0.66 else ('g1' if q > 0.33 else 'g2')
                s.add(f'<circle cx="{cx}" cy="{cy}" r="{2.6 + 6.2*q:.1f}" fill="{s.c(col)}"><title>{dmy(d)} · {v} commit.</title></circle>')
            else:
                s.add(f'<circle cx="{cx}" cy="{cy}" r="1.6" fill="{s.c("g4")}"/>')
            if d == TODAY:
                s.add(f'<circle cx="{cx}" cy="{cy}" r="10" fill="none" stroke="{s.c("orange")}" stroke-width="1.4"/>')
    lx = hx + (weeks - 1) * pitch

    # pora dnia
    ty = hy + 7 * pitch + 34
    s.text(gx, ty, 'PORA DNIA · COMMITY WG GODZINY', 'M', 12, 'g3', ls=2)
    hmx = max(HOURS.values() or [1])
    hp = (lx - hx + 30) / 24
    base = ty + 100
    for h in range(24):
        cx = gx + 6 + h * hp
        n = round(8 * HOURS.get(h, 0) / hmx)
        for k in range(8):
            on = k < n
            s.add(f'<circle cx="{cx:.1f}" cy="{base - k*9}" r="{3.1 if on else 1.4}" fill="{s.c("orange") if (on and h == PEAK_H) else s.c("ink") if on else s.c("g4")}"/>')
        if h % 6 == 0: s.text(cx, base + 22, f'{h:02d}', 'M', 11, 'g3', anchor='middle')
    s.text(gx + 6 + 23 * hp, base + 22, '23', 'M', 11, 'g3', anchor='middle')

    # matryca repozytoriów (dawniej na okładce)
    mx0 = 686
    matrix(s, mx0, top - 4, W - gx - mx0, H - top - 36)
    return s

# ---------------------------------------------------------------- statystyki: wszystkie repozytoria
def stats_repos(theme):
    rs = sorted(REPOS, key=lambda r: -META[r]['pushed'].timestamp())
    half = math.ceil(len(rs) / 2)
    rowh = 30
    W, H = 1200, 132 + half * rowh + 40
    s = SVG(W, H, theme, f'Wszystkie repozytoria {USER} ({NREPO})')
    board(s, 'rg')
    s.text(40, 54, f'WSZYSTKIE REPOZYTORIA · {NREPO}', 'M', 12, 'g3', ls=2)
    s.text(W - 40, 54, 'od ostatnio zmienianych', 'M', 12, 'g3', anchor='end', ls=1)
    cw, gx = 536, 40
    cmax = max(len(commits[r]) for r in rs) or 1
    for ci in range(2):
        x = gx + ci * (cw + 48)
        hy = 96
        for lab, xx, anc in [('repo', x + 20, 'start'), ('język', x + 196, 'start'), ('kod', x + 300, 'start'),
                             ('commity', x + 452, 'end'), ('ostatni', x + cw, 'end')]:
            s.text(xx, hy, lab, 'M', 11, 'g3', anchor=anc, ls=1.2)
        s.add(f'<line x1="{x}" y1="{hy+12}" x2="{x+cw}" y2="{hy+12}" stroke="{s.c("line")}"/>')
        for ri, r in enumerate(rs[ci * half:(ci + 1) * half]):
            y = hy + 40 + ri * rowh
            k = ITEMS[r][0]
            s.add(f'<circle cx="{x+6}" cy="{y-4}" r="4.2" fill="{s.c(PCOL[k])}" stroke="{s.c("line")}"><title>{CATS[k]["short"]}</title></circle>')
            nm = fit(r, 'MM', 13, 150 if is_new(r) else 168)
            s.text(x + 20, y, nm, 'MM', 13, 'ink')
            if is_new(r):
                bx = x + 20 + width(nm, 'MM', 13) + 8
                s.add(f'<rect x="{bx:.1f}" y="{y-13}" width="36" height="16" rx="8" fill="none" stroke="{s.c("orange")}"/>')
                s.text(bx + 18, y - 1, 'nowe', 'M', 9.5, 'orange', anchor='middle')
            s.text(x + 196, y, fit(rlang[r], 'M', 12, 96), 'M', 12, 'g2')
            lit = max(1, round(9 * (0.12 + 0.88 * lnorm(r))))
            for i in range(9):
                s.add(f'<circle cx="{x + 304 + i*10}" cy="{y-4}" r="3" fill="{s.c(PCOL[k]) if i < lit else s.c("faint")}"/>')
            s.text(x + 452, y, num(len(commits[r])), 'M', 13, 'ink', anchor='end')
            s.text(x + cw, y, META[r]['pushed'].strftime('%d.%m.%y'), 'M', 12, 'g2', anchor='end')
            s.add(f'<path d="M{x} {y+11} H{x+cw}" stroke="{s.c("g4")}" stroke-width="1" stroke-linecap="round" stroke-dasharray="0 5" opacity=".7"/>')
    # legenda kategorii
    lx = gx
    ly = H - 30
    for k in CATS:
        s.add(f'<circle cx="{lx+5}" cy="{ly-4}" r="4.2" fill="{s.c(PCOL[k])}" stroke="{s.c("line")}"/>')
        lab = f'{CATS[k]["no"]} {CATS[k]["short"]}'
        s.text(lx + 16, ly, lab, 'M', 12, 'g2')
        lx += 16 + width(lab, 'M', 12) + 28
    s.text(W - 40, ly, 'kod = linie kodu (skala logarytmiczna)', 'M', 12, 'g3', anchor='end')
    return s

# ---------------------------------------------------------------- language strip
LRAMP = {'dark': ['#f4f4f4', '#cfcfcf', '#a8a8a8', '#858585', '#666666', '#4d4d4d', '#3a3a3a', '#2c2c2c'],
         'light': ['#0b0b0b', '#2e2e2e', '#525252', '#737373', '#949494', '#b0b0b0', '#c8c8c8', '#dadada']}
def langs(theme):
    W, H = 1200, 150
    s = SVG(W, H, theme, f'Języki w repozytoriach {USER}')
    items = langtot.most_common()
    LCOL = {name: LRAMP[theme][min(i, 7)] for i, (name, _) in enumerate(items)}
    s.text(4, 30, 'KOD', 'M', 12, 'dim', ls=2)
    s.runs(W - 4, 30, [('≈ ', 'dim'), (f'{round(TOTAL/1000)}', 'orange'), (f' tys. linii · {NREPO} repozytoriów', 'dim')], 'M', 12, anchor='end', ls=1)
    cols, pitch = 240, 1192 / 240
    prev, acc = 0, 0.0
    for name, v in items:
        acc += v / TOTAL * cols
        e = round(acc)
        for c in range(prev, e):
            for row in range(4):
                s.add(f'<circle cx="{4 + pitch/2 + c*pitch:.1f}" cy="{52 + row*7}" r="2.1" fill="{LCOL[name]}"/>')
        prev = e
    x = 4
    for name, v in items:
        pct = v / TOTAL * 100
        lab = f'{name} {pct:.0f}%' if pct >= 1 else f'{name} <1%'
        s.add(f'<circle cx="{x+5}" cy="{119}" r="5" fill="{LCOL[name]}" stroke="{s.c("line")}"/>')
        s.text(x + 16, 124, lab, 'M', 13, 'muted')
        x += 16 + width(lab, 'M', 13) + 30
    return s

# ---------------------------------------------------------------- nagłówek sekcji: pełny, odwrócony pas
def section(no, title, sub, n, theme, unit='repo'):
    W, H = 1200, 176
    s = SVG(W, H, theme, f'{no} {title}')
    s.css.append('.w{animation:w 4.8s ease-in-out infinite}@keyframes w{0%,100%{opacity:.25}50%{opacity:1}}')
    bx, by, bw, bh = 1, 8, W - 2, 160
    s.add(f'<defs><clipPath id="bc"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="26"/></clipPath></defs>')
    s.add(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="26" fill="{s.c("band")}"/>')
    # halftone narastający w prawo, z falą
    dots = []
    pitch = 10
    for gx in range(60):
        x = W - 8 - gx * pitch
        t = 1 - gx / 60
        for gy in range(int(bh // pitch)):
            y = by + 5 + gy * pitch
            r = 0.4 + 2.6 * t ** 2.2
            if r < 0.5: continue
            dots.append(f'<circle class="w" style="animation-delay:{(gx*0.06 + gy*0.03):.2f}s" cx="{x}" cy="{y}" r="{r:.2f}"/>')
    s.add(f'<g clip-path="url(#bc)" fill="{s.c("bandsub")}" opacity=".55">{"".join(dots)}</g>')
    # pomarańczowy znacznik
    s.add(f'<rect x="{bx}" y="{by+36}" width="6" height="{bh-72}" rx="3" fill="{s.c("orange")}"/>')
    s.text(40, by + 44, no, 'MM', 15, 'orange', ls=1)
    s.text(40 + width(no + ' ', 'MM', 15, 1), by + 44, f'/ {NSEC:02d}' if no != '00' else '/ konto', 'M', 15, 'bandsub', ls=1)
    size = 54
    while width(title, 'BB', size, -1) > 820: size -= 2
    s.text(38, by + 104, title, 'BB', size, 'bandink', ls=-1)
    s.text(40, by + 138, sub, 'B', 19, 'bandsub')
    # licznik
    s.add(f'<rect x="{W-176}" y="{by+22}" width="136" height="34" rx="17" fill="{s.c("bandink")}"/>')
    s.text(W - 108, by + 45, f'{n} {unit}', 'MM', 15, 'band', anchor='middle')
    return s

# ---------------------------------------------------------------- cards
def meter(s, xr, y, repo, key, n=10, r=3.2, pitch=10):
    lit = max(1, round(n * (0.15 + 0.85 * lnorm(repo))))
    for i in range(n):
        cx = xr - (n - 1 - i) * pitch
        s.add(f'<circle cx="{cx:.1f}" cy="{y}" r="{r}" fill="{s.c(PCOL[key]) if i < lit else s.c("faint")}"/>')

def arrow(s, x, y, col):
    s.add(f'<path d="M{x} {y+10} L{x+10} {y} M{x+2} {y} H{x+10} V{y+8}" stroke="{s.c(col)}" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')

def new_badge(s, xr, y):
    s.add(f'<rect x="{xr-52}" y="{y-14}" width="52" height="22" rx="11" fill="{s.c("orange")}"/>')
    s.text(xr - 26, y + 1.5, 'NOWE', 'MM', 11, 'bg', anchor='middle', ls=1)

def card(repo, theme):
    key, name, desc, plat, stack = ITEMS[repo]
    W, H = 400, 270
    s = SVG(W, H, theme, f'{name} — {desc}')
    s.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="24" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
    s.add(f'<circle cx="34" cy="40" r="5" fill="{s.c(PCOL[key])}"/>')
    s.text(48, 45, fit(plat.upper(), 'M', 12, W - 160 if is_new(repo) else W - 100), 'M', 12, 'dim', ls=1.2)
    arrow(s, W - 42, 33, 'dim')
    if is_new(repo): new_badge(s, W - 56, 39)
    size = 34
    while width(name, 'BB', size, -0.5) > W - 60 and size > 22: size -= 1
    s.text(27, 102, fit(name, 'BB', size, W - 56), 'BB', size, 'ink', ls=-0.5)
    ds = 20
    lines = wrap(desc, 'B', ds, W - 58)
    if len(lines) > 3:
        ds = 18; lines = wrap(desc, 'B', ds, W - 58)
    for i, l in enumerate(lines[:3]):
        s.text(28, 138 + i * 26, l, 'B', ds, 'muted')
    s.add(f'<line x1="28" y1="{H-58}" x2="{W-28}" y2="{H-58}" stroke="{s.c("line")}"/>')
    s.text(28, H - 26, fit(stack, 'M', 13, W - 170), 'M', 13, 'ink')
    meter(s, W - 31, H - 30, repo, key)
    return s

def featured_frame(s, repo, label, key):
    _, name, desc, plat, stack = ITEMS[repo]
    W, H = s.w, s.h
    s.add(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="28" fill="{s.c("surface")}" stroke="{s.c("line")}"/>')
    s.add(f'<circle cx="44" cy="50" r="6" fill="{s.c("orange")}"/>')
    s.text(60, 55, f'{label} · ' + plat.upper(), 'M', 13, 'dim', ls=1.4)
    size = 62
    while width(name, 'BB', size, -1.2) > 620 and size > 30: size -= 1
    s.text(38, 127, name, 'BB', size, 'ink', ls=-1.2)
    for i, l in enumerate(wrap(desc, 'B', 24, 560)[:3]):
        s.text(40, 175 + i * 33, l, 'B', 24, 'muted')
    s.text(40, H - 40, stack, 'M', 14, 'ink')
    meter(s, 640, H - 45, repo, key, n=14, r=3.6, pitch=11)

def featured_ipet(repo, theme):
    W, H = 1200, 340
    s = SVG(W, H, theme, f'{ITEMS[repo][1]} — {ITEMS[repo][2]}')
    featured_frame(s, repo, 'FLAGOWY', ITEMS[repo][0])
    bx, byy, bw, bh = 700, 36, 464, 268
    s.add(f'<rect x="{bx}" y="{byy}" width="{bw}" height="{bh}" rx="20" fill="{s.c("bg")}" stroke="{s.c("line")}"/>')
    s.text(bx + 26, byy + 38, 'PSEUDONIMIZACJA · PRZED WYSŁANIEM DO AI', 'M', 11.5, 'dim', ls=1.3)
    rows = [
        [('{{UCZEN}}', 'ink'), (' funkcjonuje na poziomie', 'muted')],
        [('niepełnosprawności w stopniu', 'muted')],
        [('umiarkowanym. Orzeczenie ', 'muted'), ('{{NR}}', 'ink')],
        [('z poradni ', 'muted'), ('{{PORADNIA}}', 'ink'), (',', 'muted')],
        [('PESEL ', 'muted'), ('{{PESEL}}', 'ink'), (' · OCR lokalny', 'muted')],
    ]
    for i, segs in enumerate(rows):
        s.runs(bx + 26, byy + 76 + i * 28, segs, 'M', 15)
    x = bx + 26; y = byy + bh - 34
    for ptxt in ['WOPFU', 'IPET', 'ICF ×9', 'KES', 'AAC', '.docx']:
        w = width(ptxt, 'M', 12.5) + 24
        s.add(f'<rect x="{x}" y="{y-17}" width="{w:.1f}" height="26" rx="13" fill="none" stroke="{s.c("dim")}" stroke-opacity="0.7"/>')
        s.text(x + 12, y + 1, ptxt, 'M', 12.5, 'muted')
        x += w + 8
    return s

def featured_gta(repo, theme):
    W, H = 1200, 340
    s = SVG(W, H, theme, f'{ITEMS[repo][1]} — {ITEMS[repo][2]}')
    s.css.append('.m{animation:m 3.2s ease-in-out infinite}@keyframes m{0%,100%{opacity:.9}50%{opacity:.35}}')
    featured_frame(s, repo, 'FLAGOWA GRA', ITEMS[repo][0])
    b = json.load(open(f'{SRC}/{repo}/data/buildings.json'))
    pts = [(sum(o['p'][0::2]) / len(o['p'][0::2]), sum(o['p'][1::2]) / len(o['p'][1::2])) for o in b]
    bx, byy, bw, bh = 700, 36, 464, 268
    s.add(f'<rect x="{bx}" y="{byy}" width="{bw}" height="{bh}" rx="20" fill="{s.c("bg")}" stroke="{s.c("line")}"/>')
    cols, rows_, pitch = 86, 41, 5.0
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
                rr = 0.9 + 1.4 * min(1, math.sqrt(v / mx) * 1.4)
                s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="{s.c("ink")}" opacity="0.85"/>')
            else:
                s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="0.55" fill="{s.c("line")}"/>')
    (kx, ky), _ = max(grid.items(), key=lambda kv: kv[1] - 0.02 * ((kv[0][0] - cols/2)**2 + (kv[0][1] - rows_/2)**2))
    gxp, gyp = ox + (kx + 3) * pitch, oy + ky * pitch
    s.add(f'<circle class="m" cx="{gxp:.1f}" cy="{gyp:.1f}" r="16" fill="{s.c("orange")}" opacity="0.25"/>')
    s.add(f'<circle cx="{gxp:.1f}" cy="{gyp:.1f}" r="5.5" fill="{s.c("orange")}"/>')
    for dx, dy in [(-9, -5), (-10, 5), (-5, 9)]:
        s.add(f'<circle cx="{gxp + dx*pitch:.1f}" cy="{gyp + dy*pitch:.1f}" r="4" fill="none" stroke="{s.c("ink")}" stroke-width="2"/>')
    s.text(bx + 24, byy + bh - 14, 'MAKÓW MAZOWIECKI · BUDYNKI Z OPENSTREETMAP', 'M', 11.5, 'dim', ls=1.3)
    return s

def featured_metaverse(repo, theme):
    W, H = 1200, 340
    s = SVG(W, H, theme, f'{ITEMS[repo][1]} — {ITEMS[repo][2]}')
    featured_frame(s, repo, 'FLAGOWY DESIGN', ITEMS[repo][0])
    bx, byy, bw, bh = 700, 36, 464, 268
    s.add(f'<defs><clipPath id="mv"><rect x="{bx}" y="{byy}" width="{bw}" height="{bh}" rx="20"/></clipPath></defs>')
    s.add(f'<rect x="{bx}" y="{byy}" width="{bw}" height="{bh}" rx="20" fill="{s.c("bg")}" stroke="{s.c("line")}"/>')
    vx, vy, f = bx + bw / 2, byy + 112, 150
    def pr(x, y, z): return vx + f * x / z, vy - f * y / z
    XW, YF, YC, ZN, ZF = 2.0, -1.0, 1.25, 0.9, 9.0
    dots = []
    zs, z = [], ZN
    while z < ZF:
        zs.append(z); z *= 1.075
    for z in zs:
        rr = max(0.45, 2.3 / z)
        x = -XW
        while x <= XW + 1e-6:
            px_, py_ = pr(x, YF, z); dots.append((px_, py_, rr, 'ink' if abs(x) < 0.01 else 'g3')); x += 0.2
        y = YF + 0.2
        while y < YC:
            for sx in (-XW, XW):
                px_, py_ = pr(sx, y, z); dots.append((px_, py_, rr * 0.8, 'g4'))
            y += 0.2
    x = -XW
    while x <= XW + 1e-6:
        y = YF
        while y <= YC + 1e-6:
            px_, py_ = pr(x, y, ZF); dots.append((px_, py_, 0.5, 'g4')); y += 0.2
        x += 0.2
    by_col = collections.defaultdict(list)
    for px_, py_, rr, col in dots:
        if bx < px_ < bx + bw and byy < py_ < byy + bh:
            by_col[col].append(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="{rr:.2f}"/>')
    g = ''.join(f'<g fill="{s.c(c)}">{"".join(v)}</g>' for c, v in by_col.items())
    frames = []
    for i, (z0, z1) in enumerate([(1.9, 2.7), (3.3, 4.3), (5.3, 6.5)]):
        for side in (-1, 1):
            sx = side * XW
            pts = [pr(sx, -0.15, z0), pr(sx, -0.15, z1), pr(sx, 0.75, z1), pr(sx, 0.75, z0)]
            d = 'M' + ' L'.join(f'{a:.1f} {b:.1f}' for a, b in pts) + 'Z'
            acc = (i == 1 and side == 1)
            frames.append(f'<path d="{d}" fill="{s.c("orange") if acc else s.c("surface")}" stroke="{s.c("orange") if acc else s.c("g2")}" stroke-width="1.2"/>')
    (ax, ay), (bx2, by2) = pr(-0.7, -0.1, ZF), pr(0.7, 0.8, ZF)
    frames.append(f'<rect x="{ax:.1f}" y="{by2:.1f}" width="{bx2-ax:.1f}" height="{ay-by2:.1f}" fill="{s.c("surface")}" stroke="{s.c("g2")}"/>')
    s.add(f'<defs><linearGradient id="mvf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{s.c("bg")}" stop-opacity="0"/>'
          f'<stop offset=".7" stop-color="{s.c("bg")}"/></linearGradient></defs>')
    s.add(f'<g clip-path="url(#mv)">{g}{"".join(frames)}<rect x="{bx}" y="{byy+bh-56}" width="{bw}" height="56" fill="url(#mvf)"/></g>')
    s.text(bx + 24, byy + bh - 14, 'SALA WYSTAWOWA · 18 GNIAZD · TRYB VR', 'M', 11.5, 'dim', ls=1.3)
    return s

FEAT_FN = {'dokshelper': featured_ipet, 'GTA26': featured_gta, 'metaverse': featured_metaverse}

def footer(theme):
    W, H = 1200, 120
    s = SVG(W, H, theme, USER)
    s.css.append('.f{animation:f 3.6s ease-in-out infinite}@keyframes f{0%,100%{opacity:.2}50%{opacity:1}}')
    n = 150
    for i in range(n):
        y = 40 + 14 * math.sin(i / n * math.pi * 4)
        col = 'orange' if i == n // 2 else ('ink' if i % 3 == 0 else 'g3')
        s.add(f'<circle class="f" style="animation-delay:{i*0.024:.2f}s" cx="{10 + i*(1180/(n-1)):.1f}" cy="{y:.1f}" r="{2.6 if col == "orange" else 1.7}" fill="{s.c(col)}"/>')
    s.text(W / 2, 100, f'{USER} · działa lokalnie · zrobione w Polsce', 'M', 13, 'dim', anchor='middle', ls=1.5)
    return s

# ================================================================ build
adir = os.path.join(OUT, ASSETS)
if os.path.isdir(adir):
    for f in glob.glob(os.path.join(adir, '*.svg')): os.remove(f)   # usuń grafiki repo, których już nie ma
os.makedirs(adir, exist_ok=True)

def is_feat(k, r): return FEATURED.get(k) == r and r in FEAT_FN and (r != 'GTA26' or os.path.exists(f'{SRC}/{r}/data/buildings.json'))

for th in ('dark', 'light'):
    save('hero', th, hero(th))
    save('section-00', th, section('00', 'Statystyki', 'Całe konto i wszystkie repozytoria, liczone na nowo przy każdej aktualizacji.', NREPO, th))
    save('stats', th, stats_overview(th))
    save('stats-repos', th, stats_repos(th))
    save('langs', th, langs(th))
    save('footer', th, footer(th))
    for k in CATS:
        save(f'section-{CATS[k]["no"]}', th, section(CATS[k]['no'], CATS[k]['title'], CATS[k]['sub'], len(P[k]), th))
        for r in P[k]:
            if is_feat(k, r): save(f'feat-{r}', th, FEAT_FN[r](r, th))
            else: save(f'card-{r}', th, card(r, th))

def pic(name, alt, w=None, href=None):
    wa = f' width="{w}"' if w else ''
    p = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{ASSETS}/{name}-dark.svg">'
         f'<img alt="{html.escape(alt)}" src="{ASSETS}/{name}-light.svg"{wa}></picture>')
    return f'<a href="{href}">{p}</a>' if href else p

GH = f'https://github.com/{USER}/'
langs_alt = 'Języki: ' + ', '.join(n for n, _ in langtot.most_common())
md = [f'<!-- Okładka profilu {USER}. Generowana automatycznie przez _generator/build.py (.github/workflows/profile.yml) — nie edytuj ręcznie. -->', '',
      '<div align="center">', '',
      pic('hero', f'{USER} — aplikacje customowe · praktyczne rozwiązania · design · eksperymentalnie · vib3c0DinG', '100%', f'https://github.com/{USER}'),
      '', '<br>', '',
      pic('section-00', '00 — Statystyki', '100%'), '', '<br>', '',
      pic('stats', f'Statystyki: {NREPO} repozytoriów, {NCOMMITS} commitów, ≈{round(TOTAL/1000)} tys. linii kodu, {len(DAYS)} aktywnych dni', '100%'), '',
      pic('langs', langs_alt, '100%'), '',
      pic('stats-repos', f'Wszystkie repozytoria ({NREPO}) z liczbą commitów i datą ostatniej zmiany', '100%'), '', '<br>', '']
for k in CATS:
    items = P[k]
    md += [pic(f'section-{CATS[k]["no"]}', f'{CATS[k]["no"]} — {CATS[k]["title"]}', '100%'), '', '<br>', '']
    grid = []
    for r in items:
        if is_feat(k, r):
            md += [pic(f'feat-{r}', f'{ITEMS[r][1]} — {ITEMS[r][2]}', '100%', GH + r), '']
        else:
            grid.append(r)
    for i in range(0, len(grid), 3):
        md.append('\n'.join(pic(f'card-{r}', f'{ITEMS[r][1]} — {ITEMS[r][2]}', '32%', GH + r) for r in grid[i:i+3]))
        md.append('')
    md += ['<br>', '']
md += [f'<sub>i jeszcze &nbsp;→&nbsp; <a href="{GH}{USER}"><code>{USER}</code></a> strona z projektami</sub>', '', '<br><br>', '',
       pic('footer', f'{USER} · działa lokalnie · zrobione w Polsce', '100%'), '', '</div>', '']
open(os.path.join(OUT, 'README.md'), 'w').write('\n'.join(md))
print('ok', NREPO, 'repo,', NCOMMITS, 'commitów,', TOTAL, 'linii', langtot.most_common())
for k in CATS: print(' ', CATS[k]['no'], CATS[k]['short'], '→', ', '.join(P[k]))
