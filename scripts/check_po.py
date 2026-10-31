#!/usr/bin/env python3
r"""A .po fájlok ellenőrzése: msgfmt -c, helyőrzők, kötelező fejlécek, fájlnevek, szótár.

Hibák (kilépési kód 1):
  msgfmt     a `msgfmt -c` hibái
  helyorzo   a msgid és a msgstr helyőrzői nem egyeznek (printf: %s, %1$s, %d;
             {név}; HTML-címkék) — a sorrend számít, ha nincs pozíció (%1$s)
  fejlec     hiányzik vagy üres az X-Plugin-Name / X-Plugin-Version / X-Plugin-Tone,
             vagy a Tone nem egyezik a mappával (formal / informal)
  fajlnev    az lw-translate fájlnév-szabálya sérül: a csomag mappája
             <tone>/<plugins|themes>/<locale>/<mappa>/, benne csak
             ^<mappa>-<locale>(\.mo|\.po|-[0-9a-f]{32}\.json)$ (és a gitben nem szereplő
             <mappa>-<locale>.l10n.php, .gitkeep); a .po mellől nem hiányozhat a
             <mappa>-<locale>.mo; .mo vagy .json nem lehet .po nélkül

Figyelmeztetés (nem hiba):
  szotar     egy `translation-glossary.json` tétel (csak a "forras": "kezi" tételek)
             angol kifejezése a msgid-ben van, de a magyar alak nincs a msgstr-ben
             (csak hu_HU fájloknál)

Használat:
  scripts/check_po.py <fájl.po>…              a megadott fájlok
  scripts/check_po.py --all                   minden .po a formal/ és informal/ alatt
  scripts/check_po.py --changed-since <ref>   a <ref> óta változott csomagmappák (git diff; egy
                                              .mo vagy .json változása is a csomag ellenőrzését jelenti)
  --glossary <fájl>                           más szótárfájl (alapból: translation-glossary.json)
  --no-warnings                               a szótár-figyelmeztetések kihagyása
  --summary                                   csak az összesítés, soronkénti lista nélkül

Függőség: polib (pip install polib), msgfmt (gettext).
"""
import collections
import json
import os
import re
import shutil
import subprocess
import sys

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
REQUIRED_HEADERS = ('X-Plugin-Name', 'X-Plugin-Version', 'X-Plugin-Tone')

# printf: %s, %d, %1$s, %05.2f — a szóköz-flaget szándékosan kihagyjuk („100% of” ne legyen helyőrző)
PRINTF = re.compile(r"%(?:(\d+)\$)?([-+0#']*)(\d*)(?:\.\d+)?([bcdeEfFgGosuxX])")
BRACE = re.compile(r'\{[A-Za-z0-9_]+\}')
TAG = re.compile(r'<(/?)([A-Za-z][A-Za-z0-9]*)\b[^<>]*>')
HTML_TAGS = set('''a abbr b blockquote br button code del details div em h1 h2 h3 h4 h5 h6 hr i img input
    ins kbd label li mark ol p pre q s small span strike strong sub summary sup table tbody td th thead
    tr u ul'''.split())


def printf_tokens(text):
    """A valódi printf-helyőrzők: (pozíció vagy None, típus).

    Kimarad, ami a magyar szövegben nem helyőrző: „30%-os”, „100%-ban” (kötőjel-flag
    szélesség nélkül), és a „%1kattintson%2” típusú, nem printf-jelölés (szélesség pozíció
    nélkül, utána rögtön betű).
    """
    for m in PRINTF.finditer(text):
        pos, flags, width, conv = m.group(1), m.group(2), m.group(3), m.group(4)
        if '-' in flags and not width:
            continue
        if width and not pos and text[m.end():m.end() + 1].isalpha():
            continue
        yield (int(pos) if pos else None), conv


