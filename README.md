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

1. Navigálj a megfelelő mappába (plugins vagy themes)
2. Válaszd ki a nyelvi kódot (pl. `hu_HU`)
3. Keresd meg a bővítmény/téma nevét
4. Másold a `.po` és `.mo` fájlokat a WordPress telepítésed megfelelő könyvtárába:
   - Bővítmények: `wp-content/languages/plugins/`
   - Témák: `wp-content/languages/themes/`

## Hozzájárulás

Ha szeretnél hozzájárulni új fordításokkal vagy javításokkal:

1. Fork-old ezt a repository-t
2. Hozz létre egy új branch-et (`git checkout -b uj-forditas`)
3. Add hozzá a fordításokat a megfelelő mappastruktúrában
4. Commit-old a változtatásokat (`git commit -m 'Új fordítás hozzáadása'`)
5. Push-old a branch-et (`git push origin uj-forditas`)
6. Nyiss egy Pull Request-et

## Licenc

A fordítások a megfelelő WordPress bővítmények és témák licencei alatt állnak.

## Kapcsolat

Ha kérdésed van, nyiss egy issue-t ebben a repository-ban.
