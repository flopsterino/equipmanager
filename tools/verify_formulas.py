#!/usr/bin/env python3
"""Read every formula in the sources and report what cannot work.

Each rule here was written after a bug that shipped, so none of them is
hypothetical:

  UNKNOWN REF   a formula names a control that does not exist on its screen.
                Studio reports this as a red cross; the build does not.
  DUPLICATE     two controls on one screen share a name.
  DEAD TAP      a gallery row nothing responds to: the gallery's OnSelect is
                false and no child has one either.
  WITH SEMI     a ';' chain inside With(), whose body is a single expression.
                The formula does not parse, and Power Apps answers an
                unparseable OnSelect by silently doing nothing.
  PATCH RECORD  Patch() given a record held in a variable. A record loses its
                schema on the way into a variable, and Patch rejects it as
                "a Record value, but of a different schema".
  QUOTED COL    a column name in quotes where Power Fx wants an identifier.
  ONE ROW ONLY  Visible: =ThisItem.IsSelected. The browse gallery template uses
                this on the rectangle that highlights the selected row, and
                every rectangle in this app was copied from it - so dividers,
                calendar cells, timeline dots and colour strips all drew on one
                row and nowhere else. This app highlights nothing by selection;
                if it ever does, that rectangle gets a name saying so.
"""
import glob, os, re, sys
import yaml

COLUMN_ARG_FUNCS = ('Ungroup', 'GroupBy', 'AddColumns', 'DropColumns',
                    'ShowColumns', 'RenameColumns', 'SortByColumns')


def strip_noise(txt):
    """Blank out string bodies and comments, strings first so // inside one survives."""
    out, i, n = [], 0, len(txt)
    while i < n:
        c = txt[i]
        if c == '"':
            out.append(' ')
            i += 1
            while i < n and txt[i] != '"':
                out.append(' ')
                i += 1
            i += 1
            out.append(' ')
        elif c == '/' and i + 1 < n and txt[i + 1] == '/':
            while i < n and txt[i] != '\n':
                out.append(' ')
                i += 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def collect(node, out, gal=None):
    for entry in node or []:
        for name, body in entry.items():
            if not isinstance(body, dict):
                continue
            kind = (body.get('Control') or '').split('@')[0]
            out.append((name, kind, gal, body.get('Properties') or {}))
            collect(body.get('Children'), out, name if kind == 'Gallery' else gal)
    return out


def semis_in_with(expr):
    """A ';' at the top level of a With() body."""
    txt = strip_noise(str(expr))
    for m in re.finditer(r'\bWith\s*\(', txt):
        depth, i = 0, m.end() - 1
        while i < len(txt):
            if txt[i] == '(':
                depth += 1
            elif txt[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body, d = txt[m.end():i], 0
        for ch in body:
            if ch in '({[':
                d += 1
            elif ch in ')}]':
                d -= 1
            elif ch == ';' and d == 0:
                return True
    return False


def patch_variable_record(expr):
    """Patch(source, <bare variable>, ...) - the second argument must carry a schema."""
    txt = strip_noise(str(expr))
    bad = []
    for m in re.finditer(r'\bPatch\s*\(', txt):
        depth, i = 0, m.end() - 1
        while i < len(txt):
            if txt[i] == '(':
                depth += 1
            elif txt[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        args, d, cur, parts = txt[m.end():i], 0, '', []
        for ch in args:
            if ch in '({[':
                d += 1
            elif ch in ')}]':
                d -= 1
            if ch == ',' and d == 0:
                parts.append(cur); cur = ''
            else:
                cur += ch
        parts.append(cur)
        if len(parts) >= 2:
            rec = parts[1].strip()
            if re.fullmatch(r'var\w+', rec):
                bad.append(rec)
    return bad


def main():
    bad = 0
    for f in sorted(glob.glob('src/scr_*.pa.yaml')):
        doc = yaml.safe_load(open(f))
        for screen, sbody in doc['Screens'].items():
            ctrls = collect(sbody.get('Children'), [])
            names = [c[0] for c in ctrls]
            screens = {os.path.basename(p).replace('.pa.yaml', '')
                       for p in glob.glob('src/scr_*.pa.yaml')}
            known = set(names) | {screen} | screens

            for n in sorted(set(names)):
                if names.count(n) > 1:
                    print(f'  DUPLICATE     {screen}.{n} defined {names.count(n)}x')
                    bad += 1

            galleries = {n for n, k, g, p in ctrls if k == 'Gallery'}
            child_taps = {g for n, k, g, p in ctrls if g and p.get('OnSelect')
                          and str(p['OnSelect']).strip() not in ('=false', 'false')}

            for name, kind, gal, props in ctrls:
                for prop, val in props.items():
                    txt = strip_noise(str(val))
                    for ref in set(re.findall(r'\b([A-Za-z_]\w*)\s*\.', txt)):
                        if ref in ('Self', 'Parent', 'ThisItem', 'ThisRecord', 'App', 'Host'):
                            continue
                        if ref in known or not re.match(r'^(lbl|btn|con|gal|txt|drp|ico|rec|scr)', ref):
                            continue
                        print(f'  UNKNOWN REF   {screen}.{name}.{prop}: no control {ref!r}')
                        bad += 1
                    if semis_in_with(val):
                        print(f'  WITH SEMI     {screen}.{name}.{prop}')
                        bad += 1
                    for rec in patch_variable_record(val):
                        print(f'  PATCH RECORD  {screen}.{name}.{prop}: Patch(..., {rec}, ...)')
                        bad += 1
                    for fn in COLUMN_ARG_FUNCS:
                        if re.search(rf'\b{fn}\s*\((?:[^()]|\([^()]*\))*,\s*"', txt):
                            print(f'  QUOTED COL    {screen}.{name}.{prop}: {fn}()')
                            bad += 1

                vis = str(props.get('Visible', '')).strip()
                if vis == '=ThisItem.IsSelected':
                    print(f'  ONE ROW ONLY  {screen}.{name}: drawn on the selected row only')
                    bad += 1

                if kind == 'Gallery':
                    tap = str(props.get('OnSelect', '')).strip()
                    if tap in ('=false', 'false') and name not in child_taps:
                        print(f'  DEAD TAP      {screen}.{name}: rows respond to nothing')
                        bad += 1

    print(f'verify_formulas: {bad} problem(s)' if bad else 'verify_formulas: OK')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