def placeholders(text):
    """A szöveg helyőrzőinek multihalmaza.

    A printf-helyőrzők (pozíció, típus) párként számítanak: a %s %s és a %2$s %1$s egyezik,
    a %s %d és a %d %s nem. A HTML-címkéknél (csak az ismert HTML-elemek) a név és a
    nyitó/záró jelleg számít, az attribútum (pl. title="…") fordítható. A kiírásban a printf
    helyőrzők pozícióval szerepelnek (a %s első helyen %1$s).
    """
    text = text.replace('%%', '')
    out = collections.Counter()
    seq = 0
    for pos, conv in printf_tokens(text):
        if pos is None:
            seq += 1
            pos = seq
        out['%{}${}'.format(pos, conv)] += 1
    for m in BRACE.finditer(text):
        out[m.group(0)] += 1
    for m in TAG.finditer(text):
        if m.group(2).lower() not in HTML_TAGS:
            continue
        out['<{}{}>'.format(m.group(1), m.group(2).lower())] += 1  # <br> = <br/> = <br />
    return out


def fmt_ph(counter):
    return ' '.join(sorted(counter.elements())) or '(nincs)'


def tone_of(path):
    rel = os.path.relpath(os.path.abspath(path), ROOT).split(os.sep)
    return rel[0] if rel and rel[0] in TONES else None


def locale_of(path):
    rel = os.path.relpath(os.path.abspath(path), ROOT).split(os.sep)
    return rel[2] if len(rel) >= 4 else None


def load_glossary(path):
    if not path or not os.path.exists(path):
        return []
    data = json.load(open(path, encoding='utf-8')).get('glossary', {})
    terms = []
    for en, v in data.items():
        if not isinstance(v, dict) or v.get('forras') != 'kezi' or not v.get('hu'):
            continue
        # a csupa nagybetűs rövidítések (API, URL, ID) kis- és nagybetű-érzékenyen
        flags = 0 if en.isupper() else re.IGNORECASE
        rx = re.compile(r'(?<![A-Za-z0-9])' + re.escape(en) + r'(?![A-Za-z0-9])', flags)
        terms.append((en, v['hu'], rx))
    return terms


def run_msgfmt(path):
    r = subprocess.run(['msgfmt', '-c', '-o', os.devnull, path], capture_output=True, text=True)
    if r.returncode == 0:
        return []
    errs = []
    for line in r.stderr.splitlines():
        line = line.strip()
        # az összesítő sort („msgfmt: found N fatal errors”) nem számoljuk külön
        if not line or line.startswith('msgfmt:'):
            continue
        errs.append(line[len(path) + 1:] if line.startswith(path + ':') else line)
    return errs or ['msgfmt kilépési kód {}'.format(r.returncode)]


PRINTF_ARG = re.compile(r'%(?:(\d+)\$)?[-+ #0]*\d*(?:\.\d+)?[bcdeEfFgGosuxX]')
SINGULAR_ONLY = re.compile(r"as in 'msgstr\[0\]', doesn't exist in 'msgid_plural'")


def singular_only_arg(po, err):
    """Igaz, ha a hiba csak az, hogy a msgstr[0] az egyes számú msgid helyőrzőjét használja, a többes számú pedig
    másikat (pl. "an %1$s" / "%2$s"): a forrás így tervezte, a fordítás helyes, futáskor nem okoz hibát."""
    typ, line, msg = err
    if typ != 'msgfmt' or not SINGULAR_ONLY.search(msg):
        return False
    entry = None
    for e in po:
        if e.linenum <= line:
            entry = e
        else:
            break
    if entry is None or not entry.msgid_plural:
        return False
    args = lambda s: {m.group(1) or str(i) for i, m in enumerate(PRINTF_ARG.finditer(s or ''), 1)}
    return args(entry.msgstr_plural.get(0)) <= args(entry.msgid)


