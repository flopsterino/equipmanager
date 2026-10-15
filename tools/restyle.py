#!/usr/bin/env python3
"""Put the app in the University of Antwerp house style.

Every colour in the sources is a literal RGBA(...), so restyling is a matter of
mapping the old palette onto the new one. The whole palette sits in PALETTE
below: if the house style's hex codes turn out to be different, change the two
brand colours there and run this again.

What it does NOT touch: positions, sizes, heights, widths or any formula that is
not a colour or a corner radius. The layout stays exactly where it was.

    python3 tools/restyle.py            # rewrites src/*.pa.yaml in place
    python3 tools/restyle.py --dry-run  # report only
"""
import glob, re, sys


def rgba(hexcode, alpha=1):
    h = hexcode.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f'RGBA({r}, {g}, {b}, {alpha})'


# --- the brand ---------------------------------------------------------------
UA_BLUE = '#002e65'      # UAntwerpen blue,  Pantone 534
UA_RED  = '#ea2c38'      # UAntwerpen red,   Pantone 1795

# --- derived, so the whole thing follows from those two ----------------------
BLUE_HOVER   = '#0a4a93'   # one step lighter, for hover and pressed
BLUE_TINT    = '#e8eff8'   # the blue at a whisper, for hovered secondary buttons
PAGE         = '#f4f5f7'   # the surface a card sits on
CARD         = '#ffffff'
SECTION      = '#eef1f6'   # the bar above a section, blue-grey rather than grey
DIVIDER      = '#e8ecf2'
FIELD_BORDER = '#d3d9e2'
EDGE         = '#cbd2dd'   # a dialog's outline
DISABLED     = '#e9edf3'
TEXT         = '#17233a'   # near-black with a blue cast, so it sits with the brand
TEXT_2       = '#5a6577'
TEXT_3       = '#8b94a3'

# Status colours as soft pills: a tinted ground with dark text, instead of a
# saturated block with white text. On a phone the block shouts; the pill reads.
GOOD_BG, GOOD_FG = '#e6f4ea', '#1b5e34'
WARN_BG, WARN_FG = '#fff4e0', '#8a4b00'
BAD_BG,  BAD_FG  = '#fde8ea', '#a3121c'      # the red, darkened enough to read on its own tint
NEUTRAL_BG, NEUTRAL_FG = '#eef0f4', '#475467'

PALETTE = {
    # action blue, everywhere it appears
    'RGBA(0, 120, 212, 1)':   rgba(UA_BLUE),
    'RGBA(16, 110, 190, 1)':  rgba(BLUE_HOVER),
    'RGBA(235, 243, 252, 1)': rgba(BLUE_TINT),

    # text
    'RGBA(50, 49, 48, 1)':    rgba(TEXT),
    'RGBA(96, 94, 92, 1)':    rgba(TEXT_2),
    'RGBA(161, 159, 157, 1)': rgba(TEXT_3),
    'RGBA(166, 166, 166, 1)': rgba(TEXT_3),

    # surfaces and lines
    'RGBA(245, 245, 245, 1)': rgba(SECTION),
    'RGBA(243, 242, 241, 1)': rgba(SECTION),
    'RGBA(250, 250, 250, 1)': rgba(PAGE),
    'RGBA(240, 240, 240, 1)': rgba(DIVIDER),
    'RGBA(219, 219, 219, 1)': rgba(FIELD_BORDER),
    'RGBA(200, 198, 196, 1)': rgba(EDGE),
    'RGBA(237, 235, 233, 1)': rgba(DISABLED),

    # status: ground
    'RGBA(16, 124, 16, 1)':   rgba(GOOD_FG),
    'RGBA(196, 116, 0, 1)':   rgba(WARN_FG),
    'RGBA(168, 0, 0, 1)':     rgba(BAD_FG),
    'RGBA(138, 0, 0, 1)':     rgba(BAD_FG),
    'RGBA(133, 66, 0, 1)':    rgba(WARN_FG),
    'RGBA(255, 244, 206, 1)': rgba(WARN_BG),
    'RGBA(253, 243, 243, 1)': rgba(BAD_BG),
    'RGBA(250, 220, 220, 1)': rgba(BAD_BG),
}

# A corner radius per role. 4 everywhere reads as nothing in particular; the
# pills keep theirs, because a pill is a shape and not a rounded rectangle.
RADII = {'4': '6', '6': '6', '8': '8'}


def main(write=True):
    changed_files = 0
    counts = {}
    for path in sorted(glob.glob('src/*.pa.yaml')):
        text = original = open(path).read()
        for old, new in PALETTE.items():
            if old in text:
                counts[old] = counts.get(old, 0) + text.count(old)
                text = text.replace(old, new)
        # Radius only where it is written as a bare number on a Radius property.
        def fix_radius(m):
            return f'{m.group(1)}={RADII.get(m.group(2), m.group(2))}'
        text = re.sub(r'(Radius(?:TopLeft|TopRight|BottomLeft|BottomRight):\s*)=(\d+)',
                      fix_radius, text)
        if text != original:
            changed_files += 1
            if write:
                open(path, 'w').write(text)
    for old, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f'  {n:4}x  {old:24} -> {PALETTE[old]}')
    print(f'{sum(counts.values())} colour(s) remapped over {changed_files} file(s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(write='--dry-run' not in sys.argv))
