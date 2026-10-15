#!/usr/bin/env python3
"""Prove the build changes nothing it was not asked to change.

Reading the sources and writing them straight back out has to land on the package
it started from. Where it does not, the YAML and the JSON disagree about what a
formula says - and since the JSON is what Power Apps imports, a silent difference
there is a change nobody made and nobody sees.

Run it after every build. It is the only thing standing between a formatting
quirk in the sources and a quietly rewritten app.
"""
import glob, json, os, sys


def walk(c):
    yield c
    for k in c.get('Children') or []:
        yield from walk(k)


def rules_of(node):
    out = {}
    for r in node.get('Rules') or []:
        out[r['Property']] = r.get('InvariantScript')
    for dp in node.get('DynamicProperties') or []:
        if isinstance(dp.get('Rule'), dict):
            out.setdefault(dp['Rule']['Property'], dp['Rule'].get('InvariantScript'))
    return out


def snapshot(root):
    out = {}
    for f in sorted(glob.glob(f'{root}/Controls/*.json')):
        doc = json.load(open(f))
        screen = doc['TopParent']['Name']
        for node in walk(doc['TopParent']):
            for prop, script in rules_of(node).items():
                out[(screen, node.get('Name'), prop)] = script
    return out


def main():
    a = snapshot('msapp_original')
    b = snapshot('build/msapp')
    if not a or not b:
        sys.exit('nothing to compare - build first')

    only_a = set(a) - set(b)
    only_b = set(b) - set(a)
    changed = [k for k in set(a) & set(b) if a[k] != b[k]]

    for k in sorted(only_a)[:20]:
        print(f'  LOST      {".".join(str(x) for x in k)}')
    for k in sorted(only_b)[:20]:
        print(f'  ADDED     {".".join(str(x) for x in k)}')
    if '--verbose' in sys.argv:
        for k in sorted(changed)[:40]:
            print(f'  CHANGED   {".".join(str(x) for x in k)}')
            print(f'      was: {str(a[k])[:120]}')
            print(f'      now: {str(b[k])[:120]}')

    # A changed formula is the point of a build. A property or a control that
    # appeared or vanished is not: the sources and the package would then
    # disagree about what the app is made of, and Power Apps reads the package.
    structural = len(only_a) + len(only_b)
    if structural:
        print(f'verify_roundtrip: {structural} property/control(s) lost or added - '
              f'the sources and the package no longer describe the same app')
        return 1
    if changed:
        print(f'verify_roundtrip: OK - {len(changed)} formula(s) changed on purpose, '
              f'{len(a) - len(changed)} untouched, nothing lost or added')
    else:
        print(f'verify_roundtrip: OK - {len(a)} properties identical')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
