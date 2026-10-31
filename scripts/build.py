#!/usr/bin/env python3
r"""A fordítások buildje: .po → .mo és .json a .po mellé (alapból), vagy release-csomag a dist/ alá.

Alapmód (helyben): a .po mappájába `<mappa>-<locale>.mo` és `<mappa>-<locale>-<md5>.json`
(`wp i18n make-mo`, `wp i18n make-json --no-purge`). Ezeket a fájlokat a main ágról tölti le az
lw-translate bővítmény, ezért a gitben vannak; a fájlnév-szabály kötelező:
`^<mappa>-<locale>(\.mo|\.po|-[0-9a-f]{32}\.json)$`. A termékek neve a .po nevét követi; ha a
.po neve nem illik a szabályra, a build figyelmeztet (a scripts/check_po.py hibát ad). A csomag
korábbi, most nem generált `<po-név>-<md5>.json` fájljait a build törli. A .l10n.php-t helyben
nem készíti (az lw-translate a .mo-ból maga generálja, és nincs a gitben).

--dist mód (a release-hez): a .po és a .mo, .l10n.php, .json csomagonként a
dist/<tone>/<plugins|themes>/<locale>/<mappa>/ alá, plusz dist/stats.json (összesítés és
csomagonkénti adatok) és dist/manifest.json (a scripts/package.py ebből csomagol).

Mindkét módban előtte: a `blocked-strings.json` mintáinak (API-kulcs-minták) eltávolítása a forrás
.po-ból (a GitHub push protection miatt; csak akkor írja a fájlt, ha talált ilyet).

Használat:
  scripts/build.py                     minden .po, helyben
  scripts/build.py <mappa|fájl.po>…    csak a megadott csomagok (mappanév, pl. acf, vagy .po útvonal)
  --dist                               a dist/ alá (release-csomag), a .po melletti fájlokhoz nem nyúl
  --out <mappa>                        a --dist kimenete (alapból: dist; magában is --dist módot jelent)
  --revision-date                      a forrásban a HEAD-hez képest változott .po-k PO-Revision-Date
                                       fejlécét a mostani időre állítja (commit előtt, helyben)

Függőség: polib, WP-CLI (`wp`, az i18n paranccsal), PHP. A `WP` környezeti változó
megadhatja a wp parancsot (pl. "php wp-cli.phar").
"""
import collections
import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

try:
    import polib
except ImportError:  # helyben a projekt .venv-jéből
    import glob
    sys.path[:0] = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                          '.venv/lib/python*/site-packages'))
    try:
        import polib
    except ImportError:
        sys.exit('Hiányzik a polib: pip install polib (vagy a projekt .venv-je)')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TONES = ('formal', 'informal')
JSON_NAME = re.compile(r'^(.+)-[0-9a-f]{32}\.json$')


def wp_cmd():
    return shlex.split(os.environ.get('WP', 'wp'))


def all_po_files():
    out = []
    for tone in TONES:
        for dirpath, _, files in os.walk(os.path.join(ROOT, tone)):
            out += [os.path.join(dirpath, f) for f in files if f.endswith('.po')]
    return sorted(out)


def describe(po_path):
    """formal/plugins/hu_HU/acf/acf-hu_HU.po → (formal, plugins, hu_HU, acf)."""
    rel = os.path.relpath(po_path, ROOT).split(os.sep)
    if len(rel) != 5 or rel[0] not in TONES or rel[1] not in ('plugins', 'themes'):
        return None
    return rel[0], rel[1], rel[2], rel[3]


# --- 1. tiltott szövegek ----------------------------------------------------------------------------

def load_blocked():
    p = os.path.join(ROOT, 'blocked-strings.json')
    if not os.path.exists(p):
        return []
    data = json.load(open(p, encoding='utf-8'))
    # a mintát pontokkal tagolva tároljuk, hogy maga a fájl se akadjon fenn a push protectionön
    return [b['msgid_parts'].replace('.', '') for b in data.get('blocked_patterns', [])]


def remove_blocked(po_path, blocked):
    """Kiveszi a tiltott msgid-jű (kontextus nélküli) bejegyzéseket. A kivettek számát adja."""
    if not blocked:
        return 0
    with open(po_path, encoding='utf-8') as f:
        raw = f.read()
    if not any(b in raw for b in blocked):
        return 0
    po = polib.pofile(po_path, wrapwidth=0)
    drop = [e for e in po if e.msgid in blocked and not e.msgctxt]
    for e in drop:
        po.remove(e)
    if drop:
        po.save(po_path)
    return len(drop)


# --- PO-Revision-Date: csak ha a bejegyzések változtak a HEAD-hez képest ------------------------

def entries_key(po):
    return sorted((e.msgctxt or '', e.msgid, e.msgid_plural or '', e.msgstr,
                   tuple(sorted(e.msgstr_plural.items()))) for e in po if not e.obsolete)


