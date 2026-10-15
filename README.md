# Lab Equipment Hub

Power Apps canvas app for managing lab equipment across campuses, rooms and research
groups, on the SharePoint site `LabEquipmentHub`. The interface is in English; the app
is used on a phone first and a desktop second.

## Layout of this repository

| Path | What it is |
|---|---|
| `src/*.pa.yaml` | The screens, one file each. This is what gets edited. |
| `msapp_original/` | The unpacked `.msapp` exported from Power Apps Studio - the base a build starts from. |
| `msapp_original.msapp` | That same export, untouched. |
| `tools/` | Build and verification scripts. |
| `build/` | Output. Not in git. |

## Recovering from an empty checkout

This repository was once rebuilt from scratch after a container was reclaimed with
nothing pushed. The route back: export the app from Power Apps Studio
(Settings > General > Export package), unzip it, and take the `.msapp` from
`Microsoft.PowerApps/apps/<id>/`. It carries `Src/*.pa.yaml` for every screen, comments
included, so the source survives inside the app itself.
