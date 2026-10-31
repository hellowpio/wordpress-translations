#!/usr/bin/env python3
"""Release-csomag a scripts/build.py kimenetéből (dist/manifest.json): egyetlen zip az összes fordítással.

Kimenet a dist/release/ alá:
  wordpress-translations.zip   minden fordítás: <tone>/<plugins|themes>/<locale>/ alatt a csomagok .po, .mo,
                               .l10n.php és .json fájljai egy mappában — a választott hangnem
                               <plugins|themes>/<locale>/ mappájának tartalma egy az egyben a
                               wp-content/languages/<plugins|themes>/ mappába másolható
  stats.json                   a dist/stats.json másolata

Egy zip a csomagonkénti zipek helyett: a GitHub egy release-be nem enged ezernyi fájlt egyszerre feltölteni.

Használat:
  scripts/package.py [--dist <mappa>]    a build kimenete (alapból: dist)
"""
import json
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_NAME = 'wordpress-translations.zip'


def main(argv):
    args = list(argv)
    dist = os.path.join(ROOT, 'dist')
    while args:
        a = args.pop(0)
        if a == '--dist':
            dist = os.path.abspath(args.pop(0))
        elif a in ('-h', '--help'):
            print(__doc__)
            return 0
        elif a == '--base-url':  # a régi release.yml-ek kedvéért elfogadjuk, de már nem kell
            args.pop(0)
        else:
            sys.exit('Ismeretlen kapcsoló: ' + a)
    manifest_path = os.path.join(dist, 'manifest.json')
    if not os.path.exists(manifest_path):
        sys.exit('Nincs {}: előbb scripts/build.py --dist'.format(os.path.relpath(manifest_path, ROOT)))
    manifest = json.load(open(manifest_path, encoding='utf-8'))

    out = os.path.join(dist, 'release')
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    seen, files = set(), 0
    with zipfile.ZipFile(os.path.join(out, ZIP_NAME), 'w', zipfile.ZIP_DEFLATED) as z:
        for pkg in sorted(manifest, key=lambda p: (p['tone'], p['type'], p['locale'], p['slug'])):
            for f in pkg['files']:
                arc = '{}/{}s/{}/{}'.format(pkg['tone'], pkg['type'], pkg['locale'], f)
                if arc in seen:  # azonos nevű fájl két csomagban: az első marad
                    print('figyelmeztetés: kétszer szereplő fájlnév, kimarad: ' + arc)
                    continue
                seen.add(arc)
                z.write(os.path.join(dist, pkg['dir'], f), arc)
                files += 1
    shutil.copy2(os.path.join(dist, 'stats.json'), out)
    print('Kész: {} ({} csomag, {} fájl), stats.json. Kimenet: {}'.format(
        ZIP_NAME, len(manifest), files, os.path.relpath(out, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
