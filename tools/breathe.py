#!/usr/bin/env python3
"""Give the content room, without moving anything.

White surfaces made the grouping visible and, with it, how tightly the content
was packed inside them. The fix is vertical: taller rows, wider gaps between
sections, taller section bars. No width changes - a container's padding and its
children's widths are set independently in this app, so widening a gutter
silently pushes content past the edge.

Each row height appears twice: once as the gallery's TemplateSize and once in
the Height that multiplies it by the row count. Both move together or the list
renders at the wrong height.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from setprop import set_prop

# gallery -> (file, new TemplateSize). The two-value ones are phone, desktop.
ROWS = [
    # The detail tables: two 12pt lines in a 34px row, a dozen rows deep.
    ('scr_AssetDetail', 'galAssetFields',  '=44'),
    ('scr_SetupDetail', 'galSetupFields',  '=44'),
    # File lists: a name and a type, both cramped.
    ('scr_AssetDetail', 'galAssetDocs',    '=48'),
    ('scr_SetupDetail', 'galSetupDocs',    '=48'),
    # A conflicting booking is bad news; it deserves to be read at a glance.
    ('scr_BookingDetail', 'galConflicts',  '=44'),
    # Two-line rows that had 56px on a desktop: title 22 + sub 20 + nothing left.
    ('scr_SetupDetail', 'galSetupAssets',  '=If(Parent.Width < 600, 94, 66)'),
    ('scr_Move', 'galSetupResults',        '=If(Parent.Width < 600, 74, 64)'),
    ('scr_Move', 'galAssetResults',        '=If(Parent.Width < 600, 74, 64)'),
    ('scr_Bookings', 'galBkDeviceResults', '=If(Parent.Width < 600, 84, 72)'),
    ('scr_BookingDetail', 'galBkAssetResults', '=If(Parent.Width < 600, 84, 72)'),
    ('scr_SetupDetail', 'galSetupAddResults', '=If(Parent.Width < 600, 84, 72)'),
]

# The Height formulas that multiply a row count by the row height.
COUPLED = [
    ('src/scr_AssetDetail.pa.yaml', 'CountRows(varAssetFields) * 34', 'CountRows(varAssetFields) * 44'),
    ('src/scr_SetupDetail.pa.yaml', 'CountRows(varSetupFields) * 34', 'CountRows(varSetupFields) * 44'),
    ('src/scr_SetupDetail.pa.yaml', ') * If(Parent.Width < 600, 94, 56)', ') * If(Parent.Width < 600, 94, 66)'),
    ('src/scr_SetupDetail.pa.yaml', ') * 40', ') * 48'),
]

# Space between the sections of a screen. 8 put a list against the next heading.
GAPS = [
    ('scr_AssetDetail', 'conAssetBody', '=16'),
    ('scr_SetupDetail', 'conSetupBody', '=16'),
    ('scr_AssetEdit',   'conEditBody',  '=14'),
    ('scr_SetupEdit',   'conSeBody',    '=14'),
    ('scr_BookingDetail', 'conBookingBody', '=14'),
    ('scr_TicketDetail', 'conTicketBody', '=14'),
]

# The tinted bar above a section. 26px is the text and nothing else.
HEADERS = [
    ('scr_AssetDetail', ['lblFieldsHeader', 'lblDocsHeader', 'lblHistoryHeader',
                         'lblAssetTicketsHeader']),
    ('scr_SetupDetail', ['lblSetupFieldsHeader', 'lblSetupAssetsHeader',
                         'lblSetupDocsHeader', 'lblSetupAddCaption']),
]


def path_of(screen):
    return f'src/{screen}.pa.yaml'


def main():
    n = 0
    for screen, ctrl, size in ROWS:
        set_prop(path_of(screen), ctrl, 'TemplateSize', size); n += 1
    for screen, ctrl, gap in GAPS:
        set_prop(path_of(screen), ctrl, 'LayoutGap', gap); n += 1
    for screen, ctrls in HEADERS:
        for c in ctrls:
            set_prop(path_of(screen), c, 'Height', '=32'); n += 1
    for path, old, new in COUPLED:
        text = open(path).read()
        if old not in text:
            sys.exit(f'{path}: expected to find {old!r} - the row height and its '
                     f'multiplier have drifted apart')
        open(path, 'w').write(text.replace(old, new)); n += 1
    print(f'{n} spacing change(s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
