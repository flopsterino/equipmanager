# Lab Equipment Hub - working rules

Standing instructions from the owner of this app. These outrank convenience.

## The app

- **It stays a Power Apps canvas app.** Not a web app, not anything else.
- **Everything in English** in the interface, because international students use it.
- **Ask when something is unclear. Never assume.**
- **House style: University of Antwerp.** Blue `#002e65`, red `#ea2c38`. The whole palette
  is derived from those two in `tools/restyle.py`; change them there, not control by control.

## Every screen size, not one

The app is used on a phone (iPhone 14 Pro) and on a desktop. A change is finished when it
looks right at **both** ends, and at the widths in between:

- Check every new or changed control at `Parent.Width < 600`, and at the tighter `< 420`
  breakpoint where one already exists.
- A fixed `Height` that fits on a desktop usually does not fit when the same text wraps
  into two or three lines in a narrow column. Derive the height from the content.
- Buttons side by side need their combined width plus the gaps to fit inside
  `Parent.Width - padding`, or they wrap into a row that has no height for them.
- A label in a gallery row either has room for two lines or says `Wrap: =false`. A row has
  one height for every row, so there is no third option.

## The source lives in the app

If this checkout is ever empty again: export the app from Power Apps Studio
(Settings > General > Export package), unzip it, and take the `.msapp` from
`Microsoft.PowerApps/apps/<id>/`. It carries `Src/*.pa.yaml` for every screen with the
comments intact. That is how this repository was rebuilt once already.

**Push every change.** The work is only safe once it is on the remote.

## Before delivering

Run `./tools/check_all.sh`. It writes the sources into the package and then checks that
nothing was lost or added - a changed formula is a build, a vanished control is a bug.
