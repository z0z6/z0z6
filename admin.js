/* Panel administratora (admin.html). Strona jest wczytana obok w ramce podglądu i sterowana przez jej window.Site.
   Zapis: GitHub API zapisuje config.json w repozytorium strony (token z prawem Contents: Read and write).
   Token zostaje tylko w przeglądarce administratora, nigdy w plikach strony. */
(() => {
  "use strict";
  let Site = null;          // interfejs strony z ramki podglądu
  let CFG = null, saved = ""; // edytowane ustawienia i ostatnio zapisana wersja
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cfg = () => CFG;
  function toast(msg, ms = 2600) {
    const t = $("#toast"); t.textContent = msg; t.classList.add("show");
    clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("show"), ms);
  }
  function setCfg(obj) { CFG = Site.withDefaults(obj); Site.useConfig(CFG); Site.refresh({ intro: true }); }
  const TOKEN_KEY = "portfolio-admin-token";
  const PLATFORMS = ["Android", "Windows", "Linux", "macOS", "iOS", "Web", "VR"];

  const I = {
    star: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3.5l2.6 5.3 5.9.9-4.25 4.1 1 5.8L12 16.9l-5.25 2.7 1-5.8L3.5 9.7l5.9-.9z"/></svg>',
    starOn: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3.5l2.6 5.3 5.9.9-4.25 4.1 1 5.8L12 16.9l-5.25 2.7 1-5.8L3.5 9.7l5.9-.9z"/></svg>',
    eye: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M2.5 12s3.5-6.5 9.5-6.5S21.5 12 21.5 12s-3.5 6.5-9.5 6.5S2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/></svg>',
    eyeOff: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l18 18M10.6 5.6A9.6 9.6 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a16 16 0 0 1-2.9 3.6M6.2 6.9C3.9 8.6 2.5 12 2.5 12s3.5 6.5 9.5 6.5a9 9 0 0 0 4.4-1.1"/></svg>',
    up: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14l6-6 6 6"/></svg>',
    down: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 10l6 6 6-6"/></svg>',
    trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    min: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12h14"/></svg>',
    max: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>',
    grip: '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="9" cy="6" r="1.6"/><circle cx="15" cy="6" r="1.6"/><circle cx="9" cy="12" r="1.6"/><circle cx="15" cy="12" r="1.6"/><circle cx="9" cy="18" r="1.6"/><circle cx="15" cy="18" r="1.6"/></svg>'
  };

  /* ===================== Stan ===================== */
  let token = null, user = null, mode = null, sha = null, saving = false;
  let tab = "projekty", openRef = null, confirmRef = null;
  let imp = null; // { loading, error, repos, cat, picked:Set }

  const store = {
    get() { try { return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY); } catch (_) { return null; } },
    set(t, remember) { try { (remember ? localStorage : sessionStorage).setItem(TOKEN_KEY, t); } catch (_) {} },
    clear() { try { localStorage.removeItem(TOKEN_KEY); sessionStorage.removeItem(TOKEN_KEY); } catch (_) {} }
  };
  const onLive = () => /\.github\.io$/i.test(location.hostname) || (cfg().admin.domain && location.hostname === cfg().admin.domain);
  const dirty = () => JSON.stringify(cfg()) !== saved;
  const today = () => new Date().toISOString().slice(0, 10);
  const fold = s => String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l");
  const slug = s => fold(s).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "kategoria";

  /* ===================== GitHub API ===================== */
  async function api(path, opts = {}) {
    const headers = { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
    if (token) headers.Authorization = "Bearer " + token;
    if (opts.body) headers["Content-Type"] = "application/json";
    const r = await fetch("https://api.github.com" + path, Object.assign({}, opts, { headers, cache: "no-store" }));
    if (!r.ok) {
      const e = new Error("HTTP " + r.status); e.status = r.status;
      try { e.body = await r.json(); } catch (_) {}
      throw e;
    }
    return r.status === 204 ? null : r.json();
  }
  function errText(e) {
    if (!e) return "Coś poszło nie tak.";
    if (e instanceof TypeError || !e.status) return e.message && !/fetch|network|load/i.test(e.message) ? e.message : "Brak połączenia z GitHubem. Sprawdź internet, a w podglądzie użyj trybu próbnego.";
    if (e.status === 401) return "Token jest nieprawidłowy albo wygasł. Zaloguj się ponownie nowym tokenem.";
    if (e.status === 403) return "GitHub odmówił dostępu: brak uprawnień albo przekroczony limit zapytań. Spróbuj za kilka minut.";
    if (e.status === 404) return "Nie znaleziono repozytorium albo pliku. Sprawdź ustawienia w zakładce Publikacja.";
    if (e.status === 409 || e.status === 422) return "Plik zmienił się w międzyczasie. Zapisz jeszcze raz.";
    return (e.body && e.body.message) || e.message;
  }
  const b64enc = s => { const b = new TextEncoder().encode(s); let bin = ""; for (let i = 0; i < b.length; i += 0x8000) bin += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000)); return btoa(bin); };
  const b64dec = s => new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\s/g, "")), c => c.charCodeAt(0)));
  const contentPath = () => { const a = cfg().admin; return `/repos/${a.owner}/${a.repo}/contents/${a.path.split("/").map(encodeURIComponent).join("/")}`; };

  async function login(t) {
    token = t;
    const u = await api("/user");
    const a = cfg().admin;
    let repo;
    try { repo = await api(`/repos/${a.owner}/${a.repo}`); }
    catch (e) {
      if (e.status === 404) throw new Error(`Nie widzę repozytorium ${a.owner}/${a.repo}. Sprawdź, czy istnieje i czy token ma do niego dostęp.`);
      throw e;
    }
    if (!repo.permissions || !repo.permissions.push) throw new Error("Ten token nie może zapisywać w repozytorium. Nadaj mu uprawnienie Contents: Read and write.");
    user = u.login; mode = "github";
    await pull(true);
  }
  async function pull(apply) {
    try {
      const f = await api(contentPath() + "?ref=" + encodeURIComponent(cfg().admin.branch));
      sha = f.sha;
      if (apply && f.content) {
        const remote = JSON.parse(b64dec(f.content));
        if (JSON.stringify(Site.withDefaults(remote)) !== JSON.stringify(cfg())) setCfg(remote);
        saved = JSON.stringify(cfg());
      }
    } catch (e) { if (e.status === 404) sha = null; else throw e; }
  }
  async function save() {
    if (saving) return;
    if (mode !== "github") {
      toast("W trybie próbnym nic nie trafia na GitHuba. Skopiuj config.json poniżej.", 4000);
      tab = "publikacja"; render(); return;
    }
    saving = true; renderFoot();
    try {
      await pull(false);
      const a = cfg().admin;
      const body = { message: ($("#a-msg") && $("#a-msg").value.trim()) || "Aktualizacja strony", content: b64enc(JSON.stringify(cfg(), null, 2) + "\n"), branch: a.branch };
      if (sha) body.sha = sha;
      const r = await api(contentPath(), { method: "PUT", body: JSON.stringify(body) });
      sha = r.content && r.content.sha;
      saved = JSON.stringify(cfg());
      toast("Opublikowano. Strona odświeży się w ciągu około minuty.", 4000);
    } catch (e) { toast(errText(e), 6000); }
    finally { saving = false; renderFoot(); }
  }

  /* ===================== Logowanie ===================== */
  const loginEl = $("#login");
  function showLogin(errMsg) {
    $("#app").hidden = true;
    loginEl.hidden = false;
    const a = cfg().admin;
    loginEl.innerHTML = `<form class="box" novalidate>
      <h1>Panel strony</h1>
      <p>Zaloguj się tokenem GitHub z prawem zapisu do repozytorium <b>${esc(a.owner)}/${esc(a.repo)}</b>. Token zostaje tylko w tej przeglądarce.</p>
      <label class="f"><span>Token GitHub</span><input class="in" id="al-token" type="password" autocomplete="off" spellcheck="false" placeholder="github_pat_..."></label>
      <label class="sw"><span>Zapamiętaj na tym urządzeniu</span><input type="checkbox" id="al-rem"></label>
      <p class="err" id="al-err" ${errMsg ? "" : "hidden"}>${esc(errMsg || "")}</p>
      <div class="row-btns"><button class="b pri" type="submit" id="al-go">Zaloguj</button></div>
      <details><summary>Jak zdobyć token</summary><ol>
        <li>Otwórz <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">github.com/settings/personal-access-tokens/new</a>.</li>
        <li>W „Repository access” wybierz „Only select repositories” i zaznacz <b>${esc(a.repo)}</b>.</li>
        <li>W „Permissions” ustaw „Contents” na „Read and write”.</li>
        <li>Kliknij „Generate token” i wklej go powyżej.</li>
      </ol></details>
      ${onLive() ? "" : `<div class="or">albo</div>
      <button class="b" type="button" id="al-demo">Wypróbuj panel bez logowania</button>
      <p class="a-note">W trybie próbnym zmiany widzisz od razu w podglądzie, ale zostają tylko w tej karcie. Na koniec możesz skopiować gotowy config.json.</p>`}
      <a class="back" href="index.html">Wróć na stronę</a>
    </form>`;
    const form = $("form", loginEl), err = $("#al-err", loginEl), go = $("#al-go", loginEl);
    setTimeout(() => $("#al-token", loginEl).focus(), 30);
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const t = $("#al-token", loginEl).value.trim();
      if (!t) { err.hidden = false; err.textContent = "Wklej token, żeby się zalogować."; return; }
      go.disabled = true; go.textContent = "Sprawdzam...";
      try {
        await login(t);
        store.set(t, $("#al-rem", loginEl).checked);
        showApp();
        toast("Zalogowano jako " + user);
      } catch (ex) {
        token = null; mode = null;
        err.hidden = false; err.textContent = ex.status || ex instanceof TypeError ? errText(ex) : ex.message;
        go.disabled = false; go.textContent = "Zaloguj";
      }
    });
    const demo = $("#al-demo", loginEl);
    if (demo) demo.addEventListener("click", () => { mode = "demo"; user = null; showApp(); });
  }

  async function start() {
    const t = store.get();
    if (t) {
      loginEl.innerHTML = '<div class="box"><p class="a-note">Łączę z GitHubem...</p></div>';
      try { await login(t); showApp(); return; }
      catch (e) { token = null; store.clear(); showLogin(e.status || e instanceof TypeError ? errText(e) : e.message); return; }
    }
    showLogin();
  }

  /* ===================== Panel i podgląd ===================== */
  const drawer = $("#panel");
  let bound = false;
  function showApp() {
    loginEl.hidden = true;
    $("#app").hidden = false;
    if (!bound) {
      bound = true;
      drawer.addEventListener("click", onClick);
      drawer.addEventListener("input", onInput);
      drawer.addEventListener("change", onChange);
      drawer.addEventListener("keydown", onKey);
      drawer.addEventListener("pointerdown", e => { const g = e.target.closest(".grip"); if (g) g.closest(".it").draggable = true; });
      drawer.addEventListener("dragstart", onDragStart);
      drawer.addEventListener("dragover", onDragOver);
      drawer.addEventListener("dragleave", e => { const it = e.target.closest(".it"); if (it) it.classList.remove("over-top", "over-bot"); });
      drawer.addEventListener("drop", onDrop);
      drawer.addEventListener("dragend", () => { $$(".it", drawer).forEach(x => { x.classList.remove("drag", "over-top", "over-bot"); x.draggable = false; }); });
    }
    render();
  }

  // Przełącznik komputer / telefon i odświeżanie podglądu
  $("#device").addEventListener("click", e => {
    const b = e.target.closest("[data-dev]"); if (!b) return;
    $$("#device button").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    $("#stage").classList.toggle("mobile", b.dataset.dev === "mobile");
  });
  $("#reload").addEventListener("click", () => { $("#frame").contentWindow.location.reload(); });
  $$('#preview [data-act="preview"]').forEach(b => b.addEventListener("click", () => $("#app").classList.remove("show-preview")));

  // Ramka podglądu: przy każdym wczytaniu podłączamy ją do edytowanych ustawień
  const frame = $("#frame");
  let firstLoad = true;
  function attach() {
    let w;
    try { w = frame.contentWindow; if (!w.Site) return; } catch (_) { loginEl.innerHTML = '<div class="box"><p class="err">Podgląd nie daje się podłączyć. Otwórz admin.html z tego samego adresu co stronę.</p></div>'; return; }
    w.Site.ready.then(site => {
      Site = site;
      if (CFG) { Site.useConfig(CFG); Site.refresh({ intro: true }); }
      else { CFG = Site.withDefaults(Site.cfg); saved = JSON.stringify(CFG); Site.useConfig(CFG); }
      if (firstLoad) { firstLoad = false; start(); }
    });
  }
  frame.addEventListener("load", attach);
  if (frame.contentDocument && frame.contentDocument.readyState === "complete" && frame.contentWindow.Site) attach();

  /* ===================== Renderowanie ===================== */
  function render() {
    if (!CFG) return;
    $("#a-who", drawer).textContent = mode === "github" ? "Zalogowano jako " + user : "Tryb próbny";
    $$(".a-tabs [data-tab]", drawer).forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
    const body = $("#a-body", drawer);
    const st = body.scrollTop;
    body.innerHTML = ({ projekty: tabProjects, profil: tabProfile, wyglad: tabLook, publikacja: tabPublish })[tab]();
    body.scrollTop = st;
    renderFoot();
  }
  function renderFoot() {
    if (!CFG) return;
    const d = dirty();
    const s = $("#a-status", drawer);
    s.classList.toggle("dirty", d);
    $("#a-st", drawer).textContent = mode === "github" ? (d ? "Masz niezapisane zmiany" : "Wszystko zapisane") : (d ? "Zmiany tylko w tej karcie" : "Brak zmian");
    const b = $("#a-save", drawer);
    b.disabled = saving || (mode === "github" && !d);
    b.textContent = saving ? "Zapisuję..." : mode === "github" ? "Zapisz i opublikuj" : "Pobierz ustawienia";
  }

  const field = (label, inner, hint) => `<label class="f"><span>${label}</span>${inner}${hint ? `<small>${hint}</small>` : ""}</label>`;
  const inp = (path, val, extra = "") => `<input class="in" data-bind="${path}" value="${esc(val)}" ${extra}>`;
  const sw = (label, path, val) => `<label class="sw"><span>${label}</span><input type="checkbox" data-bind="${path}" ${val ? "checked" : ""}></label>`;
  const seg = (path, cur, opts, extra = "") => `<div class="seg">${opts.map(([v, l]) => `<button type="button" data-act="set" data-path="${path}" data-v="${esc(v)}" ${extra} aria-pressed="${String(cur) === String(v)}">${l}</button>`).join("")}</div>`;
  const counter = (len, max) => `<span class="count${len > max ? " over" : ""}" data-max="${max}">${len} / ${max}</span>`;

  /* ---------- Projekty ---------- */
  function tabProjects() {
    const c = cfg();
    const cats = c.categories;
    const known = new Set(cats.map(x => x.id));
    const groups = cats.map(cat => ({ id: cat.id, label: cat.label, items: c.projects.map((p, i) => ({ p, i })).filter(x => x.p.category === cat.id) }));
    const orphans = c.projects.map((p, i) => ({ p, i })).filter(x => !known.has(x.p.category));
    if (orphans.length) groups.push({ id: "", label: "Bez kategorii", items: orphans });

    return `
    <section class="a-sec">
      <h3>Projekty <span class="row-btns"><button class="b sm" type="button" data-act="import">Importuj z GitHuba</button><button class="b sm pri" type="button" data-act="add-project">Dodaj</button></span></h3>
      ${imp ? importBox() : ""}
      <p class="a-note">Przeciągnij za uchwyt albo użyj strzałek, żeby zmienić kolejność. Gwiazdka wyróżnia projekt, oko ukrywa go na stronie.</p>
      <div class="ilist">
        ${groups.map(g => `<div class="ihead" data-cat="${esc(g.id)}"><span>${esc(g.label)}</span><span>${g.items.length}</span></div>
          ${g.items.map(({ p, i }) => itemHTML(p, i)).join("") || `<p class="a-note" data-cat="${esc(g.id)}">Pusto. Przeciągnij tu projekt.</p>`}`).join("")}
      </div>
    </section>
    <section class="a-sec">
      <h3>Kategorie <button class="b sm" type="button" data-act="add-cat">Dodaj kategorię</button></h3>
      <div class="ilist">${cats.map((cat, i) => `<div class="mini cat">
        <input class="in" data-bind="categories.${i}.label" value="${esc(cat.label)}" aria-label="Nazwa kategorii">
        <span class="acts">
          <button class="tg" type="button" data-act="cat-up" data-i="${i}" aria-label="Przesuń wyżej" ${i === 0 ? "disabled" : ""}>${I.up}</button>
          <button class="tg" type="button" data-act="cat-down" data-i="${i}" aria-label="Przesuń niżej" ${i === cats.length - 1 ? "disabled" : ""}>${I.down}</button>
          <button class="tg" type="button" data-act="cat-del" data-i="${i}" aria-label="Usuń kategorię">${I.trash}</button>
        </span></div>`).join("")}</div>
    </section>
    <section class="a-sec">
      <h3>Porządki</h3>
      <div class="row-btns">
        <button class="b sm" type="button" data-act="sort-date">Sortuj według daty zmiany</button>
        <button class="b sm" type="button" data-act="sync-dates">Pobierz daty zmian z GitHuba</button>
      </div>
    </section>`;
  }
  function itemHTML(p, i) {
    const open = openRef === p;
    const meta = [p.repo ? "repo: " + p.repo : "bez repozytorium", (p.platforms || []).join(", ")].filter(Boolean).join(", ");
    return `<div class="it${p.hidden ? " off" : ""}" data-i="${i}">
      <div class="it-row">
        <span class="grip" title="Przeciągnij">${I.grip}</span>
        <button class="it-name" type="button" data-act="edit" data-i="${i}" aria-expanded="${open}"><b>${esc(p.name || "Bez nazwy")}</b><small>${esc(meta)}</small></button>
        <button class="tg${p.featured ? " on" : ""}" type="button" data-act="feat" data-i="${i}" aria-pressed="${!!p.featured}" aria-label="Wyróżnij">${p.featured ? I.starOn : I.star}</button>
        <button class="tg${p.hidden ? " on" : ""}" type="button" data-act="hide" data-i="${i}" aria-pressed="${!!p.hidden}" aria-label="${p.hidden ? "Pokaż na stronie" : "Ukryj na stronie"}">${p.hidden ? I.eyeOff : I.eye}</button>
        <button class="tg" type="button" data-act="up" data-i="${i}" aria-label="Przesuń wyżej">${I.up}</button>
        <button class="tg" type="button" data-act="down" data-i="${i}" aria-label="Przesuń niżej">${I.down}</button>
      </div>
      ${open ? editHTML(p, i) : ""}
    </div>`;
  }
  function editHTML(p, i) {
    const c = cfg();
    const pre = `projects.${i}`;
    const plats = Array.from(new Set([...PLATFORMS, ...(p.platforms || [])]));
    const del = confirmRef === p
      ? `<div class="confirm"><span>Usunąć „${esc(p.name)}” ze strony? Repozytorium zostaje.</span><button class="b sm dng" type="button" data-act="del-yes" data-i="${i}">Usuń</button><button class="b sm" type="button" data-act="del-no">Anuluj</button></div>`
      : `<div class="row-btns"><button class="b sm dng" type="button" data-act="del" data-i="${i}">${I.trash} Usuń projekt</button></div>`;
    return `<div class="it-edit">
      ${field("Nazwa", inp(pre + ".name", p.name, 'data-live="name"'))}
      <div class="f2">
        ${field("Repozytorium", inp(pre + ".repo", p.repo || "", 'placeholder="nazwa-repo"'), "Nazwa lub pełny adres")}
        ${field("Kategoria", `<select data-bind="${pre}.category" data-rerender="1">${c.categories.map(x => `<option value="${esc(x.id)}" ${x.id === p.category ? "selected" : ""}>${esc(x.label)}</option>`).join("")}</select>`)}
      </div>
      ${field("Adres działającej wersji", inp(pre + ".demo", p.demo || "", 'type="url" placeholder="https://..."'), "Pojawi się przycisk „Otwórz w przeglądarce”")}
      ${field("Link do pobrania", inp(pre + ".download", p.download || "", 'type="url" placeholder="https://github.com/.../releases"'))}
      <label class="f"><span>Opis</span><textarea data-bind="${pre}.desc" data-count="140">${esc(p.desc || "")}</textarea>${counter((p.desc || "").length, 140)}</label>
      <div class="f"><span>Platformy</span>
        <div class="plats">${plats.map(x => `<button type="button" data-act="plat" data-i="${i}" data-v="${esc(x)}" aria-pressed="${(p.platforms || []).includes(x)}">${esc(x)}</button>`).join("")}</div>
        <input class="in" data-act-enter="add-plat" data-i="${i}" placeholder="Inna platforma i Enter">
      </div>
      <div class="f2">
        ${field("Data zmiany", inp(pre + ".updated", p.updated || "", 'type="date"'))}
        ${field("Słowa dla wyszukiwarki", inp(pre + ".tags", (p.tags || []).join(", "), 'data-type="list" placeholder="kotlin, ai"'))}
      </div>
      ${del}
    </div>`;
  }
  function importBox() {
    if (imp.loading) return `<p class="a-note">Pobieram listę repozytoriów...</p>`;
    if (imp.error) return `<div class="confirm"><span>${esc(imp.error)}</span><button class="b sm" type="button" data-act="import-close">Zamknij</button></div>`;
    const c = cfg();
    const have = new Set(c.projects.map(p => String(p.repo || "").toLowerCase()));
    const list = imp.repos.filter(r => !have.has(r.name.toLowerCase()) && r.name.toLowerCase() !== (c.admin.repo || "").toLowerCase());
    if (!list.length) return `<div class="confirm" style="background:color-mix(in srgb,var(--accent) 10%,transparent)"><span>Wszystkie publiczne repozytoria są już na stronie.</span><button class="b sm" type="button" data-act="import-close">Zamknij</button></div>`;
    return `<div class="a-sec">
      <div class="imp">${list.map(r => `<label><input type="checkbox" data-imp="${esc(r.name)}" ${imp.picked.has(r.name) ? "checked" : ""}>
        <span><b>${esc(r.name)}</b>${r.fork ? ' <span class="badge">fork</span>' : ""}${r.has_pages ? ' <span class="badge">ma stronę</span>' : ""}
        <small>${esc(r.description || "Bez opisu")}</small><small>${esc([r.language, r.pushed_at && "zmiana " + r.pushed_at.slice(0, 10)].filter(Boolean).join(", "))}</small></span></label>`).join("")}</div>
      <div class="f2">
        <label class="f"><span>Dodaj do kategorii</span><select data-imp-cat>${c.categories.map(x => `<option value="${esc(x.id)}" ${x.id === imp.cat ? "selected" : ""}>${esc(x.label)}</option>`).join("")}</select></label>
        <div class="f"><span>&nbsp;</span><div class="row-btns"><button class="b pri" type="button" data-act="import-add" ${imp.picked.size ? "" : "disabled"}>Dodaj zaznaczone (${imp.picked.size})</button><button class="b" type="button" data-act="import-close">Zamknij</button></div></div>
      </div>
    </div>`;
  }

  /* ---------- Profil ---------- */
  function tabProfile() {
    const p = cfg().profile;
    return `
    <section class="a-sec">
      <h3>Profil</h3>
      ${field("Napis w nagłówku", inp("profile.handle", p.handle, 'data-intro="1"'), "Rysowany z kropek, wielkimi literami albo wpisywany w terminalu, zależnie od koncepcji.")}
      ${field("Tytuł karty przeglądarki", inp("profile.name", p.name))}
      <label class="f"><span>Opis</span><textarea data-bind="profile.bio" data-count="220">${esc(p.bio)}</textarea>${counter((p.bio || "").length, 220)}</label>
      <div class="f"><span>Zdjęcie profilowe</span>
        <div class="avatar-row">
          <span class="av">${p.avatar ? `<img alt="" src="${esc(p.avatar)}">` : ""}</span>
          <span class="row-btns">
            <label class="b sm">Wgraj zdjęcie<input type="file" accept="image/*" id="a-avatar" hidden></label>
            ${p.avatar ? `<button class="b sm" type="button" data-act="avatar-del">Usuń</button>` : ""}
          </span>
        </div>
        <small>Widoczne w koncepcji Linktree. Bez zdjęcia pokazuje się wzór z kropek wyliczony z napisu.</small>
      </div>
    </section>
    <section class="a-sec">
      <h3>Linki <button class="b sm" type="button" data-act="add-link">Dodaj link</button></h3>
      <div class="ilist">${(p.links || []).map((l, i) => `<div class="mini">
        <input class="in" data-bind="profile.links.${i}.label" value="${esc(l.label)}" placeholder="Nazwa" aria-label="Nazwa linku">
        <input class="in" data-bind="profile.links.${i}.url" value="${esc(l.url)}" placeholder="https://..." aria-label="Adres linku">
        <span class="acts">
          <button class="tg" type="button" data-act="link-up" data-i="${i}" aria-label="Przesuń wyżej" ${i === 0 ? "disabled" : ""}>${I.up}</button>
          <button class="tg" type="button" data-act="link-del" data-i="${i}" aria-label="Usuń link">${I.trash}</button>
        </span></div>`).join("") || `<p class="a-note">Brak linków.</p>`}</div>
      <p class="a-note">Adres e-mail wpisz jako mailto:ty@example.com, wtedy na stronie pokaże się sam adres.</p>
    </section>`;
  }

  /* ---------- Wygląd ---------- */
  const PREVIEW = {
    matryca: '<i class="dots" style="left:8px;top:8px;width:58px;height:18px"></i><i class="mu" style="left:8px;top:32px;width:80%;height:7px"></i><i class="mu" style="left:8px;top:43px;width:80%;height:7px"></i><i class="ac" style="left:8px;top:33px;width:5px;height:5px;border-radius:50%"></i>',
    kafle: '<i style="left:8px;top:6px;width:20px;height:16px"></i><i class="ac" style="left:30px;top:6px;width:20px;height:16px"></i><i style="left:52px;top:6px;width:20px;height:16px"></i><i class="mu" style="left:8px;top:28px;width:calc(100% - 16px);height:12px"></i><i class="mu" style="left:8px;top:43px;width:calc(50% - 10px);height:12px"></i><i class="mu" style="left:calc(50% + 2px);top:43px;width:calc(50% - 10px);height:12px"></i>',
    terminal: '<i class="ac" style="left:8px;top:9px;width:22px;height:4px"></i><i style="left:33px;top:9px;width:26px;height:4px"></i><i style="left:8px;top:18px;width:34px;height:8px"></i><i class="ac" style="left:8px;top:32px;width:22px;height:4px"></i><i class="mu" style="left:8px;top:42px;width:70%;height:4px"></i><i class="mu" style="left:8px;top:50px;width:55%;height:4px"></i>',
    indeks: '<i class="mu" style="left:8px;top:7px;width:70%;height:9px"></i><i style="left:8px;top:22px;width:62%;height:9px"></i><i class="ac" style="left:8px;top:35px;width:48%;height:9px"></i><i style="left:8px;top:48px;width:56%;height:9px"></i>',
    klasyk: '<i class="ac" style="left:calc(50% - 8px);top:5px;width:16px;height:16px;border-radius:50%"></i><i style="left:20%;top:26px;width:60%;height:8px;border-radius:4px"></i><i class="mu" style="left:20%;top:38px;width:60%;height:8px;border-radius:4px"></i><i class="mu" style="left:20%;top:50px;width:60%;height:8px;border-radius:4px"></i>'
  };
  function tabLook() {
    const c = cfg(), t = c.theme, m = c.matrix, b = c.background, u = c.ui;
    const cur = t.preset;
    const P = Site.PRESETS;
    const sws = [["auto", "Auto", "auto"], ...Object.entries(P).map(([k, p]) => [k, p.label, ""]), ["wlasny", "Własny", "custom"]];
    const accentVal = t.accent || (t.preset === "wlasny" ? t.custom.accent : (P[Site.currentPresetKey()] || P.mgla).accent);
    const fonts = Object.keys(Site.FONTS);
    return `
    <section class="a-sec">
      <h3>Koncepcja</h3>
      <div class="concepts">${Object.entries(Site.CONCEPTS).map(([k, x]) => `<button class="cc" type="button" data-act="concept" data-v="${k}" aria-pressed="${c.concept === k}">
        <span class="pv">${PREVIEW[k] || ""}</span><b>${esc(x.label)}</b><small>${esc(x.desc)}</small></button>`).join("")}</div>
      <p class="a-note">Koncepcja ustawia też pasującą czcionkę i tło. Możesz je potem zmienić niżej.</p>
    </section>
    <section class="a-sec">
      <h3>Motyw kolorystyczny</h3>
      <div class="themes">${sws.map(([k, l, cls]) => {
        const p = P[k];
        const style = p ? `style="--sw-bg:${p.bg};--sw-ink:${p.ink};--sw-mu:${p.line};--sw-ac:${p.accent}"` : "";
        return `<button class="th" type="button" data-act="preset" data-v="${k}" aria-pressed="${cur === k}"><span class="s ${cls}" ${style}></span>${l}</button>`;
      }).join("")}</div>
      <p class="a-note">Auto przełącza Mgłę i Noc według ustawień systemu odwiedzającego. Przycisk ze słońcem na stronie przełącza na motyw do pary.</p>
      ${t.preset === "wlasny" ? `<div class="colors">${[["bg", "Tło"], ["surface", "Wiersze"], ["ink", "Tekst"], ["muted", "Tekst drugi"], ["line", "Linie"], ["accent", "Akcent"]].map(([k, l]) => `<label><input type="color" data-bind="theme.custom.${k}" value="${esc(t.custom[k])}">${l}</label>`).join("")}</div>` : ""}
      <div class="f"><span>Kolor akcentu</span><div class="row-btns"><input type="color" data-bind="theme.accent" value="${esc(accentVal)}" aria-label="Kolor akcentu"><button class="b sm" type="button" data-act="accent-reset" ${t.accent ? "" : "disabled"}>Wróć do koloru motywu</button></div></div>
    </section>
    <section class="a-sec">
      <h3>Typografia i układ</h3>
      <div class="f2">
        ${field("Czcionka", `<select data-bind="theme.font" data-rerender="1">${fonts.map(f => `<option ${f === t.font ? "selected" : ""}>${esc(f)}</option>`).join("")}${fonts.includes(t.font) ? "" : `<option selected>${esc(t.font)}</option>`}</select>`)}
        ${field("Inna z Google Fonts", `<input class="in" data-bind="theme.font" value="${esc(t.font)}" data-lazy="1" placeholder="np. Manrope">`)}
      </div>
      ${field("Zaokrąglenie rogów", `<input type="range" min="0" max="24" step="1" data-bind="theme.radius" value="${t.radius}">`)}
      <div class="f"><span>Lista projektów</span>${seg("theme.density", t.density, [["comfortable", "Z opisami"], ["compact", "Zwarta"]])}</div>
    </section>
    <section class="a-sec">
      <h3>Nagłówek z kropek ${c.concept === "matryca" ? "" : '<span class="badge">tylko Matryca</span>'}</h3>
      <div class="f"><span>Kształt kropek (też w tle)</span>${seg("matrix.shape", m.shape, [["circle", "Koło"], ["square", "Kwadrat"], ["plus", "Plus"]])}</div>
      ${field("Gęstość kropek", `<input type="range" min="6" max="14" step="1" data-bind="matrix.cell" value="${m.cell}">`, "W lewo gęściej, w prawo grubiej.")}
      <div class="f"><span>Reakcja na kursor</span>${seg("matrix.cursor", m.cursor, [["repel", "Odpycha"], ["attract", "Przyciąga"], ["none", "Brak"]])}</div>
      <div class="f"><span>Animacja wejścia</span>${seg("matrix.intro", m.intro, [["assemble", "Zlot"], ["scan", "Skan"], ["none", "Brak"]], 'data-intro="1"')}</div>
      <div class="row-btns"><button class="b sm" type="button" data-act="replay">Powtórz animację</button></div>
    </section>
    <section class="a-sec">
      <h3>Tło strony</h3>
      <div class="f"><span>Styl</span>${seg("background.style", b.enabled ? b.style : "none", [["fala", "Fala"], ["przeplyw", "Przepływ"], ["deszcz", "Deszcz"], ["none", "Brak"]])}</div>
      <div class="f2">
        ${field("Siła", `<input type="range" min="0.1" max="1" step="0.05" data-bind="background.intensity" value="${b.intensity}">`)}
        ${field("Tempo", `<input type="range" min="0.2" max="2" step="0.1" data-bind="background.speed" value="${b.speed}">`)}
      </div>
      ${field("Odstęp kropek", `<input type="range" min="14" max="40" step="1" data-bind="background.spacing" value="${b.spacing}">`)}
      ${sw("Poświata pod kursorem", "background.cursor", b.cursor)}
      ${sw("Fala po kliknięciu", "background.ripples", b.ripples)}
    </section>
    <section class="a-sec">
      <h3>Zachowanie</h3>
      ${sw("Wyszukiwarka projektów", "ui.search", u.search)}
      ${sw("Daty zmian przy projektach", "ui.showUpdated", u.showUpdated)}
      ${sw("Linki w nowej karcie", "ui.newTab", u.newTab)}
    </section>`;
  }

  /* ---------- Publikacja ---------- */
  function tabPublish() {
    const a = cfg().admin;
    return `
    <section class="a-sec">
      <h3>Publikacja</h3>
      <p class="a-note">${mode === "github"
        ? `Zapis trafia do pliku <b>${esc(a.path)}</b> w repozytorium <b>${esc(a.owner)}/${esc(a.repo)}</b> (gałąź ${esc(a.branch)}). GitHub Pages odświeża stronę w około minutę.`
        : "Tryb próbny: zmiany widzisz tylko w tej karcie. Żeby je zachować, skopiuj config.json niżej albo zaloguj się tokenem."}</p>
      ${mode === "github" ? `${field("Opis zmiany", `<input class="in" id="a-msg" placeholder="Aktualizacja strony">`)}
      <div class="row-btns"><button class="b pri" type="button" data-act="save">Zapisz i opublikuj</button><button class="b" type="button" data-act="discard">Odrzuć niezapisane zmiany</button></div>`
      : `<div class="row-btns"><button class="b pri" type="button" data-act="relogin">Zaloguj tokenem</button><button class="b" type="button" data-act="discard">Cofnij wszystkie zmiany</button></div>`}
    </section>
    <section class="a-sec">
      <h3>Repozytorium strony</h3>
      <div class="f2">
        ${field("Właściciel", inp("admin.owner", a.owner))}
        ${field("Repozytorium", inp("admin.repo", a.repo))}
        ${field("Gałąź", inp("admin.branch", a.branch))}
        ${field("Plik", inp("admin.path", a.path))}
      </div>
      ${field("Własna domena (opcjonalnie)", inp("admin.domain", a.domain || "", 'placeholder="z0z6.is-a.dev"'), "Na tej domenie przycisk trybu próbnego jest ukryty.")}
      <p class="a-note">Panel jest zawsze pod adresem strony z dopiskiem /admin.html, np. https://${esc(a.owner)}.github.io/admin.html. Na stronie nie ma do niego przycisku.</p>
    </section>
    <section class="a-sec">
      <h3>config.json</h3>
      <textarea class="code" id="a-json" readonly>${esc(JSON.stringify(cfg(), null, 2))}</textarea>
      <div class="row-btns"><button class="b sm" type="button" data-act="copy-json">Kopiuj</button><button class="b sm" type="button" data-act="refresh-json">Odśwież</button>
        <label class="b sm">Wczytaj z pliku<input type="file" accept=".json,application/json" id="a-load" hidden></label></div>
    </section>
    ${mode === "github" ? `<section class="a-sec"><h3>Sesja</h3><div class="row-btns"><button class="b dng" type="button" data-act="logout">Wyloguj</button></div><p class="a-note">Wylogowanie usuwa token z tej przeglądarki.</p></section>` : ""}`;
  }

  /* ===================== Zdarzenia ===================== */
  let refreshTimer = 0, pendingOpts = {};
  function liveRefresh(opts = {}, delay = 180) {
    Object.assign(pendingOpts, opts);
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => { Site.refresh(pendingOpts); pendingOpts = {}; renderFoot(); }, delay);
    renderFoot();
  }
  function setPath(obj, path, v) {
    const ks = path.split(".");
    let o = obj;
    for (let i = 0; i < ks.length - 1; i++) { if (o[ks[i]] == null) o[ks[i]] = {}; o = o[ks[i]]; }
    o[ks[ks.length - 1]] = v;
  }

  function onInput(e) {
    const el = e.target;
    if (!el.dataset.bind || el.tagName === "SELECT") return;
    let v;
    if (el.type === "checkbox") v = el.checked;
    else if (el.type === "range") v = +el.value;
    else if (el.dataset.type === "list") v = el.value.split(",").map(s => s.trim()).filter(Boolean);
    else v = el.value;
    if (el.dataset.lazy && !String(v).trim()) return;
    setPath(cfg(), el.dataset.bind, v);
    if (el.dataset.count) {
      const c = el.parentElement.querySelector(".count"), max = +el.dataset.count;
      if (c) { c.textContent = `${el.value.length} / ${max}`; c.classList.toggle("over", el.value.length > max); }
    }
    if (el.dataset.live === "name") { const b = el.closest(".it").querySelector(".it-name b"); if (b) b.textContent = el.value || "Bez nazwy"; }
    if (el.dataset.bind === "theme.accent") { const r = $('[data-act="accent-reset"]', drawer); if (r) r.disabled = false; }
    const profileField = el.dataset.bind.startsWith("profile.");
    liveRefresh({ term: profileField, intro: !!el.dataset.intro }, el.type === "range" || el.type === "color" ? 60 : 220);
  }
  function onChange(e) {
    const el = e.target;
    if (el.tagName === "SELECT" && el.dataset.bind) {
      setPath(cfg(), el.dataset.bind, el.value);
      Site.refresh({ term: true }); render(); return;
    }
    if (el.matches("[data-imp]")) { el.checked ? imp.picked.add(el.dataset.imp) : imp.picked.delete(el.dataset.imp); render(); return; }
    if (el.matches("[data-imp-cat]")) { imp.cat = el.value; return; }
    if (el.id === "a-avatar" && el.files[0]) { loadAvatar(el.files[0]); return; }
    if (el.id === "a-load" && el.files[0]) {
      el.files[0].text().then(txt => {
        try { const obj = JSON.parse(txt); setCfg(obj); render(); toast("Wczytano ustawienia z pliku. Zapisz, żeby je opublikować."); }
        catch (_) { toast("To nie jest poprawny plik JSON.", 4000); }
      });
    }
  }
  function onKey(e) {
    const el = e.target;
    if (e.key === "Enter" && el.dataset.actEnter === "add-plat") {
      e.preventDefault();
      const v = el.value.trim(); if (!v) return;
      const p = cfg().projects[+el.dataset.i];
      p.platforms = Array.from(new Set([...(p.platforms || []), v]));
      el.value = ""; Site.refresh(); render();
    }
  }

  function moveInCategory(i, dir) {
    const arr = cfg().projects, cat = arr[i].category;
    let j = i + dir;
    while (j >= 0 && j < arr.length && arr[j].category !== cat) j += dir;
    if (j < 0 || j >= arr.length) return;
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  const swap = (arr, i, j) => { if (j < 0 || j >= arr.length) return; [arr[i], arr[j]] = [arr[j], arr[i]]; };

  async function onClick(e) {
    const tabBtn = e.target.closest("[data-tab]");
    if (tabBtn) { tab = tabBtn.dataset.tab; confirmRef = null; render(); $("#a-body", drawer).scrollTop = 0; return; }
    const b = e.target.closest("[data-act]");
    if (!b || b.disabled) return;
    const c = cfg(), i = +b.dataset.i, act = b.dataset.act;
    const P = c.projects;
    switch (act) {
      case "preview": $("#app").classList.toggle("show-preview"); return;
      case "save": save(); return;
      case "set": {
        let v = b.dataset.v;
        if (b.dataset.path === "background.style") { c.background.enabled = v !== "none"; if (v === "none") { render(); Site.refresh(); return; } }
        setPath(c, b.dataset.path, v);
        Site.refresh({ intro: !!b.dataset.intro }); render(); return;
      }
      case "concept": {
        const k = b.dataset.v, x = Site.CONCEPTS[k];
        c.concept = k; c.theme.font = x.font;
        c.background.enabled = true; c.background.style = x.bg;
        Site.refresh({ intro: true }); render(); return;
      }
      case "preset": c.theme.preset = b.dataset.v; c.theme.accent = null; Site.setManualPreset(null); Site.refresh(); render(); return;
      case "accent-reset": c.theme.accent = null; Site.refresh(); render(); return;
      case "replay": Site.replayIntro(); return;

      case "edit": openRef = openRef === P[i] ? null : P[i]; confirmRef = null; render(); if (openRef) { const n = $(`.it[data-i="${i}"] [data-bind$=".name"]`, drawer); n && n.focus(); } return;
      case "feat": P[i].featured = !P[i].featured; break;
      case "hide": P[i].hidden = !P[i].hidden; break;
      case "up": moveInCategory(i, -1); break;
      case "down": moveInCategory(i, 1); break;
      case "plat": {
        const v = b.dataset.v, s = new Set(P[i].platforms || []);
        s.has(v) ? s.delete(v) : s.add(v);
        P[i].platforms = Array.from(s); break;
      }
      case "del": confirmRef = P[i]; render(); return;
      case "del-no": confirmRef = null; render(); return;
      case "del-yes": P.splice(i, 1); confirmRef = null; openRef = null; toast("Usunięto projekt."); break;
      case "add-project": {
        const p = { name: "Nowy projekt", repo: "", category: (c.categories[0] || {}).id || "", desc: "", platforms: [], updated: today() };
        P.unshift(p); openRef = p; Site.refresh(); render();
        const n = $(`.it[data-i="0"] [data-bind$=".name"]`, drawer); if (n) { n.focus(); n.select(); }
        return;
      }
      case "add-cat": {
        let id = slug("Nowa kategoria"), k = 2;
        while (c.categories.some(x => x.id === id)) id = slug("Nowa kategoria") + "-" + k++;
        c.categories.push({ id, label: "Nowa kategoria" }); break;
      }
      case "cat-up": swap(c.categories, i, i - 1); break;
      case "cat-down": swap(c.categories, i, i + 1); break;
      case "cat-del": {
        const n = P.filter(p => p.category === c.categories[i].id).length;
        if (n) { toast(`W tej kategorii jest ${n} proj. Przenieś je najpierw do innej.`, 4000); return; }
        c.categories.splice(i, 1); break;
      }
      case "sort-date": P.sort((a, b2) => String(b2.updated || "").localeCompare(String(a.updated || ""))); toast("Posortowano od najnowszych zmian."); break;
      case "sync-dates": syncDates(); return;
      case "import": startImport(); return;
      case "import-close": imp = null; render(); return;
      case "import-add": importPicked(); return;

      case "add-link": c.profile.links.push({ label: "", url: "" }); render(); { const l = $$(".mini input", drawer); const x = l[l.length - 2]; x && x.focus(); } return;
      case "link-up": swap(c.profile.links, i, i - 1); break;
      case "link-del": c.profile.links.splice(i, 1); break;
      case "avatar-del": c.profile.avatar = ""; break;

      case "copy-json": {
        const ta = $("#a-json", drawer); ta.value = JSON.stringify(c, null, 2);
        try { await navigator.clipboard.writeText(ta.value); toast("Skopiowano config.json. Podmień nim plik w repozytorium."); }
        catch (_) { ta.focus(); ta.select(); toast("Tekst zaznaczony, skopiuj go skrótem Ctrl+C."); }
        return;
      }
      case "refresh-json": $("#a-json", drawer).value = JSON.stringify(c, null, 2); return;
      case "discard": setCfg(JSON.parse(saved)); openRef = null; render(); toast("Przywrócono ostatnio zapisaną wersję."); return;
      case "relogin": showLogin(); return;
      case "logout": store.clear(); token = null; user = null; mode = null; sha = null; showLogin(); toast("Wylogowano."); return;
      default: return;
    }
    Site.refresh({ term: act.startsWith("link") }); render();
  }

  /* ---------- Przeciąganie ---------- */
  let dragFrom = -1;
  function onDragStart(e) {
    const it = e.target.closest(".it"); if (!it) return;
    dragFrom = +it.dataset.i; it.classList.add("drag");
    e.dataTransfer.effectAllowed = "move";
    try { e.dataTransfer.setData("text/plain", String(dragFrom)); } catch (_) {}
  }
  function onDragOver(e) {
    if (dragFrom < 0) return;
    const it = e.target.closest(".it"), head = e.target.closest("[data-cat]");
    if (!it && !head) return;
    e.preventDefault();
    if (it) {
      const r = it.getBoundingClientRect(), after = e.clientY > r.top + r.height / 2;
      it.classList.toggle("over-bot", after); it.classList.toggle("over-top", !after);
    }
  }
  function onDrop(e) {
    if (dragFrom < 0) return;
    e.preventDefault();
    const P = cfg().projects;
    const it = e.target.closest(".it"), head = e.target.closest("[data-cat]");
    const src = P[dragFrom];
    if (it) {
      const to = +it.dataset.i, target = P[to];
      if (target !== src) {
        const r = it.getBoundingClientRect(), after = e.clientY > r.top + r.height / 2;
        P.splice(dragFrom, 1);
        let idx = P.indexOf(target) + (after ? 1 : 0);
        src.category = target.category;
        P.splice(idx, 0, src);
      }
    } else if (head && head.dataset.cat) {
      P.splice(dragFrom, 1);
      src.category = head.dataset.cat;
      const first = P.findIndex(p => p.category === head.dataset.cat);
      P.splice(first < 0 ? P.length : first, 0, src);
    }
    dragFrom = -1;
    Site.refresh(); render();
  }

  /* ---------- Import z GitHuba ---------- */
  async function fetchRepos() {
    const owner = cfg().admin.owner;
    return api(`/users/${encodeURIComponent(owner)}/repos?per_page=100&sort=pushed`);
  }
  async function startImport() {
    imp = { loading: true, repos: [], picked: new Set(), cat: (cfg().categories[0] || {}).id };
    render();
    try { imp.repos = await fetchRepos(); imp.loading = false; }
    catch (e) { imp.loading = false; imp.error = errText(e); }
    render();
  }
  function importPicked() {
    const c = cfg(), owner = c.admin.owner;
    const add = imp.repos.filter(r => imp.picked.has(r.name)).map(r => ({
      name: r.name, repo: r.name, category: imp.cat || (c.categories[0] || {}).id,
      desc: r.description || "", platforms: r.has_pages ? ["Web"] : [],
      demo: r.has_pages ? `https://${owner}.github.io/${r.name}/` : "",
      updated: (r.pushed_at || "").slice(0, 10)
    }));
    c.projects.unshift(...add);
    toast(`Dodano ${add.length} proj. Uzupełnij opisy i platformy.`, 3500);
    imp = null; Site.refresh(); render();
  }
  async function syncDates() {
    try {
      toast("Pobieram daty z GitHuba...");
      const repos = await fetchRepos();
      const map = new Map(repos.map(r => [r.name.toLowerCase(), (r.pushed_at || "").slice(0, 10)]));
      let n = 0;
      cfg().projects.forEach(p => { const d = map.get(String(p.repo || "").toLowerCase()); if (d && d !== p.updated) { p.updated = d; n++; } });
      toast(n ? `Zaktualizowano daty: ${n}.` : "Wszystkie daty są aktualne.");
      Site.refresh(); render();
    } catch (e) { toast(errText(e), 5000); }
  }

  /* ---------- Zdjęcie profilowe ---------- */
  function loadAvatar(file) {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const S = 256, cv = document.createElement("canvas"); cv.width = S; cv.height = S;
      const s = Math.min(img.width, img.height);
      cv.getContext("2d").drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, 0, 0, S, S);
      cfg().profile.avatar = cv.toDataURL("image/jpeg", 0.85);
      URL.revokeObjectURL(url);
      if (cfg().concept !== "klasyk") toast("Zdjęcie widać w koncepcji Linktree.");
      Site.refresh(); render();
    };
    img.onerror = () => { URL.revokeObjectURL(url); toast("Nie udało się odczytać tego obrazu.", 4000); };
    img.src = url;
  }

})();