def check_file(path, glossary, warnings=True):
    errors, warns = [], []  # (típus, sor, üzenet)
    for e in run_msgfmt(path):
        m = re.match(r'(\d+):\s*(.*)', e)
        errors.append(('msgfmt', int(m.group(1)) if m else 0, m.group(2) if m else e))

    try:
        po = polib.pofile(path, wrapwidth=0)
    except Exception as ex:  # a msgfmt már jelezte; a polib nem tud tovább menni
        errors.append(('msgfmt', 0, 'a fájl nem olvasható: {}'.format(ex)))
        return errors, warns
    errors = [e for e in errors if not singular_only_arg(po, e)]
    # ha a végzetes msgfmt-hibák mind ilyenek voltak, a fejléc-figyelmeztetések sem hibák (a msgfmt csak a
    # nem nulla kilépési kód miatt írta ki őket)
    if not any(t == 'msgfmt' and not m.startswith('warning:') for t, _, m in errors):
        errors = [e for e in errors if not (e[0] == 'msgfmt' and e[2].startswith('warning:'))]

    meta = po.metadata
    for h in REQUIRED_HEADERS:
        if not meta.get(h, '').strip():
            errors.append(('fejlec', 1, 'hiányzik vagy üres: {}'.format(h)))
    tone = tone_of(path)
    have = meta.get('X-Plugin-Tone', '').strip()
    if tone and have and have != tone:
        errors.append(('fejlec', 1, 'X-Plugin-Tone: {} (a mappa szerint: {})'.format(have, tone)))

    check_glossary = warnings and glossary and locale_of(path) == 'hu_HU'
    for e in po:
        if e.obsolete or 'fuzzy' in e.flags or not e.msgid:
            continue
        if e.msgid_plural:
            allowed = [placeholders(e.msgid), placeholders(e.msgid_plural)]
            strs = [s for _, s in sorted(e.msgstr_plural.items()) if s]
        else:
            allowed = [placeholders(e.msgid)]
            strs = [e.msgstr] if e.msgstr else []
        for s in strs:
            got = placeholders(s)
            if got not in allowed:
                errors.append(('helyorzo', e.linenum, 'msgid: {} | msgstr: {} | {!r}'.format(
                    fmt_ph(allowed[-1] if e.msgid_plural else allowed[0]), fmt_ph(got), e.msgid[:80])))
        if check_glossary and strs:
            for en, hu, rx in glossary:
                if rx.search(e.msgid) and not any(hu.lower() in s.lower() for s in strs):
                    warns.append(('szotar', e.linenum, '{} = {} | {!r}'.format(en, hu, e.msgid[:80])))
    return errors, warns


KINDS = ('plugins', 'themes')
IGNORED_NAMES = ('.gitkeep', '.DS_Store')


def check_names(directory):
    """Az lw-translate fájlnév-szabálya egy mappára. A mappa a csomagmappa
    (<tone>/<plugins|themes>/<locale>/<mappa>), vagy bármely más mappa a formal/ és informal/
    alatt: ott a .gitkeep-en kívül nem lehet fájl. Visszaad: [(fájl relatív útja, üzenet)]."""
    errors = []
    rel = os.path.relpath(directory, ROOT)
    parts = rel.split(os.sep)
    try:
        names = sorted(n for n in os.listdir(directory)
                       if os.path.isfile(os.path.join(directory, n)) and n not in IGNORED_NAMES)
    except FileNotFoundError:
        return errors
    if not names:
        return errors
    if len(parts) != 4 or parts[0] not in TONES or parts[1] not in KINDS:
        for n in names:
            errors.append((os.path.join(rel, n), 'a fájl nem <tone>/<plugins|themes>/<locale>/<mappa>/ alatt van'))
        return errors
    folder, locale = parts[3], parts[2]
    base = re.escape('{}-{}'.format(folder, locale))
    rule = re.compile(r'^' + base + r'(\.mo|\.po|-[0-9a-f]{32}\.json)$')
    local_only = re.compile(r'^' + base + r'\.l10n\.php$')  # a gitben nincs, helyben megmaradhat
    expected = '{}-{}'.format(folder, locale)
    for n in names:
        if not rule.match(n) and not local_only.match(n):
            errors.append((os.path.join(rel, n), 'a fájlnév nem illik a szabályra: '
                           '^{0}(\\.mo|\\.po|-[0-9a-f]{{32}}\\.json)$'.format(expected)))
    pos = [n for n in names if n.endswith('.po')]
    if pos and expected + '.mo' not in names:
        errors.append((os.path.join(rel, pos[0]), 'hiányzik a .po mellől: {}.mo (scripts/build.py)'.format(expected)))
    if not pos and any(n.endswith(('.mo', '.json')) for n in names):
        errors.append((os.path.join(rel, names[0]), 'a mappában nincs .po, de van .mo vagy .json'))
    return errors


def all_dirs():
    out = []
    for tone in TONES:
        for dirpath, _, _ in os.walk(os.path.join(ROOT, tone)):
            out.append(dirpath)
    return sorted(out)


