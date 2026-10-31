## Mi változott

<!-- Melyik bővítmény vagy sablon, melyik verzió, formal vagy informal. -->

## Ellenőrzés

- [ ] Csak `.po` fájl változott (a `.mo`, `.l10n.php` és `.json` a release-ben készül, nem kell commitolni).
- [ ] A fejlécben megvan az `X-Plugin-Name`, az `X-Plugin-Version` (a verzió, amiből a fordítás készült) és az `X-Plugin-Tone` (a mappának megfelelően `formal` vagy `informal`).
- [ ] A helyőrzők (`%s`, `%1$s`, `%d`, `{név}`, HTML-címkék) a fordításban is megvannak.
- [ ] `python3 scripts/check_po.py <fájl.po>` hiba nélkül fut (a CI is ezt futtatja).
