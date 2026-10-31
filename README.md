# WordPress-fordítások

WordPress-bővítmények és -sablonok fordításai, elsősorban magyarul (`hu_HU`), magázó (`formal`) és tegező
(`informal`) változatban. A forrás a `.po` fájl; mellette a gitben van a belőle generált `.mo` és a
JavaScript-fordítások `.json` fájljai is. A [Releases](https://github.com/hellowpio/wordpress-translations/releases)
oldalon ugyanezek csomagonként zipben is letölthetők.

## Telepítés az LW Translate bővítménnyel (ajánlott)

A legegyszerűbb az [LW Translate](https://github.com/lwplugins/lw-translate) bővítmény: a WordPress
adminfelületéről listázza a telepített bővítményekhez és sablonokhoz elérhető fordításokat ebből a repóból, és
egy kattintással telepíti, frissíti vagy törli őket. A frissítést magától jelzi, ha itt újabb fordítás jelent meg.

Kell hozzá: PHP 8.1+ és WordPress 6.6+.

1. Telepítsd a bővítményt:
   - Composerrel: `composer require lwplugins/lw-translate`
   - vagy kézzel: a [legutóbbi release](https://github.com/lwplugins/lw-translate/releases) zipjét töltsd fel
     a `wp-content/plugins/` mappába, és kapcsold be.
2. Az **LW Plugins → Translate Settings** oldalon válaszd ki a hangnemet (`formal` = magázó, `informal` =
   tegező) és a nyelvet (`hu_HU`).
3. Az **LW Plugins → Translate** oldalon telepítsd vagy frissítsd a fordításokat, egyenként vagy
   tömegesen.

A bővítmény leírása: [lwplugins/lw-translate](https://github.com/lwplugins/lw-translate).

## Az lw-translate és a fájlnév-szabály

Az lw-translate bővítmény ezt a repót élesben olvassa: a GitHub Trees API-ból (`git/trees/main?recursive=1`) listázza
a fájlokat, és a `raw.githubusercontent.com/hellowpio/wordpress-translations/main/<útvonal>` címről **közvetlenül a
main ág `.mo`, `.po` és `.json` fájljait** tölti le; hogy egy fájl frissült-e, a git blob SHA dönti el. Release-t
nem használ, a `.l10n.php`-t a `.mo`-ból maga készíti. Ezért:

- a `.mo` és a fordítási `.json` a `.po` mellett a repóban marad (a `.l10n.php` nincs a gitben);
- az útvonal `<tone>/<plugins|themes>/<locale>/<mappa>/`, a fájlnév-szabály **kötelező**:
  `^<név>-<locale>(\.mo|\.po|-[0-9a-f]{32}\.json)$`, például
  `formal/plugins/hu_HU/acf/acf-hu_HU.mo`;
- a `<mappa>` a bővítmény vagy sablon **telepítési könyvtárneve** (`wp-content/plugins/<mappa>/`, `wp-content/themes/<mappa>/`);
- a `<név>` a bővítmény **text domainje** (a `.po` `X-Domain` fejléce): a WordPress a `<text domain>-<locale>.mo`
  fájlt tölti be. Ahol a text domain megegyezik a mappával (a legtöbb csomag), a kettő ugyanaz; ahol eltér, a fájl
  a text domain nevét viseli, például
  `formal/plugins/hu_HU/complianz-gdpr-premium/complianz-gdpr-hu_HU.mo`.

A CI hibát ad, ha egy fájlnév nem illik a szabályra (az előtag nem a mappa és nem a `.po` `X-Domain`-je), ha a
`.po` mellől hiányzik az azonos nevű `.mo`, vagy ha egy `.mo`/`.json` mellett nincs azonos nevű `.po`.

## Letöltés és telepítés kézzel (bővítmény nélkül)

A [legutóbbi release](https://github.com/hellowpio/wordpress-translations/releases/latest) egyetlen zipet
tartalmaz, benne az összes fordítással:
[wordpress-translations.zip](https://github.com/hellowpio/wordpress-translations/releases/latest/download/wordpress-translations.zip).
A zipben `<tone>/<plugins|themes>/<locale>/` mappák vannak, bennük a csomagok `.po`, `.mo`, `.l10n.php` és
JavaScript-fordítási `.json` fájljai. A választott hangnem mappájának tartalmát ide kell másolni (elég a
használt bővítmények és sablonok fájljait):

- bővítményeknél: `formal/plugins/hu_HU/` (vagy `informal/…`) → `wp-content/languages/plugins/`
- sablonoknál: `formal/themes/hu_HU/` (vagy `informal/…`) → `wp-content/languages/themes/`

**Melyik változat?** A `formal` hivatalos, üzleti oldalakhoz (webshop, cégoldal), az `informal` közvetlen hangú
oldalakhoz (blog, közösségi oldal) való. Váltáskor elég a másik változat fájljait bemásolni.

Loco Translate-tel is használható: a `.po` fájlt a fenti mappába másolva a Loco a fordítást megnyitja, mentéskor
elkészíti a `.mo` és `.l10n.php` fájlt.

## Fordítási hiba bejelentése

[Fordítási hiba bejelentése](https://github.com/hellowpio/wordpress-translations/issues/new?template=forditasi-hiba.yml) (GitHub issue-űrlap).

Előfordul, hogy egy szöveg a teljes fordítás ellenére angolul jelenik meg: ilyenkor a bővítmény a szöveget nem a
WordPress fordítási rendszerén keresztül írja ki. Ezt is érdemes jelezni.

## Mappastruktúra

```
formal/                    magázó fordítások
  plugins/<locale>/<mappa>/<text domain>-<locale>.po
  themes/<locale>/<mappa>/<text domain>-<locale>.po
informal/                  tegező fordítások, ugyanígy
```

A `<mappa>` a bővítmény vagy sablon telepítési könyvtárneve, a fájlnév eleje a text domain (a legtöbbször a
kettő ugyanaz), a `<locale>` a nyelvi kód (pl. `hu_HU`). A fájlnév-szabály fent: [Az lw-translate és a fájlnév-szabály](#az-lw-translate-és-a-fájlnév-szabály).

| Fájl | Mire való | WordPress |
|---|---|---|
| `.po` | a forrás, ezt szerkesztjük | — |
| `.mo` | bináris fordítás a PHP-szövegekhez | minden verzió |
| `.l10n.php` | PHP-tömb a PHP-szövegekhez, gyorsabban töltődik a `.mo`-nál (csak a release-zipben) | 6.5+ |
| `-<hash>.json` | a JavaScript-szövegek (blokkszerkesztő, React-felületek) fordítása | 5.0+ |

A `.mo` és a `.json` a gitben is megvan (az lw-translate onnan tölti le), a `.l10n.php` csak a release-zipben.

## Közreműködés

1. Forkold a repót, és hozz létre egy ágat.
2. A `.po` fájlt módosítsd vagy add hozzá, utána futtasd a `scripts/build.py <mappa>` parancsot, és a
   `.po` mellé generált `.mo` és `.json` fájlokat is commitold (kézzel ezeket ne szerkeszd).
3. A `.po` fejlécében kötelező:
   ```
   "X-Plugin-Name: Advanced Custom Fields Multilingual\n"
   "X-Plugin-Tone: formal\n"
   "X-Plugin-Version: 2.1.5\n"
   ```
   Az `X-Plugin-Tone` a mappának felel meg (`formal/` alatt `formal`, `informal/` alatt `informal`), az
   `X-Plugin-Version` az a verzió, amelyből a fordítás készült.
4. Futtasd az ellenőrzést (lent), és nyiss pull requestet.

A terminológiához a [translation-glossary.json](translation-glossary.json) szótárt használjuk; új kifejezést
issue-ban vagy pull requestben lehet javasolni.

## Ellenőrzés és build helyben

Kell hozzá: Python 3 és a `polib` csomag (`pip install polib`), a gettext `msgfmt` parancsa, a buildhez
WP-CLI és PHP.

```bash
python3 scripts/check_po.py <fájl.po>…        # msgfmt -c, helyőrzők, fejlécek, fájlnevek, szótár-figyelmeztetés
python3 scripts/check_po.py --all             # minden .po és minden mappa
python3 scripts/check_po.py --changed-since main
python3 scripts/build.py [<mappa>…]           # .mo és .json a .po mellé (alapértelmezés)
python3 scripts/build.py --dist [<mappa>…]    # .po, .mo, .l10n.php, .json és stats.json a dist/ alá (release)
python3 scripts/package.py                    # egy zip (wordpress-translations.zip) a dist/release/ alá
```

A `check_po.py` hibának veszi a `msgfmt -c` hibáit, a msgid és a msgstr eltérő helyőrzőit (`%s`, `%1$s`, `%d`,
`{név}`, HTML-címkék), a hiányzó vagy a mappával ellentétes fejlécet, a fájlnév-szabályba nem illő fájlt és a
`.po` mellől hiányzó `.mo`-t. Figyelmeztet, ha egy kézzel
rögzített szótári kifejezés a msgid-ben szerepel, de a magyar alakja nincs a fordításban.

A `build.py` a `blocked-strings.json` mintáit (API-kulcs-helyőrzők, amelyeken a GitHub push protection
fennakad) kiveszi a `.po`-ból, majd a WP-CLI `wp i18n make-mo` és `make-json --no-purge` parancsával a `.po`
mappájába írja a `.po` nevével azonos `<név>-<locale>.mo` és `<név>-<locale>-<md5>.json` fájlokat; a csomag korábbi, már nem
generált `.json` fájljait törli. A `--dist` kapcsolóval a `dist/` alá dolgozik (`make-php` is), a forrásmappához nem
nyúl; ebből csomagol a `package.py`. A `--revision-date` kapcsoló a módosított `.po` fájlok `PO-Revision-Date`
fejlécét a mostani időre állítja; commit előtt érdemes futtatni, mert a `translations-*.json` `updated` mezője
ebből jön.

## Automatizálás (GitHub Actions)

- **CI** (`ci-cd.yml`): pull requestnél és pushnál a `check_po.py` a változott csomagmappákon (`.po`, `.mo`,
  `.json`, fájlnevek). A repóban lévő régebbi hibák nem blokkolnak, csak a módosított csomagok hibái.
- **Release** (`release.yml`, kiegészítő terjesztés): a main ágra pusholt fordítás-változás után
  `build.py --dist`, egyetlen zip és GitHub Release dátum-alapú taggel (`v2026.10.31`, ugyanazon a napon `v2026.10.31-2`).
- **Dependabot**: a workflow-k GitHub Actions-verziói.

## Statisztikák

A fájlok, bejegyzések és a lefedettség aktuális számait minden release `stats.json`-ja tartalmazza: [a legutóbbi release stats.json-ja](https://github.com/hellowpio/wordpress-translations/releases/latest/download/stats.json).

## Licenc

A fordítások az adott bővítmény vagy sablon licence alatt állnak.

## Kapcsolat

Kérdéssel issue-t lehet nyitni ebben a repóban.
