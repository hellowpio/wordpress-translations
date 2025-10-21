# WordPress Fordítások Gyűjteménye

Ez a repository WordPress bővítmények és témák fordításait tartalmazza különböző nyelveken. Jelenleg **393 bővítmény** és **9 téma** magyar fordítása érhető el.

## Mappastruktúra

A fordítások formális (magázódó) és informális (tegező) változatokban érhetők el:

```
wordpress-translations/
├── formal/              # Magázódó fordítások (Ön, Önnek, stb.)
│   ├── plugins/
│   │   └── hu_HU/
│   │       ├── elementor-pro/
│   │       ├── woocommerce/
│   │       └── ...
│   └── themes/
│       └── hu_HU/
│           ├── astra/
│           ├── generatepress/
│           └── ...
└── informal/            # Tegező fordítások (te, neked, stb.)
    ├── plugins/
    │   └── hu_HU/
    │       └── ...
    └── themes/
        └── hu_HU/
            └── ...
```

**Melyiket válaszd?**
- **formal**: Hivatalos, professzionális, üzleti weboldalaknál (pl. webshop, vállalati oldal)
- **informal**: Barátságos, közvetlen stílusú oldalaknál (pl. blog, közösségi oldal)

## Használat

### Bővítmények fordításai

A bővítmények fordításai a `{formal|informal}/plugins/{nyelv_KÓD}/{bővítmény-neve}/` mappában találhatók.

Példák:
- Magázódó: `formal/plugins/hu_HU/elementor-pro/`
- Tegező: `informal/plugins/hu_HU/elementor-pro/`

### Témák fordításai

A témák fordításai a `{formal|informal}/themes/{nyelv_KÓD}/{téma-neve}/` mappában találhatók.

Példák:
- Magázódó: `formal/themes/hu_HU/astra/`
- Tegező: `informal/themes/hu_HU/astra/`

## Nyelvi kódok

- `hu_HU` - Magyar
- További nyelvek később...

## Fordítási fájlformátumok

A WordPress fordítási rendszere több fájlformátumot használ különböző célokra:

### .po fájlok (Portable Object)
- **Célja**: Emberi olvasásra szánt szövegfájl, amely tartalmazza az eredeti szövegeket és fordításaikat
- **Használat**: Fordítók és fejlesztők számára a fordítások szerkesztéséhez
- **Példa**: `plugin-name-hu_HU.po`

### .mo fájlok (Machine Object)
- **Célja**: Bináris formátum a gyors betöltéshez
- **Használat**: A WordPress hagyományosan ezt használja PHP kódban található szövegek fordításához (`__()`, `_e()` függvények)
- **Generálás**: Automatikusan generálódik a .po fájlokból
- **Példa**: `plugin-name-hu_HU.mo`

### .l10n.php fájlok (WordPress 6.5+)
- **Célja**: Optimalizált PHP cache fájl a gyorsabb betöltéshez
- **Használat**: WordPress 6.5 óta ez az elsődleges formátum, 10-30%-kal gyorsabb mint a .mo fájlok
- **Előnyök**:
  - Natív PHP array formátum, nem igényel bináris parsing-ot
  - OPcache-elhető a még jobb teljesítményért
  - Kisebb memóriahasználat
- **Generálás**: Automatikusan generálódik a .po fájlokból
- **Példa**: `plugin-name-hu_HU.l10n.php`

### .json fájlok (WordPress 5.0+)
- **Célja**: JavaScript alapú fordítások támogatása
- **Használat**: Gutenberg blokkok, React komponensek és más JavaScript kód fordításaihoz
- **Mikor kell**:
  - Ha a plugin/téma használja a Block Editor-t (Gutenberg)
  - Ha JavaScript kódban van `wp.i18n.__()` függvény
  - Modern admin felületeknél, ahol React/Vue.js keretrendszert használnak
- **Generálás**: WP-CLI `wp i18n make-json` paranccsal a .po fájlokból
- **Példa**: `plugin-name-hu_HU-{script-handle-hash}.json`

### Melyik fájlra van szükség?

| WordPress verzió | PHP fordítások | JavaScript fordítások |
|-----------------|---------------|----------------------|
| < 5.0 | .mo | - |
| 5.0 - 6.4 | .mo | .json |
| 6.5+ | .l10n.php (elsődleges) vagy .mo | .json |

**Fontos**: Ez a repository automatikusan generálja az összes szükséges formátumot (.mo, .l10n.php, .json) a .po fájlokból, így biztosítva a kompatibilitást minden WordPress verzióval.

## Fordítás fájlok telepítése

### 1. módszer: Manuális telepítés

1. Válaszd ki a megfelelő stílust (`formal` vagy `informal`)
2. Navigálj a megfelelő mappába (plugins vagy themes)
3. Válaszd ki a nyelvi kódot (pl. `hu_HU`)
4. Keresd meg a bővítmény/téma nevét
5. Másold a `.po` fájlt a WordPress telepítésed megfelelő könyvtárába:
   - Bővítmények: `wp-content/languages/plugins/`
   - Témák: `wp-content/languages/themes/`

### 2. módszer: Loco Translate bővítménnyel

