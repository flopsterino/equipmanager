#!/usr/bin/env python3
"""Catch text that will not fit the box it was given.

Two rules, both learned from bugs that shipped.

A label's Height has to hold one line of its own font size plus its padding.
Size is in points and Height in pixels, so a line takes about Size * 1.6 px
(points to pixels is 4/3, default line height 1.2).

And inside a gallery row, a label that wraps needs room for TWO lines. Every row
in a gallery has the same height, so a label that wraps into a row sized for one
line renders its second line half inside and half outside - sliced through the
middle. The honest options are: give it the room, or say Wrap: =false and let it
truncate. This demands one of them.
"""
import glob, os, re, sys
import yaml

LINE_PX = 1.6


def nums(expr):
    """The numbers a property can evaluate to, ignoring breakpoint widths.

    A responsive size reads If(Parent.Width < 600, 10, 11); the 600 is a screen
    width being tested, not a font size.
    """
    txt = re.sub(r'[<>]=?\s*\d+(?:\.\d+)?', '', str(expr or ''))
    return [float(x) for x in re.findall(r'\d+(?:\.\d+)?', txt)]


def pad(props):
    return (max(nums(props.get('PaddingTop')) or [0]) +
            max(nums(props.get('PaddingBottom')) or [0]))


def collect(node, out, gal=None):
    for entry in node or []:
        for name, body in entry.items():
            if not isinstance(body, dict):
                continue
            kind = (body.get('Control') or '').split('@')[0]
            out.append((name, kind, gal, body.get('Properties') or {}))
            collect(body.get('Children'), out, name if kind == 'Gallery' else gal)
    return out


def check(screen, name, kind, gal, props):
    if not kind.startswith('Label'):
        return 0
    if str(props.get('Visible', '')).strip() == '=false':
        return 0
    size = max(nums(props.get('Size')) or [11.0])
    h = props.get('Height')
    if h is None:
        return 0
    hs = str(h)
    if 'Self.Size' in hs:
        mult = nums(hs.split('Self.Size')[1][:8])
        if mult and size * mult[0] < size * LINE_PX + pad(props):
            print(f'  CLIPPED  {screen}.{name}: Height = Size * {mult[0]:g} '
                  f'({size * mult[0]:.0f}px) under the {size * LINE_PX + pad(props):.0f}px one line needs')
            return 1
        return 0
    if 'Parent.' in hs or 'Self.' in hs:
        return 0                              # relative to its container, not judged here
    heights = nums(hs)
    if not heights:
        return 0
    bad = 0
    need_one = size * LINE_PX + pad(props)
    if min(heights) < need_one:
        print(f'  CLIPPED  {screen}.{name}: Height {min(heights):g}px under the '
              f'{need_one:.0f}px one line of size {size:g} needs')
        bad += 1
    elif gal and str(props.get('Wrap', '')).strip() != '=false':
        need_two = size * LINE_PX * 2 + pad(props)
        if min(heights) < need_two:
            print(f'  WRAPS    {screen}.{name}: in a gallery row, wraps, but Height '
                  f'{min(heights):g}px holds one line; two need {need_two:.0f}px. '
                  f'Give it the room or set Wrap: =false')
            bad += 1
    return bad


def main():
    bad = 0
    for f in sorted(glob.glob('src/scr_*.pa.yaml')):
        screen = os.path.basename(f).replace('.pa.yaml', '')
        doc = yaml.safe_load(open(f))
        for sname, sbody in doc['Screens'].items():
            for name, kind, gal, props in collect(sbody.get('Children'), []):
                bad += check(sname, name, kind, gal, props)
    print(f'verify_layout: {bad} problem(s)' if bad else 'verify_layout: OK')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
