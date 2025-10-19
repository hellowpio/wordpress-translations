# WordPress Fordítások Gyűjteménye

Ez a repository WordPress bővítmények és témák fordításait tartalmazza különböző nyelveken.

## Mappastruktúra

A fordítások a következő struktúrában vannak rendszerezve:

```
wordpress-translations/
├── plugins/
│   └── hu_HU/
│       ├── elementor-pro/
│       ├── woocommerce/
│       └── ...
└── themes/
    └── hu_HU/
        ├── astra/
        ├── generatepress/
        └── ...
```

## Használat

### Bővítmények fordításai

A bővítmények fordításai a `plugins/{nyelv_KÓD}/{bővítmény-neve}/` mappában találhatók.

Példa: `plugins/hu_HU/elementor-pro/`

### Témák fordításai

A témák fordításai a `themes/{nyelv_KÓD}/{téma-neve}/` mappában találhatók.

Példa: `themes/hu_HU/astra/`

## Nyelvi kódok

- `hu_HU` - Magyar
- További nyelvek később...

## Fordítás fájlok telepítése

### 1. módszer: Manuális telepítés

1. Navigálj a megfelelő mappába (plugins vagy themes)
2. Válaszd ki a nyelvi kódot (pl. `hu_HU`)
3. Keresd meg a bővítmény/téma nevét
4. Másold a `.po` fájlt a WordPress telepítésed megfelelő könyvtárába:
   - Bővítmények: `wp-content/languages/plugins/`
   - Témák: `wp-content/languages/themes/`

### 2. módszer: Loco Translate bővítménnyel

1. Telepítsd és aktiváld a [Loco Translate](https://wordpress.org/plugins/loco-translate/) bővítményt
2. Töltsd le a `.po` fájlt ebből a repository-ból
3. Másold a `.po` fájlt a megfelelő WordPress languages mappába:
   - Bővítmények: `wp-content/languages/plugins/`
   - Témák: `wp-content/languages/themes/`
4. WordPress admin felületen: **Loco Translate → Plugins** vagy **Themes**
5. Válaszd ki a bővítményt/témát
6. Kattints a fordítási nyelvre (pl. Magyar)
7. Nyisd meg a fordítást és kattints a **Mentés** gombra
8. A Loco automatikusan generálja a `.mo` és `.l10n.php` fájlokat

**Tipp:** A Loco Translate segítségével szerkesztheted is a fordításokat közvetlenül a WordPress admin felületen.

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

Ez a repository automatikusan generálja a `.mo` és `.l10n.php` fájlokat a `.po` fájlokból.

### Lokális build (fejlesztőknek)

```bash
# Függőségek telepítése (első alkalommal)
npm install

# Fordítások build-elése
npm run build

# Watch mód (automatikus újragenerálás változáskor)
npm run watch
```

### GitHub Actions

A repository automatikusan futtatja a következő ellenőrzéseket:

- **PHP Syntax Check**: Ellenőrzi a `.l10n.php` fájlok szintaxisát PHP 8.0-8.3 verziókon
- **Dependabot**: Hetente ellenőrzi és frissíti az npm függőségeket

## Hozzájárulás

Ha szeretnél hozzájárulni új fordításokkal vagy javításokkal:

1. Fork-old ezt a repository-t
2. Hozz létre egy új branch-et (`git checkout -b uj-forditas`)
3. **Csak a `.po` fájlt add hozzá** - a `.mo` és `.l10n.php` fájlok automatikusan generálódnak
4. A `.po` fájl fejlécébe add meg a verzió információt:
   ```
   "X-Plugin-Version: 5.3.0\n"
   ```
   (ahol a szám a bővítmény/téma verzióját jelöli, amiről a fordítás készült)
5. Commit-old a változtatásokat (`git commit -m 'Új fordítás hozzáadása'`)
6. Push-old a branch-et (`git push origin uj-forditas`)
7. Nyiss egy Pull Request-et

## Licenc

A fordítások a megfelelő WordPress bővítmények és témák licencei alatt állnak.

## Kapcsolat

Ha kérdésed van, nyiss egy issue-t ebben a repository-ban.
