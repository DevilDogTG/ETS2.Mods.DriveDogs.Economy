#!/usr/bin/env python
"""Generate DriveDogs Economy's driver pool: names 355-999 plus their portraits.

Vanilla caps the company at 355 hireable drivers because that is how many names
locale/en_gb/driver_names.sii defines (name[0]..name[354]). Each index N needs a portrait,
/material/ui/driver/N.mat and /material/ui/driver/small/N.mat (SCS's own comment in the file).
Recruitment agencies run dry at that count no matter how many garage slots are free.

This writes a whole-file copy of the vanilla driver_names.sii with every vanilla line untouched
(existing saves keep their drivers) and new names appended up to --total. Each new driver reuses
a vanilla portrait of the same gender (vanilla prefixes female names with '+'), cycling through
the vanilla faces so repeats spread evenly. No new art.

Vanilla ships the list only under en_gb; other languages fall back to it. The same file is also
written under every locale in OUT_LOCALES, so a language that the player uses doesn't depend on
that fallback (Av_Mark's "Additional AI Drivers" works only in English (US), the default
English variant).

Names follow vanilla's style ("First L."), drawn from first names across the map's countries,
about one in four female as in vanilla, and never repeat a vanilla or another new name.
Output is deterministic: no randomness, same input gives the same files.

Usage:
    python tools/generate_driver_pool.py --vanilla-root <extracted base root, e.g. ...\\base\\1.62>
"""
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'src'
NAMES_REL = Path('locale/en_gb/driver_names.sii')
# Identical copies of the list; en_gb is vanilla's own location and must stay first.
OUT_LOCALES = ('en_gb', 'en_us')
PORTRAIT_REL = Path('material/ui/driver')

DEFAULT_TOTAL = 1000

# Every fourth new driver is female: 25%, as in vanilla (88 of 355).
FEMALE_EVERY = 4

# Surname initials, cycled per first name. X/Y/Q left out: rare as European surname initials.
INITIALS = 'SMBPHKDVRLTFAJCGNWZOEI'

# First names per region of the map. Regions are interleaved so neighbouring indexes mix countries.
MALE = [
    # UK / Ireland
    ['Oliver', 'Harry', 'Jack', 'Charlie', 'Thomas', 'James', 'Callum', 'Liam', 'Connor', 'Declan',
     'Owen', 'Rhys', 'Stuart', 'Alistair', 'Graham', 'Neil', 'Gavin', 'Colin'],
    # Germany / Austria / Switzerland
    ['Lukas', 'Jonas', 'Felix', 'Moritz', 'Florian', 'Stefan', 'Matthias', 'Jürgen', 'Dieter', 'Uwe',
     'Torsten', 'Markus', 'Andreas', 'Wolfgang', 'Klaus', 'Holger', 'Reto', 'Urs'],
    # France / Belgium / Luxembourg
    ['Julien', 'Mathieu', 'Nicolas', 'Antoine', 'Guillaume', 'Thierry', 'Olivier', 'Laurent', 'Yannick',
     'Sébastien', 'Benoît', 'Cédric', 'Arnaud', 'Didier', 'Gilles', 'Rémi', 'Pierre', 'Hugo'],
    # Netherlands
    ['Daan', 'Sem', 'Bram', 'Jeroen', 'Joost', 'Sander', 'Ruud', 'Wouter', 'Bas', 'Thijs', 'Pieter',
     'Kees', 'Jasper', 'Niels'],
    # Italy
    ['Luca', 'Marco', 'Giovanni', 'Alessandro', 'Davide', 'Matteo', 'Stefano', 'Andrea', 'Fabio',
     'Riccardo', 'Paolo', 'Giuseppe', 'Salvatore', 'Lorenzo', 'Enrico', 'Massimo'],
    # Spain / Portugal
    ['Javier', 'Alejandro', 'Sergio', 'Pablo', 'Álvaro', 'Iker', 'Raúl', 'Diego', 'Jorge', 'Rubén',
     'João', 'Tiago', 'Rui', 'Nuno', 'Gonçalo', 'Duarte', 'Paulo', 'Ricardo'],
    # Poland
    ['Piotr', 'Krzysztof', 'Tomasz', 'Paweł', 'Michał', 'Marcin', 'Łukasz', 'Grzegorz', 'Kamil',
     'Bartosz', 'Rafał', 'Dariusz', 'Zbigniew', 'Szymon'],
    # Czechia / Slovakia
    ['Petr', 'Martin', 'Pavel', 'Ondřej', 'Radek', 'Miroslav', 'Lukáš', 'Zdeněk', 'Milan', 'Roman',
     'Štefan', 'Juraj', 'Peter', 'Marek'],
    # Hungary / Romania / Bulgaria
    ['Bence', 'Gábor', 'Zoltán', 'László', 'Balázs', 'Attila', 'Andrei', 'Mihai', 'Bogdan', 'Cristian',
     'Florin', 'Ionuț', 'Georgi', 'Dimitar', 'Ivaylo', 'Stoyan', 'Nikolay', 'Hristo'],
    # Western Balkans
    ['Luka', 'Ivan', 'Marko', 'Nikola', 'Stefan', 'Miloš', 'Dragan', 'Goran', 'Zoran', 'Tomislav',
     'Ante', 'Damir', 'Emir', 'Edin', 'Arben', 'Besnik', 'Blerim', 'Aleksandar'],
    # Baltics / Finland
    ['Mantas', 'Tomas', 'Darius', 'Andris', 'Jānis', 'Kārlis', 'Rihards', 'Kaspar', 'Rasmus', 'Mihkel',
     'Tõnis', 'Juha', 'Mikko', 'Jukka', 'Antti', 'Pekka', 'Ville', 'Eero'],
    # Scandinavia / Iceland
    ['Lars', 'Anders', 'Erik', 'Henrik', 'Magnus', 'Nils', 'Sven', 'Bjørn', 'Rune', 'Kjetil', 'Mads',
     'Søren', 'Jesper', 'Gunnar', 'Einar', 'Sigurður', 'Ólafur', 'Gísli'],
    # Greece / Turkey
    ['Giorgos', 'Nikos', 'Kostas', 'Dimitris', 'Yannis', 'Vasilis', 'Christos', 'Panagiotis', 'Mehmet',
     'Emre', 'Burak', 'Murat', 'Hakan', 'Serkan', 'Kemal', 'Onur'],
    # Russia / Ukraine / Belarus
    ['Dmitri', 'Sergei', 'Alexei', 'Mikhail', 'Pavel', 'Yuri', 'Oleg', 'Igor', 'Vadim', 'Taras',
     'Bohdan', 'Mykola', 'Andriy', 'Oleksandr', 'Artem', 'Denis'],
]

