# WordPress-fordítások

WordPress-bővítmények és -sablonok fordításai, elsősorban magyarul (`hu_HU`), magázó (`formal`) és tegező
(`informal`) változatban. A forrás a `.po` fájl; a WordPress által betöltött `.mo`, `.l10n.php` és `.json`
fájlok minden változás után automatikusan elkészülnek, és a [Releases](https://github.com/hellowpio/wordpress-translations/releases) oldalról tölthetők le.

## Letöltés és telepítés

A [legutóbbi release](https://github.com/hellowpio/wordpress-translations/releases/latest) csomagonként egy zipet tartalmaz:
`<mappa>-<locale>-<tone>.zip`, például `woocommerce-subscriptions-hu_HU-formal.zip`. A zipben a `.po`, `.mo`,
`.l10n.php` és a JavaScript-fordítások `.json` fájljai vannak; a tartalmát ide kell kicsomagolni:

- bővítménynél: `wp-content/languages/plugins/`
- sablonnál: `wp-content/languages/themes/`

Ugyanitt van két jegyzék a WordPress fordítás-API szerkezetében (`type`, `slug`, `language`, `version`, `updated`,
`package`, `autoupdate`), automatikus frissítéshez:

- [translations-formal.json](https://github.com/hellowpio/wordpress-translations/releases/latest/download/translations-formal.json)
- [translations-informal.json](https://github.com/hellowpio/wordpress-translations/releases/latest/download/translations-informal.json)

A `version` az a bővítmény- vagy sablonverzió, amelyből a fordítás készült (a `.po` `X-Plugin-Version` fejléce),
az `updated` a `.po` `PO-Revision-Date` fejléce.

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
  plugins/<locale>/<mappa>/<mappa>-<locale>.po
  themes/<locale>/<mappa>/<mappa>-<locale>.po
informal/                  tegező fordítások, ugyanígy
```

A `<mappa>` a bővítmény vagy sablon text domainje, a `<locale>` a nyelvi kód (pl. `hu_HU`).

| Fájl | Mire való | WordPress |
|---|---|---|
| `.po` | a forrás, ezt szerkesztjük | — |
| `.mo` | bináris fordítás a PHP-szövegekhez | minden verzió |
| `.l10n.php` | PHP-tömb a PHP-szövegekhez, gyorsabban töltődik a `.mo`-nál | 6.5+ |
| `-<hash>.json` | a JavaScript-szövegek (blokkszerkesztő, React-felületek) fordítása | 5.0+ |

A generált fájlok (`.mo`, `.l10n.php`, `.json`) nincsenek a gitben, csak a release-ben.

## Közreműködés

1. Forkold a repót, és hozz létre egy ágat.
2. Csak a `.po` fájlt módosítsd vagy add hozzá.
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
python3 scripts/check_po.py <fájl.po>…        # msgfmt -c, helyőrzők, fejlécek, szótár-figyelmeztetés
python3 scripts/check_po.py --all             # minden .po
python3 scripts/check_po.py --changed-since main
python3 scripts/build.py [<mappa>…]           # .mo, .l10n.php, .json és stats.json a dist/ alá
python3 scripts/package.py --base-url <URL>   # zipek és translations-*.json a dist/release/ alá
```

A `check_po.py` hibának veszi a `msgfmt -c` hibáit, a msgid és a msgstr eltérő helyőrzőit (`%s`, `%1$s`, `%d`,
`{név}`, HTML-címkék) és a hiányzó vagy a mappával ellentétes fejlécet. Figyelmeztet, ha egy kézzel
rögzített szótári kifejezés a msgid-ben szerepel, de a magyar alakja nincs a fordításban.

A `build.py` a `blocked-strings.json` mintáit (API-kulcs-helyőrzők, amelyeken a GitHub push protection
fennakad) kiveszi a `.po`-ból, majd a WP-CLI `wp i18n make-mo`, `make-php` és `make-json --no-purge`
parancsával készíti el a fájlokat. A `--revision-date` kapcsoló a módosított `.po` fájlok `PO-Revision-Date`
fejlécét a mostani időre állítja; commit előtt érdemes futtatni, mert a `translations-*.json` `updated` mezője
ebből jön.

## Automatizálás (GitHub Actions)

- **CI** (`ci-cd.yml`): pull requestnél és pushnál a `check_po.py` a változott `.po` fájlokon. A repóban
  lévő régebbi hibák nem blokkolnak, csak a módosított fájlok hibái.
- **Release** (`release.yml`): a main ágra pusholt fordítás-változás után build, csomagolás és GitHub
  Release dátum-alapú taggel (`v2026.10.31`, ugyanazon a napon `v2026.10.31-2`).
- **Verzió-figyelés** (`verziok.yml`): hetente összeveti a fordítások verzióját a HelloPack legújabb
  verzióival, és az eredményt az „Elavult fordítások” issue-ba írja.
- **Dependabot**: a workflow-k GitHub Actions-verziói.

## Fordításfrissítő eszköz (`bin/hwpt`)

A `bin/hwpt` (`tools/hwpt.py`) a HelloPack-csomagok fordításának karbantartója: kiírja, melyik fordítás
melyik verzióról készült és mi a legújabb (`allapot`), letölti az új verziót, abból POT-ot készít és
összefésüli a `.po`-val (`frissit`), a hiányzó szövegeket fordítási memóriából és gépi fordítással tölti ki,
és ellenőriz (`ellenoriz`). A HelloPack-tokent és az API-kulcsot a gitignore-olt `.env`-ből olvassa. A
parancsok és a munkamenet leírása: [CLAUDE.md](CLAUDE.md).

## Statisztikák

A fájlok, bejegyzések és a lefedettség aktuális számait minden release `stats.json`-ja tartalmazza: [a legutóbbi release stats.json-ja](https://github.com/hellowpio/wordpress-translations/releases/latest/download/stats.json).

## Licenc

A fordítások az adott bővítmény vagy sablon licence alatt állnak.

## Kapcsolat

Kérdéssel issue-t lehet nyitni ebben a repóban.
