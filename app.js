/* Strona główna. Treść i wygląd są w config.json, a zmieniasz je w panelu administratora (admin.js). */
(() => {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const root = document.documentElement;
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ===================== Motywy ===================== */
  const PRESETS = {
    mgla:     { label: "Mgła",     dark: false, pair: "noc",      bg: "#e9ecf0", surface: "#f6f7f9", ink: "#151922", muted: "#5d6574", line: "#d3d8e0", accent: "#3245e6" },
    papier:   { label: "Papier",   dark: false, pair: "atrament", bg: "#f6f6f3", surface: "#ffffff", ink: "#1b1b1d", muted: "#626268", line: "#dddcd8", accent: "#d92d6a" },
    lod:      { label: "Lód",      dark: false, pair: "glebia",   bg: "#e6f0f2", surface: "#f5fafb", ink: "#0f2a30", muted: "#4d6a70", line: "#c9dde1", accent: "#087a7a" },
    pistacja: { label: "Pistacja", dark: false, pair: "las",      bg: "#ecf1e4", surface: "#f7faf2", ink: "#1c2a16", muted: "#5a6a50", line: "#d3dcc6", accent: "#6a3fd6" },
    roz:      { label: "Róż",      dark: false, pair: "wino",     bg: "#f7eaee", surface: "#fdf6f8", ink: "#2b1620", muted: "#7a5a66", line: "#ead3db", accent: "#d6331f" },
    lawenda:  { label: "Lawenda",  dark: false, pair: "atrament", bg: "#ebe8f6", surface: "#f7f6fc", ink: "#1d1934", muted: "#625d80", line: "#d8d3ec", accent: "#c94a06" },
    beton:    { label: "Beton",    dark: false, pair: "grafit",   bg: "#e2e2df", surface: "#efefec", ink: "#111111", muted: "#5c5c58", line: "#cbcbc6", accent: "#cc3d00" },
    noc:      { label: "Noc",      dark: true,  pair: "mgla",     bg: "#0f1218", surface: "#171b23", ink: "#e7eaf0", muted: "#8d95a5", line: "#272d39", accent: "#8e9bff" },
    atrament: { label: "Atrament", dark: true,  pair: "lawenda",  bg: "#120e24", surface: "#1b1633", ink: "#ece8ff", muted: "#9a92c4", line: "#2c2550", accent: "#ff7ac6" },
    glebia:   { label: "Głębia",   dark: true,  pair: "lod",      bg: "#061a22", surface: "#0c2630", ink: "#dff3f5", muted: "#7fa3ab", line: "#183a45", accent: "#3de0d0" },
    las:      { label: "Las",      dark: true,  pair: "pistacja", bg: "#0f1d17", surface: "#15271f", ink: "#e2ede6", muted: "#8ea698", line: "#22392d", accent: "#f2c14e" },
    wino:     { label: "Wino",     dark: true,  pair: "roz",      bg: "#1d0c13", surface: "#2a131c", ink: "#f6e6ea", muted: "#b08a96", line: "#3d1d29", accent: "#ffb347" },
    grafit:   { label: "Grafit",   dark: true,  pair: "beton",    bg: "#18181a", surface: "#222225", ink: "#ededea", muted: "#9a9a96", line: "#313134", accent: "#ffb86b" },
    kontrast: { label: "Kontrast", dark: true,  pair: "papier",   bg: "#000000", surface: "#0d0d0d", ink: "#ffffff", muted: "#c8c8c8", line: "#3a3a3a", accent: "#ffe500" }
  };

  /* ===================== Koncepcje ===================== */
  const CONCEPTS = {
    matryca:  { label: "Matryca",  desc: "Napis z kropek, który rozsypuje się pod kursorem. Lista w kategoriach.", font: "Bricolage Grotesque", bg: "fala" },
    kafle:    { label: "Kafle",    desc: "Wielkie litery zmieniające grubość pod kursorem. Projekty w siatce kafli.", font: "Bricolage Grotesque", bg: "przeplyw" },
    terminal: { label: "Terminal", desc: "Tekst wpisywany jak w konsoli. Projekty jak listing katalogu.", font: "JetBrains Mono", bg: "deszcz" },
    indeks:   { label: "Indeks",   desc: "Duży opis i wielkie nazwy projektów, jedna pod drugą.", font: "Fraunces", bg: "fala" },
    klasyk:   { label: "Linktree", desc: "Awatar na środku i duże przyciski z projektami.", font: "Sora", bg: "fala" }
  };

  /* Czcionki z Google Fonts (z polskimi znakami) */
  const FONTS = {
    "Bricolage Grotesque": "Bricolage+Grotesque:opsz,wght@12..96,200..800",
    "Familjen Grotesk": "Familjen+Grotesk:wght@400..700",
    "Sora": "Sora:wght@300..800",
    "Unbounded": "Unbounded:wght@300..900",
    "Syne": "Syne:wght@400..800",
    "Fraunces": "Fraunces:opsz,wght@9..144,300..900",
    "JetBrains Mono": "JetBrains+Mono:wght@400..800",
    "Space Mono": "Space+Mono:wght@400;700"
  };

  const DEFAULTS = {
    profile: { handle: "z0z6", name: "z0z6", bio: "", avatar: "", links: [] },
    concept: "matryca",
    theme: { preset: "auto", accent: null, custom: { bg: "#eef0f4", surface: "#ffffff", ink: "#14161c", muted: "#5f6675", line: "#d6dae2", accent: "#3245e6" }, font: "Bricolage Grotesque", radius: 14, density: "comfortable" },
    matrix: { enabled: true, shape: "circle", cell: 9, dot: 0.62, intro: "assemble", cursor: "repel", ambient: true, height: 150 },
    background: { enabled: true, style: "fala", spacing: 22, intensity: 0.55, speed: 1, cursor: true, ripples: true },
    ui: { search: true, showUpdated: true, newTab: true },
    admin: { owner: "z0z6", repo: "z0z6.github.io", branch: "main", path: "config.json" },
    categories: [], projects: []
  };
  function withDefaults(c) {
    const o = JSON.parse(JSON.stringify(c || {}));
    for (const k in DEFAULTS) {
      const d = DEFAULTS[k];
      if (Array.isArray(d)) o[k] = Array.isArray(o[k]) ? o[k] : [];
      else if (d && typeof d === "object") o[k] = Object.assign({}, JSON.parse(JSON.stringify(d)), o[k] || {});
      else if (o[k] === undefined) o[k] = d;
    }
    o.theme.custom = Object.assign({}, DEFAULTS.theme.custom, o.theme.custom || {});
    return o;
  }

  let CFG = withDefaults({});
  const bgOn = () => CFG.background.enabled && CFG.background.style !== "none";
  const isMatryca = () => CFG.concept === "matryca" && CFG.matrix.enabled;

  /* ===================== Kolory ===================== */
  let manualPreset = null;
  function systemDark() {
    const t = root.getAttribute("data-theme");
    if (t === "dark") return true;
    if (t === "light") return false;
    return matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function currentPresetKey() {
    if (manualPreset) return manualPreset;
    const p = CFG.theme.preset;
    if (p === "wlasny") return "wlasny";
    if (p === "auto" || !PRESETS[p]) return systemDark() ? "noc" : "mgla";
    return p;
  }
  function luminance(hex) {
    const n = parseInt(hex.slice(1), 16);
    const ch = [n >> 16, (n >> 8) & 255, n & 255].map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
  }
  const isHex = v => typeof v === "string" && /^#[0-9a-f]{6}$/i.test(v);
  function palette() {
    const key = currentPresetKey();
    let p;
    if (key === "wlasny") {
      const c = CFG.theme.custom;
      p = Object.assign({}, PRESETS.mgla, c, { dark: luminance(isHex(c.bg) ? c.bg : "#ffffff") < 0.2 });
    } else p = PRESETS[key];
    const accent = isHex(CFG.theme.accent) ? CFG.theme.accent : p.accent;
    return Object.assign({}, p, { accent });
  }
  function applyTheme() {
    const p = palette();
    for (const k of ["bg", "surface", "ink", "muted", "line", "accent"]) root.style.setProperty("--" + k, p[k]);
    root.style.setProperty("--on-accent", luminance(p.accent) > 0.45 ? "#111111" : "#ffffff");
    root.style.setProperty("--radius", (+CFG.theme.radius || 0) + "px");
    root.style.colorScheme = p.dark ? "dark" : "light";
    const meta = $('meta[name="theme-color"]'); if (meta) meta.content = p.bg;
    document.body.classList.toggle("compact", CFG.theme.density === "compact");
    Matrix.setColors(p.ink, p.muted, p.accent);
    Bg.setColors(p.muted, p.accent);
    Avatar.draw();
  }
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => applyTheme());
  new MutationObserver(() => applyTheme()).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
  $("#theme-toggle").addEventListener("click", () => {
    const key = currentPresetKey();
    manualPreset = key === "wlasny" ? (palette().dark ? "mgla" : "noc") : PRESETS[key].pair;
    applyTheme();
  });

  /* ===================== Czcionka ===================== */
  let loadedFont = "";
  function applyFont() {
    const f = (CFG.theme.font || "Bricolage Grotesque").trim();
    if (f !== loadedFont) {
      const q = FONTS[f] || (f.replace(/\s+/g, "+") + ":wght@400;700");
      // Terminal zawsze potrzebuje kroju o stałej szerokości
      const extra = CFG.concept === "terminal" && f !== "JetBrains Mono" ? "&family=" + FONTS["JetBrains Mono"] : "";
      $("#font-css").href = "https://fonts.googleapis.com/css2?family=" + q + extra + "&display=swap";
      loadedFont = f;
    }
    const fallback = /mono/i.test(f) ? 'ui-monospace, "SF Mono", Menlo, Consolas, monospace' : '"Segoe UI", system-ui, sans-serif';
    root.style.setProperty("--font", `"${f}", ${fallback}`);
    root.style.setProperty("--mono", /mono/i.test(f) ? `"${f}", ${fallback}` : '"JetBrains Mono", ui-monospace, Menlo, Consolas, monospace');
    return f;
  }
  function fontReady(f, text) {
    if (!document.fonts || !document.fonts.load) return Promise.resolve();
    return Promise.race([document.fonts.load(`800 80px "${f}"`, text || "z0z6"), new Promise(r => setTimeout(r, 1500))]).catch(() => {});
  }

  /* ===================== Kształt kropki (wspólny) ===================== */
  function dotShape(ctx, x, y, r) {
    const s = CFG.matrix.shape;
    if (s === "square") ctx.fillRect(x - r, y - r, r * 2, r * 2);
    else if (s === "plus") { const w = r * 0.62; ctx.fillRect(x - r, y - w / 2, r * 2, w); ctx.fillRect(x - w / 2, y - r, w, r * 2); }
    else { ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill(); }
  }
  const hexRgb = h => { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; };
  const mixRgb = (a, b, t) => `rgb(${a[0] + (b[0] - a[0]) * t | 0},${a[1] + (b[1] - a[1]) * t | 0},${a[2] + (b[2] - a[2]) * t | 0})`;

  /* ===================== Matryca kropek (koncepcja Matryca) ===================== */
  const Matrix = (() => {
    const canvas = $("#matrix");
    const wrap = canvas.parentElement;
    const ctx = canvas.getContext("2d");
    let W = 0, H = 0, cell = 9, dots = [], raf = 0, t0 = 0, visible = true, introMode = "none";
    const pointer = { x: -9999, y: -9999, active: false };
    let ink = [21, 25, 34], muted = [93, 101, 116], acc = [50, 69, 230];
    let fontFamily = "Bricolage Grotesque";

    function build(withIntro) {
      if (!isMatryca()) { dots = []; return; }
      const m = CFG.matrix;
      const rect = wrap.getBoundingClientRect();
      if (rect.width < 10) return;
      W = Math.max(200, Math.round(rect.width));
      H = Math.round(Math.min(+m.height || 150, Math.max(90, W * 0.36)));
      root.style.setProperty("--matrix-h", H + "px");
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cell = clamp(+m.cell || 9, 5, 16);

      const off = document.createElement("canvas");
      off.width = W; off.height = H;
      const o = off.getContext("2d", { willReadFrequently: true });
      const text = CFG.profile.handle || "z0z6";
      let size = H * 1.18;
      const setFont = () => { o.font = `800 ${size}px "${fontFamily}", system-ui, sans-serif`; };
      setFont();
      const pad = cell;
      const mw = o.measureText(text).width;
      if (mw > W - pad * 2) { size *= (W - pad * 2) / mw; setFont(); }
      const mt = o.measureText(text);
      const asc = mt.actualBoundingBoxAscent || size * 0.72, desc = mt.actualBoundingBoxDescent || 0;
      o.fillText(text, pad + (mt.actualBoundingBoxLeft || 0), (H - (asc + desc)) / 2 + asc);
      const data = o.getImageData(0, 0, W, H).data;

      dots = [];
      const cols = Math.floor(W / cell), rows = Math.floor(H / cell);
      const ox = (W - cols * cell) / 2 + cell / 2, oy = (H - rows * cell) / 2 + cell / 2;
      const intro = withIntro && !reduceMotion ? m.intro : "none";
      for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
        const x = ox + c * cell, y = oy + r * cell;
        const isText = data[((y | 0) * W + (x | 0)) * 4 + 3] > 110;
        const d = { hx: x, hy: y, x, y, vx: 0, vy: 0, t: isText, delay: 0, seed: Math.random() * 6.28 };
        if (isText && intro === "assemble") {
          const ang = Math.random() * Math.PI * 2, dist = 120 + Math.random() * W * 0.5;
          d.x = x + Math.cos(ang) * dist; d.y = y + Math.sin(ang) * dist * 0.5;
          d.delay = (x / W) * 380 + Math.random() * 260;
        }
        dots.push(d);
      }
      t0 = performance.now();
      introMode = intro;
      start();
    }

    function frame(now) {
      raf = 0;
      if (!dots.length) return;
      const m = CFG.matrix, el = now - t0, R = cell * 8;
      const r0 = cell * clamp(+m.dot || 0.62, 0.2, 0.95) / 2;
      ctx.clearRect(0, 0, W, H);
      let moving = false;
      const scanX = introMode === "scan" ? (el / 900) * (W + 80) - 40 : Infinity;
      if (introMode === "scan" && scanX < W + 40) moving = true;
      const bgActive = bgOn();

      for (let i = 0; i < dots.length; i++) {
        const d = dots[i];
        const pdx = d.x - pointer.x, pdy = d.y - pointer.y;
        const pd = Math.sqrt(pdx * pdx + pdy * pdy);
        if (!d.t) {
          let a = bgActive ? 0 : 0.13;
          if (m.ambient && !reduceMotion && !bgActive) a += 0.07 * Math.sin(el * 0.0011 + d.hx * 0.025 + d.hy * 0.04 + d.seed * 0.3);
          let glow = 0;
          if (pointer.active && m.cursor !== "none" && pd < R * 1.3) { glow = 1 - pd / (R * 1.3); a += glow * 0.55; }
          if (introMode === "scan") a *= clamp((scanX - d.hx) / 60, 0, 1);
          if (a <= 0.01) continue;
          ctx.globalAlpha = a;
          ctx.fillStyle = mixRgb(muted, acc, glow);
          dotShape(ctx, d.hx, d.hy, r0 * (0.55 + glow * 0.3));
          continue;
        }
        if (el >= d.delay) {
          let fx = (d.hx - d.x) * 0.075, fy = (d.hy - d.y) * 0.075;
          if (pointer.active && m.cursor !== "none" && pd < R && pd > 0.01) {
            const f = Math.pow(1 - pd / R, 2) * (m.cursor === "repel" ? 5.5 : -2.2);
            fx += (pdx / pd) * f; fy += (pdy / pd) * f;
          }
          d.vx = (d.vx + fx) * 0.8; d.vy = (d.vy + fy) * 0.8;
          d.x += d.vx; d.y += d.vy;
        }
        const disp = Math.hypot(d.x - d.hx, d.y - d.hy);
        if (disp > 0.15 || Math.abs(d.vx) > 0.05) moving = true;
        let alpha = 1;
        if (introMode === "assemble") alpha = clamp((el - d.delay) / 300, 0, 1);
        if (introMode === "scan") alpha = clamp((scanX - d.hx) / 40, 0, 1);
        const heat = Math.min(1, disp / (cell * 1.6));
        ctx.globalAlpha = alpha;
        ctx.fillStyle = mixRgb(ink, acc, heat > 0.02 ? heat : 0);
        dotShape(ctx, d.x, d.y, r0 * (1 + heat * 0.25));
      }
      ctx.globalAlpha = 1;
      if (introMode !== "none" && el > 2200) introMode = "none";
      const keep = visible && !reduceMotion && (moving || pointer.active || (m.ambient && !bgActive) || introMode !== "none");
      if (keep) raf = requestAnimationFrame(frame);
    }
    function start() { if (!raf && dots.length) raf = requestAnimationFrame(frame); }

    function onMove(e) {
      const r = canvas.getBoundingClientRect();
      pointer.x = e.clientX - r.left; pointer.y = e.clientY - r.top; pointer.active = true; start();
    }
    const leave = () => { pointer.active = false; pointer.x = pointer.y = -9999; start(); };
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerdown", onMove);
    canvas.addEventListener("pointerleave", leave);
    canvas.addEventListener("pointerup", e => { if (e.pointerType !== "mouse") leave(); });
    new IntersectionObserver(es => { visible = es[0].isIntersecting; if (visible) start(); }).observe(canvas);
    let rt;
    new ResizeObserver(() => { clearTimeout(rt); rt = setTimeout(() => { if (isMatryca() && Math.abs(wrap.getBoundingClientRect().width - W) > 2) build(false); }, 120); }).observe(wrap);

    return {
      rebuild(intro, family) {
        if (family) fontFamily = family;
        document.body.classList.toggle("has-matrix", isMatryca());
        build(!!intro);
      },
      setColors(i, m, a) { ink = hexRgb(i); muted = hexRgb(m); acc = hexRgb(a); start(); },
      kick: start
    };
  })();

  /* ===================== Tło strony ===================== */
  const Bg = (() => {
    const cv = $("#bg");
    const ctx = cv.getContext("2d");
    let W = 0, H = 0, raf = 0, ripples = [];
    const ptr = { x: -1e4, y: -1e4, on: false };
    let muted = [93, 101, 116], acc = [50, 69, 230];
    const t0 = performance.now();
    const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };

    function size() {
      const dpr = Math.min(1.5, window.devicePixelRatio || 1);
      W = window.innerWidth; H = window.innerHeight;
      cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      start();
    }

    function frame(now) {
      raf = 0;
      ctx.clearRect(0, 0, W, H);
      if (!bgOn()) { cv.style.display = "none"; return; }
      cv.style.display = "";
      const b = CFG.background, style = b.style;
      const flow = style === "przeplyw", rain = style === "deszcz";
      const t = reduceMotion ? 0 : ((now - t0) / 1000) * clamp(+b.speed || 1, 0.1, 3);
      let sp = clamp(+b.spacing || 22, 14, 40);
      if (W < 600) sp = Math.max(sp, 24);
      const I = clamp(+b.intensity, 0, 1);
      const scroll = window.scrollY * 0.25;
      const y0 = -(scroll % sp);
      const base = sp * 0.12;
      const mid = W / 2, half = Math.min(W / 2, 360);
      ripples = ripples.filter(r => now - r.t < 2200);
      const R = 180, trail = 260;

      let ci = 0;
      for (let x = sp / 2; x < W + sp; x += sp, ci++) {
        const colSpeed = 40 + hash(ci) * 110, colOff = hash(ci + 99) * (H + trail * 2);
        const head = rain ? ((t * colSpeed + colOff) % (H + trail * 2)) - trail : 0;
        const dxm = Math.abs(x - mid);
        const mask = dxm < half ? 0.4 : 0.4 + 0.6 * Math.min(1, (dxm - half) / 140);
        for (let y = y0 - sp; y < H + sp; y += sp) {
          const wy = y + scroll;
          let n, v;
          if (rain) {
            const behind = head - y;
            n = behind >= 0 && behind < trail ? Math.pow(1 - behind / trail, 1.6) : 0;
            v = n * 2 - 1;
          } else {
            v = (Math.sin(x * 0.011 + t * 0.7) + Math.sin(wy * 0.014 - t * 0.5)
               + Math.sin((x + wy) * 0.006 + t * 0.33) + Math.sin((x - wy) * 0.009 - t * 0.41)) / 4;
            n = (v + 1) / 2;
          }
          let px = x, py = y, boost = 0;
          if (flow) { const a = v * 6.2832 + t * 0.25; px += Math.cos(a) * sp * 0.3; py += Math.sin(a) * sp * 0.3; }
          if (b.cursor && ptr.on) {
            const d = Math.hypot(px - ptr.x, py - ptr.y);
            if (d < R) { const k = 1 - d / R; boost += k * k; }
          }
          for (let i = 0; i < ripples.length; i++) {
            const r = ripples[i], age = now - r.t;
            const rr = age * 0.6, life = 1 - age / 2200;
            const dx = px - r.x, dy = py - r.y, dd = Math.hypot(dx, dy) || 1;
            const k = 1 - Math.abs(dd - rr) / 50;
            if (k > 0) { const f = k * life; boost += f; px += (dx / dd) * f * 7; py += (dy / dd) * f * 7; }
          }
          const alpha = rain
            ? Math.min(0.9, (0.05 + 0.75 * I * n) * mask + boost * 0.45)
            : Math.min(0.85, (0.06 + 0.42 * I * n * n) * mask + boost * 0.45);
          if (alpha < 0.02) continue;
          const tint = Math.min(1, (rain ? (n > 0.92 ? 1 : n * 0.5) : n * n * n * 0.9) * I + boost);
          ctx.globalAlpha = alpha;
          ctx.fillStyle = mixRgb(muted, acc, tint);
          const r0 = flow ? base * 1.15 : rain ? base * (0.8 + n * 0.8) : base * (0.55 + n * 1.5 * (0.4 + I));
          dotShape(ctx, px, py, r0 * (1 + boost * 0.7));
        }
      }
      ctx.globalAlpha = 1;
      if (!reduceMotion) raf = requestAnimationFrame(frame);
    }
    function start() { if (!raf) raf = requestAnimationFrame(frame); }

    window.addEventListener("resize", size);
    window.addEventListener("scroll", () => { if (reduceMotion) start(); }, { passive: true });
    window.addEventListener("pointermove", e => { ptr.x = e.clientX; ptr.y = e.clientY; ptr.on = e.pointerType === "mouse"; });
    document.addEventListener("mouseleave", () => { ptr.on = false; });
    window.addEventListener("pointerdown", e => {
      if (!CFG.background.ripples || reduceMotion || e.target.closest(".adm")) return;
      ripples.push({ x: e.clientX, y: e.clientY, t: performance.now() });
      if (ripples.length > 5) ripples.shift();
    });
    return { init: size, setColors(m, a) { muted = hexRgb(m); acc = hexRgb(a); start(); }, kick: start };
  })();

  /* ===================== Awatar (koncepcja Linktree) ===================== */
  const Avatar = (() => {
    const wrap = $("#avatar-wrap");
    let last = "";
    function draw() {
      const src = CFG.profile.avatar;
      if (src) {
        if (last !== "img:" + src) { wrap.innerHTML = `<img alt="" src="${esc(src)}">`; last = "img:" + src; }
        return;
      }
      // Bez zdjęcia: symetryczny wzór z kropek wyliczony z nazwy
      let c = $("canvas", wrap);
      if (!c) { wrap.innerHTML = "<canvas></canvas>"; c = $("canvas", wrap); }
      last = "dots";
      const S = 208; c.width = S; c.height = S;
      const g = c.getContext("2d");
      const p = palette();
      g.fillStyle = p.surface; g.fillRect(0, 0, S, S);
      let h = 2166136261;
      for (const ch of (CFG.profile.handle || "z0z6")) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
      const n = 7, cell = S / (n + 2);
      for (let y = 0; y < n; y++) for (let x = 0; x < Math.ceil(n / 2); x++) {
        h ^= h << 13; h ^= h >>> 17; h ^= h << 5;
        const on = (h >>> 0) % 100 < 55;
        if (!on) continue;
        const accent = ((h >>> 8) % 100) < 35;
        g.fillStyle = accent ? p.accent : p.ink;
        for (const xx of [x, n - 1 - x]) dotShape(g, cell * (xx + 1.5), cell * (y + 1.5), cell * 0.36);
      }
    }
    return { draw };
  })();

  /* ===================== Terminal (koncepcja Terminal) ===================== */
  const Term = (() => {
    const el = $("#term");
    let timer = 0, runId = 0;
    function run(animate) {
      clearTimeout(timer); runId++;
      if (CFG.concept !== "terminal") { el.innerHTML = ""; return; }
      const id = runId;
      const user = (CFG.profile.handle || "z0z6");
      const prompt = `${user}@github:~$ `;
      const script = [
        { p: prompt, cmd: "whoami" },
        { out: user, big: true },
        { p: prompt, cmd: "cat o-mnie.txt" },
        { out: CFG.profile.bio || "" },
        { p: prompt, cmd: "" }
      ];
      if (!animate || reduceMotion) {
        el.innerHTML = script.map(lineHTML).join("") .replace(/<\/div>$/, '<span class="caret"></span></div>');
        return;
      }
      el.innerHTML = "";
      let li = 0;
      const next = () => {
        if (id !== runId) return;
        if (li >= script.length) return;
        const s = script[li++];
        const div = document.createElement("div");
        el.appendChild(div);
        if (s.out !== undefined) {
          div.className = "out" + (s.big ? " big" : "");
          div.textContent = s.out;
          timer = setTimeout(next, 160);
          return;
        }
        div.innerHTML = `<span class="p">${esc(s.p)}</span><span class="c"></span><span class="caret"></span>`;
        const c = div.querySelector(".c");
        let k = 0;
        const type = () => {
          if (id !== runId) return;
          if (k < s.cmd.length) { c.textContent += s.cmd[k++]; timer = setTimeout(type, 45 + Math.random() * 50); }
          else if (li < script.length) { div.querySelector(".caret").remove(); timer = setTimeout(next, 260); }
        };
        timer = setTimeout(type, 240);
      };
      next();
    }
    function lineHTML(s) {
      if (s.out !== undefined) return `<div class="out${s.big ? " big" : ""}">${esc(s.out)}</div>`;
      return `<div><span class="p">${esc(s.p)}</span>${esc(s.cmd)}</div>`;
    }
    return { run };
  })();

  /* ===================== Litery (koncepcja Kafle) ===================== */
  const Letters = (() => {
    const h1 = $("#handle");
    let chars = [];
    function render() {
      const text = CFG.profile.handle || "z0z6";
      if (CFG.concept === "kafle") {
        h1.innerHTML = Array.from(text).map((ch, k) => `<span class="ch" style="--k:${k}">${esc(ch)}</span>`).join("");
        h1.setAttribute("aria-label", text);
        chars = $$(".ch", h1);
      } else { h1.textContent = text; h1.removeAttribute("aria-label"); chars = []; }
    }
    window.addEventListener("pointermove", e => {
      if (!chars.length || reduceMotion) return;
      for (const c of chars) {
        const r = c.getBoundingClientRect();
        const d = Math.hypot(e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2));
        c.style.setProperty("--w", Math.round(200 + 600 * clamp(d / 420, 0, 1)));
      }
    });
    return { render };
  })();

  /* ===================== Profil ===================== */
  function renderProfile() {
    document.title = CFG.profile.name || CFG.profile.handle || "Portfolio";
    Letters.render();
    $("#bio").textContent = CFG.profile.bio || "";
    const target = CFG.ui.newTab ? ' target="_blank" rel="noopener"' : "";
    $("#links").innerHTML = (CFG.profile.links || []).filter(l => l.url).map(l => {
      const isMail = /^mailto:/i.test(l.url);
      const shown = isMail ? l.url.replace(/^mailto:/i, "") : (l.label || l.url);
      return `<a class="pill" href="${esc(l.url)}"${isMail ? "" : target}>${esc(shown)}</a>`;
    }).join("");
  }

  /* ===================== Projekty ===================== */
  const fold = s => String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l");
  const today = new Date(); today.setHours(0, 0, 0, 0);
  function ago(iso) {
    if (!iso) return "";
    const days = Math.round((today - new Date(iso + "T00:00:00")) / 864e5);
    if (isNaN(days)) return "";
    if (days <= 0) return "zmiana dziś";
    if (days === 1) return "zmiana wczoraj";
    if (days < 14) return `zmiana ${days} dni temu`;
    if (days < 60) return `zmiana ${Math.round(days / 7)} tyg. temu`;
    if (days < 365) return `zmiana ${Math.round(days / 30)} mies. temu`;
    return "zmiana ponad rok temu";
  }
  const plural = (n, one, few, many) => {
    const t = n % 10, h = n % 100;
    if (n === 1) return one;
    return t >= 2 && t <= 4 && (h < 12 || h > 14) ? few : many;
  };
  const repoUrl = p => p.repo ? (/^https?:/.test(p.repo) ? p.repo : `https://github.com/${CFG.admin.owner || CFG.profile.handle}/${p.repo}`) : null;

  function rowHTML(p, catLabel) {
    const target = CFG.ui.newTab ? ' target="_blank" rel="noopener"' : "";
    const repo = repoUrl(p);
    const primary = p.demo || p.download || repo || "#";
    const verb = p.demo ? "otwórz w przeglądarce" : p.download ? "pobierz" : "zobacz kod";
    const hay = fold([p.name, p.desc, p.repo, (p.platforms || []).join(" "), catLabel, (p.tags || []).join(" ")].join(" "));
    const plats = (p.platforms || []).map(x => `<span class="tag${x === "Web" ? " web" : ""}">${esc(x)}</span>`).join("");
    const links = [
      p.demo ? `<a class="open" href="${esc(p.demo)}"${target}>Otwórz w przeglądarce</a>` : "",
      p.download ? `<a href="${esc(p.download)}"${target}>Pobierz</a>` : "",
      repo ? `<a href="${esc(repo)}"${target}>Kod źródłowy</a>` : ""
    ].join("");
    const when = CFG.ui.showUpdated && p.updated ? `<span class="when">${ago(p.updated)}</span>` : "";
    return `<li class="row${p.featured ? " featured" : ""}" data-s="${esc(hay)}">
      <span class="mark" aria-hidden="true"></span>
      <h3 class="title"><a class="primary" href="${esc(primary)}"${target} aria-label="${esc(p.name)}, ${verb}">${esc(p.name)}</a></h3>
      <div class="plat">${plats}</div>
      ${p.desc ? `<p class="desc">${esc(p.desc)}</p>` : ""}
      <div class="meta">${links}${when}</div>
    </li>`;
  }

  const state = { cat: "all", q: "" };
  function renderProjects() {
    const projects = CFG.projects.filter(p => !p.hidden);
    const cats = CFG.categories;
    $("#groups").innerHTML = cats.map(cat => {
      // Kolejność z panelu; wyróżnione zawsze na górze kategorii
      const list = projects.filter(p => p.category === cat.id).sort((a, b) => (b.featured | 0) - (a.featured | 0));
      if (!list.length) return "";
      return `<div class="group" data-cat="${esc(cat.id)}">
        <h2 class="group-head"><span class="lbl">${esc(cat.label)}</span> <span class="n"></span></h2>
        <ul class="rows">${list.map(p => rowHTML(p, cat.label)).join("")}</ul>
      </div>`;
    }).join("");
    $("#chips").innerHTML = [{ id: "all", label: "Wszystko" }, ...cats.filter(c => projects.some(p => p.category === c.id))]
      .map(c => `<button class="chip" type="button" data-cat="${esc(c.id)}" aria-pressed="false">${esc(c.label)} <span class="n"></span></button>`).join("");
    if (state.cat !== "all" && !cats.some(c => c.id === state.cat)) state.cat = "all";
    const last = projects.map(p => p.updated).filter(Boolean).sort().pop();
    const fmt = last ? new Date(last + "T00:00:00").toLocaleDateString("pl-PL", { day: "numeric", month: "long", year: "numeric" }) : "";
    $("#foot-left").textContent = `${projects.length} ${plural(projects.length, "projekt", "projekty", "projektów")}${fmt ? ", ostatnia zmiana " + fmt : ""}`;
    $("#search-wrap").hidden = !CFG.ui.search;
    filter(false);
  }

  function filter(animate) {
    const terms = fold(state.q.trim()).split(/\s+/).filter(Boolean);
    const counts = { all: 0 };
    let shown = 0, idx = 0;
    $$(".group").forEach(g => {
      const cat = g.dataset.cat;
      let n = 0;
      $$(".row", g).forEach(r => {
        const hit = terms.every(t => r.dataset.s.includes(t));
        if (hit) { counts[cat] = (counts[cat] || 0) + 1; counts.all++; }
        const show = hit && (state.cat === "all" || state.cat === cat);
        const was = !r.hidden;
        r.hidden = !show;
        if (show) {
          n++; shown++;
          if (animate && !was && !reduceMotion) { r.style.setProperty("--i", idx++); r.classList.remove("enter"); void r.offsetWidth; r.classList.add("enter"); }
        }
      });
      g.hidden = n === 0;
      $(".group-head .n", g).textContent = n;
    });
    $$(".chip").forEach(ch => {
      ch.setAttribute("aria-pressed", String(ch.dataset.cat === state.cat));
      $(".n", ch).textContent = counts[ch.dataset.cat] || 0;
    });
    $("#empty").hidden = shown > 0;
    if (!shown) $("#empty-text").textContent = state.q
      ? `Nic nie pasuje do „${state.q.trim()}”${state.cat !== "all" ? " w tej kategorii" : ""}.`
      : "Nie ma jeszcze projektów. Dodaj je w panelu administratora.";
  }

  $("#chips").addEventListener("click", e => {
    const ch = e.target.closest(".chip"); if (!ch) return;
    state.cat = ch.dataset.cat;
    try { history.replaceState(null, "", state.cat === "all" ? location.pathname + location.search : "#" + state.cat); } catch (_) {}
    filter(true);
  });
  const q = $("#q");
  q.addEventListener("input", () => { state.q = q.value; filter(true); });
  $("#clear").addEventListener("click", () => { q.value = ""; state.q = ""; state.cat = "all"; filter(true); q.focus(); });

  function fromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    state.cat = CFG.categories.some(c => c.id === h) ? h : "all";
    filter(false);
  }
  window.addEventListener("hashchange", fromHash);

  /* ===================== Klawiatura ===================== */
  document.addEventListener("keydown", e => {
    if (e.target.closest && e.target.closest(".adm")) return;
    const tag = (e.target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea" || tag === "select";
    if (e.key === "/" && !typing && CFG.ui.search) { e.preventDefault(); q.focus(); q.select(); return; }
    if (e.key === "Escape" && e.target === q && q.value) { q.value = ""; state.q = ""; filter(true); return; }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (typing && e.target !== q) return;
      const links = $$(".row:not([hidden]) .primary").filter(a => !a.closest(".group[hidden]"));
      if (!links.length) return;
      const i = links.indexOf(document.activeElement);
      let n;
      if (e.key === "ArrowDown") n = i < 0 ? 0 : Math.min(links.length - 1, i + 1);
      else { if (i <= 0) { if (i === 0 && CFG.ui.search) { e.preventDefault(); q.focus(); } return; } n = i - 1; }
      e.preventDefault();
      links[n].focus();
      links[n].closest(".row").scrollIntoView({ block: "nearest", behavior: reduceMotion ? "auto" : "smooth" });
    }
  });

  /* ===================== Złożenie całości ===================== */
  let lastConcept = "";
  function refresh(opts = {}) {
    const conceptChanged = CFG.concept !== lastConcept;
    lastConcept = CFG.concept;
    document.body.className = document.body.className.replace(/\bconcept-\S+/g, "").trim() + " concept-" + (CONCEPTS[CFG.concept] ? CFG.concept : "matryca");
    const f = applyFont();
    renderProfile();
    applyTheme();
    renderProjects();
    const intro = opts.intro || conceptChanged;
    fontReady(f, CFG.profile.handle).then(() => Matrix.rebuild(intro, f));
    if (conceptChanged || opts.intro || opts.term) Term.run(intro);
    Bg.kick();
  }

  function toast(msg, ms = 2600) {
    const t = $("#toast"); t.textContent = msg; t.classList.add("show");
    clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("show"), ms);
  }

  // Interfejs dla panelu (admin.html wczytuje tę stronę w podglądzie i steruje nią przez window.Site)
  let readyResolve;
  window.Site = {
    ready: new Promise(r => { readyResolve = r; }),
    get cfg() { return CFG; },
    setConfig(c) { CFG = withDefaults(c); refresh({ intro: true }); },
    useConfig(obj) { CFG = obj; },
    refresh, toast, PRESETS, CONCEPTS, FONTS, DEFAULTS, withDefaults,
    replayIntro() { refresh({ intro: true }); },
    setManualPreset(v) { manualPreset = v; },
    currentPresetKey
  };

  /* ===================== Start ===================== */
  Bg.init();
  fetch("config.json", { cache: "no-cache" })
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(c => { CFG = withDefaults(c); })
    .catch(() => { toast("Nie udało się wczytać config.json. Strona pokazuje ustawienia domyślne.", 5000); })
    .finally(() => {
      refresh({ intro: true });
      fromHash();
      // Poza GitHub Pages (np. w podglądzie) stopka ma skrót do panelu; na prawdziwej stronie panel jest tylko pod /admin.html
      const live = /\.github\.io$/i.test(location.hostname) || (CFG.admin.domain && location.hostname === CFG.admin.domain);
      const embedded = /[?&]embed\b/.test(location.search);
      if (!live && !embedded) { const a = $("#admin-link"); if (a) a.hidden = false; }
      readyResolve(window.Site);
    });
})();