FEMALE = [
    # UK / Ireland
    ['Charlotte', 'Amelia', 'Olivia', 'Hannah', 'Niamh', 'Aoife', 'Siobhan', 'Fiona', 'Rachel'],
    # Germany / Austria / Switzerland
    ['Anna', 'Lena', 'Sabine', 'Petra', 'Katrin', 'Julia', 'Ursula', 'Heike', 'Annika'],
    # France / Belgium
    ['Camille', 'Chloé', 'Manon', 'Élodie', 'Céline', 'Aurélie', 'Nathalie', 'Margaux'],
    # Netherlands
    ['Sanne', 'Fleur', 'Anouk', 'Lieke', 'Femke', 'Marieke'],
    # Italy
    ['Giulia', 'Chiara', 'Francesca', 'Valentina', 'Elena', 'Federica', 'Silvia'],
    # Spain / Portugal
    ['Lucía', 'Carmen', 'Marta', 'Paula', 'Inês', 'Beatriz', 'Mariana', 'Joana'],
    # Poland
    ['Agnieszka', 'Katarzyna', 'Magdalena', 'Joanna', 'Małgorzata', 'Ewa', 'Zofia'],
    # Czechia / Slovakia
    ['Tereza', 'Lucie', 'Petra', 'Kateřina', 'Veronika', 'Zuzana', 'Lenka'],
    # Hungary / Romania / Bulgaria
    ['Eszter', 'Réka', 'Zsófia', 'Ioana', 'Andreea', 'Elena', 'Desislava', 'Mariya', 'Gergana'],
    # Western Balkans
    ['Ana', 'Ivana', 'Maja', 'Jelena', 'Milica', 'Lejla', 'Elira', 'Marija'],
    # Baltics / Finland
    ['Rūta', 'Ieva', 'Laura', 'Līga', 'Kristiina', 'Kadri', 'Aino', 'Sanna', 'Riikka'],
    # Scandinavia / Iceland
    ['Ingrid', 'Astrid', 'Sofie', 'Karin', 'Maja', 'Freja', 'Sigrid', 'Guðrún', 'Helga'],
    # Greece / Turkey
    ['Eleni', 'Katerina', 'Sofia', 'Despina', 'Zeynep', 'Elif', 'Ayşe', 'Merve'],
    # Russia / Ukraine / Belarus
    ['Natalia', 'Olga', 'Tatiana', 'Svetlana', 'Oksana', 'Iryna', 'Yulia', 'Daria'],
]

NAME_LINE_RE = re.compile(r'^\s*name\[(\d+)\]:\s*"([^"]*)"', re.MULTILINE)
UNIT_END_RE = re.compile(r'\n\}\s*\n\}\s*$')

MAT_TEMPLATE = '''effect : "ui.rfx" {{
\ttexture : "texture" {{
\t\tsource : "{source}"
\t\tu_address : clamp
\t\tv_address : clamp
\t\tmip_filter : none
\t}}
}}
'''


def fail(msg):
    sys.exit(f'error: {msg}')


def interleave(regions):
    """One name per region in turn, so consecutive drivers come from different countries."""
    out, seen = [], set()
    for i in range(max(len(r) for r in regions)):
        for region in regions:
            if i < len(region) and region[i] not in seen:
                seen.add(region[i])
                out.append(region[i])
    return out


