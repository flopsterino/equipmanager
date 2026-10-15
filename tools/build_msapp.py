#!/usr/bin/env python3
"""Write the formulas from src/*.pa.yaml into the app package.

Power Apps reads Controls/*.json when it imports a .msapp; Src/*.pa.yaml is the
readable mirror Studio keeps beside it. So a change has to land in the JSON, and
the YAML has to be carried along unchanged or the two disagree the next time the
app is opened in Studio.

This writes properties onto controls that already exist. Adding or removing a
control is not something it does - that is what Studio is for, and a package
assembled by hand with a control missing from one of the two representations
fails in ways that are hard to see.

    python3 tools/build_msapp.py            # -> build/Lab_Equipment_Hub.msapp
"""
import glob, json, os, re, shutil, sys, zipfile
import yaml

ORIG = 'msapp_original'
OUT = 'build/msapp'
PKG = 'build/Lab_Equipment_Hub.msapp'


def yaml_controls(node, out, path=()):
    """name -> {property: formula} for every control in one screen file."""
    for entry in node or []:
        for name, body in entry.items():
            if not isinstance(body, dict):
                continue
            props = body.get('Properties') or {}
            out[name] = {k: v for k, v in props.items()}
            yaml_controls(body.get('Children'), out, path + (name,))
    return out


def read_src():
    """Every control the sources define, keyed by screen."""
    screens = {}
    for f in sorted(glob.glob('src/*.pa.yaml')):
        doc = yaml.safe_load(open(f))
        for key in ('Screens', 'App'):
            section = doc.get(key)
            if not section:
                continue
            if key == 'App':
                screens['App'] = {'App': section.get('Properties') or {}}
                continue
            for sname, sbody in section.items():
                ctrls = {sname: sbody.get('Properties') or {}}
                yaml_controls(sbody.get('Children'), ctrls)
                screens[sname] = ctrls
    return screens


def walk_json(c):
    yield c
    for k in c.get('Children') or []:
        yield from walk_json(k)


def strip(formula):
    """YAML writes =<formula>; the JSON holds the formula alone."""
    s = str(formula)
    return s[1:] if s.startswith('=') else s


def main():
    src = read_src()
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(ORIG, OUT)

    written = missing = 0
    unknown = []
    carried = set()
    for f in sorted(glob.glob(f'{OUT}/Controls/*.json')):
        doc = json.load(open(f))
        top = doc['TopParent']
        ctrls = src.get(top['Name'])
        if ctrls is None:
            continue
        seen = set()
        for node in walk_json(top):
            props = ctrls.get(node.get('Name'))
            if props is None:
                continue
            seen.add(node['Name'])
            # Layout properties of an auto-layout child live in DynamicProperties,
            # not in Rules. Both carry the same kind of rule record.
            rules = {r['Property']: r for r in node.get('Rules', [])}
            for dp in node.get('DynamicProperties') or []:
                if isinstance(dp.get('Rule'), dict):
                    rules.setdefault(dp['Rule']['Property'], dp['Rule'])
            for prop, val in props.items():
                if '.' in prop:
                    # A compound property such as Items.Value - the column a
                    # dropdown displays. Studio keeps that mapping in the control's
                    # own state, not as a rule, and the package already carries it.
                    # It is left alone rather than written, so changing one in the
                    # YAML has no effect; that is what the count below is for.
                    carried.add(f'{node["Name"]}.{prop}')
                    continue
                if prop in rules:
                    rules[prop]['InvariantScript'] = strip(val)
                    written += 1
                else:
                    # A property the control has no rule for. Studio writes a rule
                    # for every property it knows, so this is a name it does not
                    # recognise - reported rather than invented.
                    unknown.append(f'{top["Name"]}.{node["Name"]}.{prop}')
        for name in ctrls:
            if name not in seen and name != top['Name']:
                missing += 1
                unknown.append(f'{top["Name"]}.{name}: control not in the package')
        json.dump(doc, open(f, 'w'), indent=1)

    if unknown:
        for u in unknown[:40]:
            print('  UNKNOWN  ', u)
        print(f'{len(unknown)} property/control name(s) the package does not have')
        return 1

    # Carry the readable sources along, so Studio does not reopen a stale mirror.
    for f in glob.glob('src/*.pa.yaml'):
        shutil.copy(f, f'{OUT}/Src/{os.path.basename(f)}')

    os.makedirs(os.path.dirname(PKG), exist_ok=True)
    if os.path.exists(PKG):
        os.remove(PKG)
    # Zip entry names use backslashes, the way the original package does.
    with zipfile.ZipFile(PKG, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, OUT).replace('/', '\\')
                z.write(full, rel)
    if carried:
        print(f'{len(carried)} compound propert(ies) left to the package '
              f'(e.g. {sorted(carried)[0]})')
    size = os.path.getsize(PKG) / 1024
    print(f'wrote {PKG} {size:.1f} KB, {written} formula(s) over '
          f'{len(glob.glob(f"{OUT}/Controls/*.json"))} screens')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
