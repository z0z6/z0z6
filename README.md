# z0z6.github.io

Strona z listą projektów i panelem administratora. Czysty HTML, CSS i JS, bez budowania i bez płatnych usług.

## Pliki

| Plik | Do czego |
|---|---|
| `config.json` | Cała treść i wygląd: profil, linki, koncepcja, motyw, tło, kategorie, projekty. Zmienia go panel. |
| `index.html`, `style.css`, `app.js` | Strona |
| `admin.html`, `admin.js`, `admin.css` | Panel administratora pod adresem `/admin.html`: edycja po lewej, podgląd strony na żywo po prawej |

## Publikacja na GitHub Pages

1. Utwórz publiczne repozytorium o nazwie dokładnie **`z0z6.github.io`**.
2. Wrzuć do niego te pliki (gałąź `main`).
3. *Settings → Pages → Source: Deploy from a branch → `main` / `(root)`*.
4. Po minucie strona działa pod **https://z0z6.github.io**.

## Panel administratora

Wejdź na **https://z0z6.github.io/admin.html** i wklej token GitHub. Panel zapisuje `config.json` w repozytorium przez GitHub API, a GitHub Pages publikuje zmianę w około minutę.

**Token (jednorazowo):**
1. Otwórz https://github.com/settings/personal-access-tokens/new
2. *Repository access → Only select repositories →* `z0z6.github.io`
3. *Permissions → Contents → Read and write*
4. *Generate token*, wklej w okno logowania. Zaznacz „Zapamiętaj”, żeby nie wklejać go za każdym razem.

Token zostaje tylko w Twojej przeglądarce. Na stronie głównej nie ma przycisku do panelu, a bez tokenu z prawem zapisu nikt niczego nie zmieni, nawet jeśli trafi na `/admin.html`. Strona panelu ma `noindex`, więc wyszukiwarki jej nie pokażą.

**Co jest w panelu:**
- **Projekty:** dodawanie, edycja, usuwanie, wyróżnianie, ukrywanie, przeciąganie między kategoriami, import repozytoriów z GitHuba, pobieranie dat ostatnich zmian.
- **Profil:** napis w nagłówku, opis, zdjęcie, linki.
- **Wygląd:** 5 koncepcji (Matryca, Kafle, Terminal, Indeks, Linktree), 14 motywów i własne kolory, czcionka, tło (Fala, Przepływ, Deszcz), animacje.
- **Publikacja:** zapis, cofanie zmian, kopia `config.json`.
- **Podgląd:** każda zmiana od razu widoczna obok, w widoku komputera albo telefonu.

Poza GitHub Pages (np. przy otwarciu pliku lokalnie) panel ma też **tryb próbny** bez logowania: zmiany widać od razu, a gotowy `config.json` można skopiować.

## Podgląd lokalny

`config.json` wczytuje się przez `fetch`, więc otwórz stronę przez serwer, a nie przez dwuklik na pliku:

```
python3 -m http.server 8000
```

## Własny krótki adres (opcjonalnie, za darmo)

[is-a.dev](https://github.com/is-a-dev/register) daje subdomenę typu `z0z6.is-a.dev` (pull request z rekordem `CNAME` → `z0z6.github.io`). Potem wpisz ją w *Settings → Pages → Custom domain* oraz w panelu: *Publikacja → Własna domena*.