1. Telepítsd és aktiváld a [Loco Translate](https://wordpress.org/plugins/loco-translate/) bővítményt
2. Töltsd le a `.po` fájlt a megfelelő mappából (`formal` vagy `informal`)
3. Másold a `.po` fájlt a megfelelő WordPress languages mappába:
   - Bővítmények: `wp-content/languages/plugins/`
   - Témák: `wp-content/languages/themes/`
4. WordPress admin felületen: **Loco Translate → Plugins** vagy **Themes**
5. Válaszd ki a bővítményt/témát
6. Kattints a fordítási nyelvre (pl. Magyar)
7. Nyisd meg a fordítást és kattints a **Mentés** gombra
8. A Loco automatikusan generálja a `.mo` és `.l10n.php` fájlokat

**Tipp:** A Loco Translate segítségével szerkesztheted is a fordításokat közvetlenül a WordPress admin felületen.

**Fontos:** Ha később át szeretnél váltani formal és informal között, egyszerűen cseréld le a `.po` fájlt a másik változatra és mentsd el újra.

## POT fájl generálása (fejlesztőknek)

A POT (Portable Object Template) fájl generálásához az alábbi eszközöket használhatod:

### WP-CLI
```bash
wp i18n make-pot /path/to/plugin /path/to/plugin/languages/plugin-name.pot
```

### Gulp
```bash
npm install --save-dev gulp-wp-pot
```

```javascript
const gulp = require('gulp');
const wpPot = require('gulp-wp-pot');

gulp.task('pot', function() {
    return gulp.src('**/*.php')
        .pipe(wpPot({
            domain: 'your-text-domain',
            package: 'Your Plugin Name'
        }))
        .pipe(gulp.dest('languages/your-plugin.pot'));
});
```

### Homebrew eszközök (macOS)
```bash
brew install gettext
xgettext --language=PHP --from-code=UTF-8 --keyword=__ --keyword=_e --keyword=_n:1,2 --keyword=_x:1,2c --keyword=_ex:1,2c --keyword=esc_attr__ --keyword=esc_attr_e --keyword=esc_attr_x:1,2c --keyword=esc_html__ --keyword=esc_html_e --keyword=esc_html_x:1,2c -o languages/plugin-name.pot **/*.php
```

## Automatikus Build Rendszer

Ez a repository automatikusan generálja a `.mo`, `.l10n.php` és `.json` fájlokat a `.po` fájlokból.

### Lokális build (fejlesztőknek)

```bash
# Függőségek telepítése (első alkalommal)
npm install

# Fordítások build-elése (generálja: .mo, .l10n.php, .json)
npm run build

# Watch mód (automatikus újragenerálás változáskor)
npm run watch
```

#### Mi generálódik a build során?

1. **`.mo` fájlok** - Régebbi WordPress verziók és visszafelé kompatibilitás miatt
2. **`.l10n.php` fájlok** - WordPress 6.5+ optimalizált teljesítmény
3. **`.json` fájlok** - JavaScript fordítások (ha a plugin használ Gutenberg blokkokat vagy modern JS-t)

**Megjegyzés**: A JSON fájlok generálásához szükséges a WP-CLI telepítése (`wp` parancs)

### GitHub Actions

A repository automatikusan futtatja a következő ellenőrzéseket:

- **PHP Syntax Check**: Ellenőrzi a `.l10n.php` fájlok szintaxisát PHP 8.0-8.3 verziókon
- **Dependabot**: Hetente ellenőrzi és frissíti az npm függőségeket

## Hozzájárulás

Ha szeretnél hozzájárulni új fordításokkal vagy javításokkal:

1. Fork-old ezt a repository-t
2. Hozz létre egy új branch-et (`git checkout -b uj-forditas`)
3. **Csak a `.po` fájlt add hozzá** - a `.mo` és `.l10n.php` fájlok automatikusan generálódnak
4. **A `.po` fájl fejlécébe add meg a következő kötelező metaadatokat:**
   ```
   "X-Plugin-Name: Advanced Custom Fields Multilingual\n"
   "X-Plugin-Tone: formal\n"
   "X-Plugin-Version: 2.1.5\n"
   ```
   - `X-Plugin-Name`: A bővítmény/téma teljes neve (angolul)
   - `X-Plugin-Tone`: A fordítás hangvétele (`formal` = magázódó, `informal` = tegező)
   - `X-Plugin-Version`: A verzió száma, amiről a fordítás készült

   Ezek a metaadatok bekerülnek a generált `.l10n.php` fájlba és segítenek a verziókövetésben.

   **Fontos**: Az `X-Plugin-Tone` értékének meg kell egyeznie a könyvtárstruktúrával:
   - `formal/` mappában lévő fájloknak: `X-Plugin-Tone: formal`
   - `informal/` mappában lévő fájloknak: `X-Plugin-Tone: informal`
5. Commit-old a változtatásokat (`git commit -m 'Új fordítás hozzáadása'`)
6. Push-old a branch-et (`git push origin uj-forditas`)
7. Nyiss egy Pull Request-et

## Licenc

A fordítások a megfelelő WordPress bővítmények és témák licencei alatt állnak.

## Statisztikák

Érdekes adatok a fordítási projektünkről:

📊 **Összesítés:**
- **Fordítási fájlok száma**: 402 db
- **Fordítási bejegyzések**: 184 004 db
- **Lefordított bejegyzések**: 183 248 db (99.6% lefedettség)

📝 **Karakterszám:**
- **Angol (eredeti)**: 6 081 166 karakter
- **Magyar (fordítás)**: 7 037 792 karakter

📈 **Különbség:**
- A magyar fordítások **+956 626 karakterrel** (15.73%-kal) hosszabbak az angol eredetinél
- Ez a magyar nyelv természetes jellemzője - általában hosszabb szószerkezetek szükségesek ugyanazon jelentés kifejezéséhez

## Kapcsolat

Ha kérdésed van, nyiss egy issue-t ebben a repository-ban.

