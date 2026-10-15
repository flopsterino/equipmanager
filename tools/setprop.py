#!/usr/bin/env python3
"""Set one property on one control in a .pa.yaml file, comments intact.

The sources carry the reasoning for nearly every unusual value as a comment
above it, so they are edited as lines rather than parsed and rewritten - a
round-trip through a YAML writer would throw all of that away.
"""
import re


def _control(lines, name):
    for i, l in enumerate(lines):
        if l.strip() == f'- {name}:':
            return i, len(l) - len(l.lstrip())
    raise KeyError(name)


def _props(lines, ci, cind):
    """First and last line of the control's own Properties block."""
    pind = cind + 4
    start = None
    for i in range(ci + 1, len(lines)):
        l = lines[i]
        if not l.strip():
            continue
        ind = len(l) - len(l.lstrip())
        if ind <= cind:
            break
        if ind == pind and l.strip() == 'Properties:':
            start = i + 1
            continue
        if start is not None and ind <= pind:
            return start, i, pind + 2
    if start is None:
        raise KeyError('no Properties block')
    return start, len(lines), pind + 2


def set_prop(path, control, prop, value, comment=None):
    lines = open(path).read().split('\n')
    ci, cind = _control(lines, control)
    lo, hi, pind = _props(lines, ci, cind)
    pad = ' ' * pind
    block = ([pad + '# ' + c for c in comment] if comment else []) + [f'{pad}{prop}: {value}']

    # Replace the property if it is already there, comments above it included.
    for i in range(lo, hi):
        l = lines[i]
        if len(l) - len(l.lstrip()) == pind and l.strip().startswith(f'{prop}:'):
            end = i + 1
            while end < hi and (not lines[end].strip() or
                                len(lines[end]) - len(lines[end].lstrip()) > pind):
                end += 1
            j = i
            while j - 1 >= lo and lines[j - 1].strip().startswith('#') and \
                    len(lines[j - 1]) - len(lines[j - 1].lstrip()) == pind:
                j -= 1
            lines[j:end] = block
            open(path, 'w').write('\n'.join(lines))
            return 'replaced'

    # Otherwise insert it in alphabetical order, where Studio would have put it.
    at = hi
    for i in range(lo, hi):
        l = lines[i]
        if len(l) - len(l.lstrip()) != pind or not l.strip() or l.strip().startswith('#'):
            continue
        if l.strip().split(':')[0] > prop:
            at = i
            break
    lines[at:at] = block
    open(path, 'w').write('\n'.join(lines))
    return 'inserted'


def put(path, control, prop, formula, comment=None):
    """Set a multi-line formula, indenting it to wherever the property sits.

    A block scalar's body has to sit deeper than its key, and how deep the key is
    depends on how far down the control tree it lives. Hard-coding that indent is
    how a formula ends up outside its own property and the file stops parsing.
    """
    import yaml
    lines = open(path).read().split('\n')
    ci, cind = _control(lines, control)
    _, _, pind = _props(lines, ci, cind)
    body = formula.strip('\n')
    if '\n' not in body:
        set_prop(path, control, prop, body, comment)
    else:
        ind = ' ' * (pind + 2)
        block = '|-\n' + '\n'.join((ind + l) if l.strip() else '' for l in body.split('\n'))
        set_prop(path, control, prop, block, comment)
    yaml.safe_load(open(path))          # fail here, not three edits later
