#!/usr/bin/env python3
"""Lift the app off a single white sheet onto a tinted page with white surfaces.

Everything used to be white on white, with light grey bars doing the work of
separating one section from the next. That is why it read as a form rather than
as an app: nothing was grouped, because nothing had an edge.

The page becomes a soft grey and the things that hold content become white, so
grouping comes from the surface itself. Which control gets which treatment
follows the naming this app already uses, so it holds on every screen and on any
screen width - no fixed positions are involved, only fills.

    con*Header   con*Actions   con*Footer   -> white, a bar that frames the page
    conFld*  con*Field                      -> white, a field sits on a surface
    gal*                                     -> white, a list is a surface
    con*Body                                 -> left alone, the page shows through
"""
import glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from setprop import set_prop
import yaml

PAGE = '=RGBA(244, 245, 247, 1)'
SURFACE = '=RGBA(255, 255, 255, 1)'

# Chip rows and other galleries that sit INSIDE a surface already. Painting them
# white again is harmless but pointless, and it hides a genuine mistake later.
SKIP = {
    'galCommDoneChips', 'galGroupChips', 'galSetupAddChosen', 'galBkAssetsChosen',
    'galSetupPersonResults', 'galHolderResults', 'galSetupSearch',
    'galBkAssetResults', 'galBkDeviceResults', 'galSetupAddResults',
    'galAssetResults', 'galEdPickDays', 'galPickDays',
}


def controls(node, out):
    for entry in node or []:
        for name, body in entry.items():
            if isinstance(body, dict):
                out.append((name, (body.get('Control') or '').split('@')[0]))
                controls(body.get('Children'), out)
    return out


def wants_surface(name, kind):
    if name in SKIP:
        return False
    if re.match(r'^con.*(Header|Actions|Footer)$', name):
        return True
    if name.startswith('conFld') or re.match(r'^con.*Field$', name):
        return True
    if kind == 'Gallery' and name.startswith('gal'):
        return True
    return False


def main(write=True):
    painted = pages = 0
    for path in sorted(glob.glob('src/scr_*.pa.yaml')):
        doc = yaml.safe_load(open(path))
        for sname, sbody in doc['Screens'].items():
            if write:
                set_prop(path, sname, 'Fill', PAGE) if False else None
            # The screen's own Fill is not a control line, so it is set directly.
            text = open(path).read()
            new = re.sub(rf'(\n      Fill: )=RGBA\(255, 255, 255, 1\)', rf'\1{PAGE[1:]}', text, count=1)
            if new != text and write:
                open(path, 'w').write(new)
                pages += 1
            for name, kind in controls(sbody.get('Children'), []):
                if wants_surface(name, kind) and write:
                    set_prop(path, name, 'Fill', SURFACE)
                    painted += 1
    print(f'{pages} page background(s), {painted} surface(s) painted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(write='--dry-run' not in sys.argv))