def name_stream(first_names, taken):
    """Unique "First L." names: every first name per round, the initial shifting each round."""
    for rnd in range(len(INITIALS)):
        for idx, first in enumerate(first_names):
            name = f'{first} {INITIALS[(idx * 7 + rnd * 3) % len(INITIALS)]}.'
            if name not in taken:
                taken.add(name)
                yield name
    fail('ran out of unique names; add first names')


def read_vanilla(root: Path):
    path = root / NAMES_REL
    if not path.is_file():
        fail(f'{path} not found (extract locale.scs into the vanilla root)')
    text = path.read_text(encoding='utf-8-sig')
    entries = [(int(i), n) for i, n in NAME_LINE_RE.findall(text)]
    indexes = [i for i, _ in entries]
    if indexes != list(range(len(entries))):
        fail(f'vanilla name[] indexes are not contiguous from 0 ({len(entries)} entries)')
    if not UNIT_END_RE.search(text):
        fail('vanilla driver_names.sii does not end with the unit and SiiNunit braces')
    for i in indexes:
        for rel in (PORTRAIT_REL / f'{i}.tobj', PORTRAIT_REL / 'small' / f'{i}.tobj'):
            if not (root / rel).is_file():
                fail(f'vanilla portrait {rel} missing for name[{i}]')
    return text, [n for _, n in entries]


def build(vanilla_names, total):
    start = len(vanilla_names)
    if total <= start:
        fail(f'--total {total} must exceed the vanilla count {start}')
    male_faces = [i for i, n in enumerate(vanilla_names) if not n.startswith('+')]
    female_faces = [i for i, n in enumerate(vanilla_names) if n.startswith('+')]
    taken = {n.lstrip('+') for n in vanilla_names}
    males, females = name_stream(interleave(MALE), taken), name_stream(interleave(FEMALE), taken)
    drivers, used = [], {'m': 0, 'f': 0}
    for index in range(start, total):
        if (index - start) % FEMALE_EVERY == FEMALE_EVERY - 1:
            face = female_faces[used['f'] % len(female_faces)]
            used['f'] += 1
            drivers.append((index, '+' + next(females), face))
        else:
            face = male_faces[used['m'] % len(male_faces)]
            used['m'] += 1
            drivers.append((index, next(males), face))
    return drivers


def write(vanilla_text, vanilla_count, drivers, out: Path):
    total = drivers[-1][0] + 1
    block = [
        '',
        f'# DDE: name[{vanilla_count}]..name[{total - 1}] added by DriveDogs Economy (vanilla stops at',
        f'# name[{vanilla_count - 1}], which caps the company at {vanilla_count} drivers). Generated by',
        '# tools/generate_driver_pool.py; each portrait reuses a vanilla face of the same gender.',
    ]
    block += [f'\tname[{i}]: "{name}"' for i, name, _ in drivers]
    m = UNIT_END_RE.search(vanilla_text)
    text = vanilla_text[:m.start()] + '\n' + '\n'.join(block) + vanilla_text[m.start():]
    for locale in OUT_LOCALES:
        names_path = out / 'locale' / locale / NAMES_REL.name
        names_path.parent.mkdir(parents=True, exist_ok=True)
        names_path.write_text(text, encoding='utf-8-sig', newline='\n')

    wanted = {f'{i}.mat' for i, _, _ in drivers}
    for sub, prefix in ((PORTRAIT_REL, '/material/ui/driver'), (PORTRAIT_REL / 'small', '/material/ui/driver/small')):
        folder = out / sub
        folder.mkdir(parents=True, exist_ok=True)
        for stale in folder.glob('*.mat'):  # this folder only holds generated portraits
            if stale.name not in wanted and stale.stem.isdigit() and int(stale.stem) >= vanilla_count:
                stale.unlink()
        for i, _, face in drivers:
            (folder / f'{i}.mat').write_text(MAT_TEMPLATE.format(source=f'{prefix}/{face}.tobj'),
                                             encoding='ascii', newline='\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--vanilla-root', required=True, type=Path,
                    help='extracted base game root holding locale/ and material/')
    ap.add_argument('--total', type=int, default=DEFAULT_TOTAL, help='drivers in the pool, vanilla included')
    ap.add_argument('--out', type=Path, default=SRC, help='mod source root (default: src/)')
    args = ap.parse_args()

    vanilla_text, vanilla_names = read_vanilla(args.vanilla_root)
    drivers = build(vanilla_names, args.total)
    write(vanilla_text, len(vanilla_names), drivers, args.out)
    female = sum(1 for _, n, _ in drivers if n.startswith('+'))
    print(f'vanilla {len(vanilla_names)} drivers; added {len(drivers)} '
          f'(name[{drivers[0][0]}]..name[{drivers[-1][0]}], {female} female) -> {args.out}')


if __name__ == '__main__':
    main()