def all_po_files():
    out = []
    for tone in TONES:
        for dirpath, _, files in os.walk(os.path.join(ROOT, tone)):
            out += [os.path.join(dirpath, f) for f in files if f.endswith('.po')]
    return sorted(out)


def changed_dirs(ref):
    """A <ref> óta változott (törölt fájlt is beleértve) mappák a formal/ és informal/ alatt."""
    if subprocess.run(['git', 'cat-file', '-e', ref + '^{commit}'], cwd=ROOT, capture_output=True).returncode:
        # force-push után a push előtti commit már nincs meg: az utolsó commithoz mérünk
        print('figyelmeztetés: {} nem található, a HEAD~1 óta változott mappákat nézem'.format(ref))
        ref = 'HEAD~1'
    r = subprocess.run(['git', 'diff', '--name-status', '--diff-filter=ACMRD', ref, '--', 'formal', 'informal'],
                       cwd=ROOT, capture_output=True, text=True, check=True)
    utak = []
    for sor in r.stdout.splitlines():
        allapot, *nevek = sor.split('\t')
        # A .l10n.php nincs a gitben (a release és az lw-translate maga készíti): a törlése nem változás.
        if allapot == 'D' and nevek[0].endswith('.l10n.php'):
            continue
        utak += nevek
    return sorted({os.path.dirname(os.path.join(ROOT, f)) for f in utak})


def po_files_in(directory):
    try:
        return [os.path.join(directory, n) for n in sorted(os.listdir(directory)) if n.endswith('.po')]
    except FileNotFoundError:
        return []


def main(argv):
    args = list(argv)
    glossary_path = os.path.join(ROOT, 'translation-glossary.json')
    warnings, summary_only, files, dirs = True, False, [], []
    while args:
        a = args.pop(0)
        if a == '--all':
            files += all_po_files()
            dirs += all_dirs()
        elif a == '--changed-since':
            changed = changed_dirs(args.pop(0))
            dirs += changed
            for d in changed:
                files += po_files_in(d)
        elif a == '--glossary':
            glossary_path = args.pop(0)
        elif a == '--no-warnings':
            warnings = False
        elif a == '--summary':
            summary_only = True
        elif a in ('-h', '--help'):
            print(__doc__)
            return 0
        else:
            files.append(os.path.abspath(a))
    files = sorted(set(files))
    dirs = sorted(set(dirs) | {os.path.dirname(f) for f in files})
    name_errors = [e for d in dirs for e in check_names(d)]
    if not files and not name_errors:
        print('Nincs ellenőrizendő .po fájl.')
        return 0
    if not shutil.which('msgfmt'):
        sys.exit('Nem található a msgfmt (gettext): telepítsd, vagy tedd a PATH-ba.')

    glossary = load_glossary(glossary_path) if warnings else []
    n_err = collections.Counter()
    n_warn = 0
    bad_files = collections.Counter()
    n_bad = 0
    for f in files:
        rel = os.path.relpath(f, ROOT)
        errors, warns = check_file(f, glossary, warnings)
        for typ, line, msg in errors:
            n_err[typ] += 1
            if not summary_only:
                print('{}:{}: HIBA [{}] {}'.format(rel, line, typ, msg))
        for typ in {t for t, _, _ in errors}:
            bad_files[typ] += 1
        n_bad += 1 if errors else 0
        for typ, line, msg in warns:
            n_warn += 1
            if not summary_only:
                print('{}:{}: figyelmeztetés [{}] {}'.format(rel, line, typ, msg))

    name_files = {f for f, _ in name_errors}
    for f, msg in name_errors:
        n_err['fajlnev'] += 1
        if not summary_only:
            print('{}: HIBA [fajlnev] {}'.format(f, msg))
    bad_files['fajlnev'] = len(name_files)

    total = sum(n_err.values())
    print('\nEllenőrizve: {} .po fájl, {} mappa. Hiba: {} ({} .po fájlban, {} fájlnév-hiba), figyelmeztetés: {}.'.format(
        len(files), len(dirs), total, n_bad, n_err['fajlnev'], n_warn))
    for typ in ('msgfmt', 'helyorzo', 'fejlec', 'fajlnev'):
        if n_err[typ]:
            print('  {:<9} {:>6} hiba {:>4} fájlban'.format(typ, n_err[typ], bad_files[typ]))
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