def update_revision_date(po_path):
    rel = os.path.relpath(po_path, ROOT)
    r = subprocess.run(['git', 'show', 'HEAD:' + rel], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        if entries_key(polib.pofile(r.stdout)) == entries_key(polib.pofile(po_path)):
            return False
    now = datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M%z')
    with open(po_path, encoding='utf-8') as f:
        raw = f.read()
    new = re.sub(r'"PO-Revision-Date:.*?\\n"', '"PO-Revision-Date: {}\\\\n"'.format(now), raw, count=1)
    if new == raw:
        return False
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(new)
    return True


# --- statisztika (a scripts/count-translation-stats.py logikája) ---------------------------------

def po_stats(po):
    entries = translated = en_chars = hu_chars = 0
    for e in po:
        if e.obsolete or not e.msgid:
            continue
        entries += 1
        en_chars += len(e.msgid)
        s = e.msgstr if not e.msgid_plural else (e.msgstr_plural.get(0) or '')
        if s:
            translated += 1
            hu_chars += len(s)
    return entries, translated, en_chars, hu_chars


def run_wp(args):
    try:
        r = subprocess.run(wp_cmd() + args, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit('Nem található a WP-CLI ({}): telepítsd, vagy add meg a WP környezeti változóban.'.format(
            ' '.join(wp_cmd())))
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit('A WP-CLI hibával állt le: wp ' + ' '.join(args))
    return r.stdout.strip()


HEADER_START = re.compile(r'^msgid ""\r?\nmsgstr ""\r?\n', re.M)
REVISION = re.compile(r'^"PO-Revision-Date: *(.*?)\\n"', re.M)


def stage_po(src, dst):
    """A .po másolata a WP-CLI-nek. Ha nincs POT-Creation-Date fejléc, a WP-CLI a futás idejét
    írná a .mo-ba (minden buildnél más blob SHA → az lw-translate újra letöltené): ilyenkor a
    másolatba a PO-Revision-Date értéke kerül. A forrás .po-hoz nem nyúl."""
    with open(src, encoding='utf-8') as fh:
        raw = fh.read()
    if '"POT-Creation-Date:' not in raw:
        rev, start = REVISION.search(raw), HEADER_START.search(raw)
        if rev and start:
            raw = raw[:start.end()] + '"POT-Creation-Date: {}\\n"\n'.format(rev.group(1)) + raw[start.end():]
    with open(dst, 'w', encoding='utf-8') as fh:
        fh.write(raw)


def rule_name(d):
    """A fájlnév-szabály szerinti alapnév: <mappa>-<locale> (az lw-translate ezt keresi)."""
    return '{}-{}'.format(d[3], d[2])


def build_in_place(batches, skipped):
    """.mo és .json a .po mellé; a csomag régi, most nem generált .json fájljait törli."""
    mo = js = removed = 0
    bad_names = []
    with tempfile.TemporaryDirectory(prefix='wpt-build-') as tmp:
        for i, batch in enumerate(batches, 1):
            stage = os.path.join(tmp, str(i))
            os.makedirs(stage)
            for name, (f, _) in batch.items():
                stage_po(f, os.path.join(stage, name))
            run_wp(['i18n', 'make-mo', stage])
            run_wp(['i18n', 'make-json', stage, '--no-purge'])
            produced = os.listdir(stage)
            for name, (f, d) in sorted(batch.items()):
                base = name[:-3]
                if base != rule_name(d):
                    bad_names.append(os.path.relpath(f, ROOT))
                target = os.path.dirname(f)
                new_json = sorted(p for p in produced
                                  if JSON_NAME.match(p) and JSON_NAME.match(p).group(1) == base)
                for old in os.listdir(target):
                    m = JSON_NAME.match(old)
                    if m and m.group(1) == base and old not in new_json:
                        os.remove(os.path.join(target, old))
                        removed += 1
                if base + '.mo' in produced:
                    shutil.move(os.path.join(stage, base + '.mo'), os.path.join(target, base + '.mo'))
                    mo += 1
                for p in new_json:
                    shutil.move(os.path.join(stage, p), os.path.join(target, p))
                js += len(new_json)
            print('{}. köteg: {} .po kész'.format(i, len(batch)))
    for s in skipped:
        print('kihagyva (nem <tone>/<plugins|themes>/<locale>/<mappa>/ alatt): ' + s)
    for b in bad_names:
        print('figyelmeztetés: a .po neve nem <mappa>-<locale>.po (a termékek is a .po nevét kapják): ' + b)
    print('Kész (helyben): {} .mo, {} .json, {} elavult .json törölve.'.format(mo, js, removed))
    return 0


def main(argv):
    args = list(argv)
    out = os.path.join(ROOT, 'dist')
    revision_date, dist_mode, wanted = False, False, []
    while args:
        a = args.pop(0)
        if a == '--out':
            out = os.path.abspath(args.pop(0))
            dist_mode = True
        elif a == '--dist':
            dist_mode = True
        elif a == '--revision-date':
            revision_date = True
        elif a in ('-h', '--help'):
            print(__doc__)
            return 0
        else:
            wanted.append(a)

    files = all_po_files()
    if wanted:
        paths = {os.path.abspath(w) for w in wanted if w.endswith('.po')}
        names = {w.rstrip('/').split('/')[-1] for w in wanted if not w.endswith('.po')}
        files = [f for f in files if f in paths or describe(f) and describe(f)[3] in names]
        if not files:
            sys.exit('Nincs ilyen csomag: ' + ' '.join(wanted))

    blocked = load_blocked()
    if dist_mode and os.path.isdir(out):
        shutil.rmtree(out)
    packages, skipped = [], []
    # A WP-CLI nem rekurzív, csomagonként hívni pedig lassú: a .po-kat kötegekbe gyűjtjük (egy
    # kötegben minden fájlnév egyszer szerepel — pl. a complianz-gdpr és a complianz-gdpr-premium
    # ugyanazt a complianz-gdpr-hu_HU.po nevet használja), kötegenként egyszer fut a három parancs,
    # utána a termékek a csomag saját mappájába kerülnek: dist/<tone>/<plugins|themes>/<locale>/<mappa>/.
    batches = []
    for f in files:
        d = describe(f)
        if not d:
            skipped.append(os.path.relpath(f, ROOT))
            continue
        n = remove_blocked(f, blocked)
        if n:
            print('{} tiltott szöveg eltávolítva: {}'.format(n, os.path.relpath(f, ROOT)))
        if revision_date and update_revision_date(f):
            print('PO-Revision-Date frissítve: {}'.format(os.path.relpath(f, ROOT)))
        name = os.path.basename(f)
        batch = next((b for b in batches if name not in b), None)
        if batch is None:
            batch = {}
            batches.append(batch)
        batch[name] = (f, d)

    if not dist_mode:
        return build_in_place(batches, skipped)

    # 3. WP-CLI, kötegenként egy hívás parancsonként
    stage_root = os.path.join(out, '.stage')
    done = []
    for i, batch in enumerate(batches, 1):
        stage = os.path.join(stage_root, str(i))
        os.makedirs(stage)
        for name, (f, _) in batch.items():
            stage_po(f, os.path.join(stage, name))
        for cmd in (['i18n', 'make-mo', stage], ['i18n', 'make-php', stage],
                    ['i18n', 'make-json', stage, '--no-purge']):
            run_wp(cmd)
        produced = os.listdir(stage)
        for name, (f, d) in sorted(batch.items()):
            base = name[:-3]
            mine = sorted(p for p in produced
                          if p in (base + '.po', base + '.mo', base + '.l10n.php')
                          or (JSON_NAME.match(p) and JSON_NAME.match(p).group(1) == base))
            target = os.path.join(out, *d)
            os.makedirs(target)
            for p in mine:
                shutil.move(os.path.join(stage, p), os.path.join(target, p))
            shutil.copy2(f, os.path.join(target, name))  # a csomagba az eredeti .po kerül
            done.append((f, d, target, mine))
        print('{}. köteg: {} .po kész'.format(i, len(batch)))
    shutil.rmtree(stage_root, ignore_errors=True)

    # 4. csomagonkénti fájllista és statisztika
    totals = collections.Counter()
    per_tone = collections.defaultdict(collections.Counter)
    manifest = []
    for f, (tone, typ, locale, folder), target, mine in sorted(done):
        po = polib.pofile(f, wrapwidth=0)
        entries, translated, en_chars, hu_chars = po_stats(po)
        meta = po.metadata
        pkg = {
            'tone': tone, 'type': typ[:-1], 'locale': locale, 'slug': folder,
            'name': meta.get('X-Plugin-Name', ''), 'version': meta.get('X-Plugin-Version', ''),
            'po_revision_date': meta.get('PO-Revision-Date', ''),
            'entries': entries, 'translated': translated,
            'coverage': round(translated / entries * 100, 1) if entries else 0.0,
        }
        packages.append(pkg)
        manifest.append(dict(pkg, dir=os.path.relpath(target, out), files=mine))
        for k, v in (('files', 1), ('entries', entries), ('translated', translated),
                     ('english_chars', en_chars), ('hungarian_chars', hu_chars)):
            totals[k] += v
            per_tone[tone][k] += v
        totals[typ] += 1

    def summary(c):
        return {'files': c['files'], 'entries': c['entries'], 'translated': c['translated'],
                'coverage': round(c['translated'] / c['entries'] * 100, 1) if c['entries'] else 0.0,
                'english_chars': c['english_chars'], 'hungarian_chars': c['hungarian_chars']}

    stats = dict(summary(totals), plugins=totals['plugins'], themes=totals['themes'],
                 generated=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                 by_tone={t: summary(c) for t, c in sorted(per_tone.items())},
                 packages=packages)
    with open(os.path.join(out, 'stats.json'), 'w', encoding='utf-8') as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out, 'manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)

    for s in skipped:
        print('kihagyva (nem <tone>/<plugins|themes>/<locale>/<mappa>/ alatt): ' + s)
    print('Kész: {} .po, {} bejegyzés, {} lefordítva ({}%). Kimenet: {}'.format(
        stats['files'], stats['entries'], stats['translated'], stats['coverage'], os.path.relpath(out, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
