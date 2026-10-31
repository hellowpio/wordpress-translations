#!/usr/bin/env python3
"""Release-csomagok a scripts/build.py kimenetéből (dist/manifest.json).

Kimenet a dist/release/ alá:
  <mappa>-<locale>-<tone>.zip     csomagonként: .po, .mo, .l10n.php, .json (a zip gyökerében,
                                  ahogy a wp-content/languages/<plugins|themes>/ várja)
  translations-formal.json        a WordPress fordítás-API szerkezetében
  translations-informal.json      ({"translations": [{type, slug, language, version, updated, package, autoupdate}]})
  stats.json                      a dist/stats.json másolata

Használat:
  scripts/package.py --base-url <URL>    a zipek letöltési címének eleje, pl.
                                         https://github.com/<org>/<repo>/releases/download/<tag>
  --dist <mappa>                         a build kimenete (alapból: dist)
"""
import datetime
import json
import os
import re
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TONES = ('formal', 'informal')


def iso_date(po_date, fallback):
    """'2025-10-21 10:11+0200' → '2025-10-21T10:11:00+02:00'; ha nem értelmezhető: fallback."""
    m = re.match(r'^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})(?::(\d{2}))?\s*([+-]\d{4})?$', (po_date or '').strip())
    if not m:
        return fallback, False
    tz = m.group(4) or '+0000'
    return '{}T{}:{}{}:{}'.format(m.group(1), m.group(2), m.group(3) or '00', tz[:3], tz[3:]), True


def main(argv):
    args = list(argv)
    dist, base_url = os.path.join(ROOT, 'dist'), None
    while args:
        a = args.pop(0)
        if a == '--dist':
            dist = os.path.abspath(args.pop(0))
        elif a == '--base-url':
            base_url = args.pop(0).rstrip('/')
        elif a in ('-h', '--help'):
            print(__doc__)
            return 0
        else:
            sys.exit('Ismeretlen kapcsoló: ' + a)
    if not base_url:
        sys.exit('Kell a --base-url (a release letöltési címének eleje).')
    manifest_path = os.path.join(dist, 'manifest.json')
    if not os.path.exists(manifest_path):
        sys.exit('Nincs {}: előbb scripts/build.py'.format(os.path.relpath(manifest_path, ROOT)))
    manifest = json.load(open(manifest_path, encoding='utf-8'))

    out = os.path.join(dist, 'release')
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    translations = {t: [] for t in TONES}
    bad_dates = []
    for pkg in manifest:
        name = '{}-{}-{}.zip'.format(pkg['slug'], pkg['locale'], pkg['tone'])
        with zipfile.ZipFile(os.path.join(out, name), 'w', zipfile.ZIP_DEFLATED) as z:
            for f in pkg['files']:
                z.write(os.path.join(dist, pkg['dir'], f), f)
        updated, ok = iso_date(pkg.get('po_revision_date'), now)
        if not ok:
            bad_dates.append(name)
        translations[pkg['tone']].append({
            'type': pkg['type'],
            'slug': pkg['slug'],
            'language': pkg['locale'],
            'version': pkg.get('version', ''),
            'updated': updated,
            'package': '{}/{}'.format(base_url, name),
            'autoupdate': True,
        })
    for tone in TONES:
        items = sorted(translations[tone], key=lambda x: (x['type'], x['slug'], x['language']))
        with open(os.path.join(out, 'translations-{}.json'.format(tone)), 'w', encoding='utf-8') as fh:
            json.dump({'translations': items}, fh, ensure_ascii=False, indent=1)
    shutil.copy2(os.path.join(dist, 'stats.json'), out)

    for n in bad_dates:
        print('figyelmeztetés: nem értelmezhető PO-Revision-Date, a build ideje került be: ' + n)
    print('Kész: {} zip, translations-formal.json ({}), translations-informal.json ({}). Kimenet: {}'.format(
        len(manifest), len(translations['formal']), len(translations['informal']), os.path.relpath(out, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
