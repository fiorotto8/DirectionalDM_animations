# CYGNO Directional Dark Matter Animations

Five Manim scenes with a fixed CYGNO signature, a small author watermark, and
an end card with the CYGNO logo and title centered above equally sized website
and original Instagram QR codes.
Valid scene IDs are defined in `config/scenes.yaml`.

## Scene status

| Scene | Animation status |
|---|---|
| 01 · Galactic wind | Refinements implemented; revised media available for review. |
| 02 · WIMP recoil | Refinements implemented; revised media available for review. |
| 03 · TPC readout | Valid, but deprecated as an animation: Scene 04 is the preferred presentation. Retained as a reference. |
| 04 · Full recoil-to-readout sequence | Preferred detector animation; revised media available for review. |
| 05 · LNGS positioning | Route and detector insertion with cameras and PMTs revised; pending collaboration validation. |

Scene 03's deprecation is a presentation choice, not a withdrawal of its
scientific validity. It remains renderable and is still included in `all` and
the package command. Use Scene 04 for the detector sequence in new edits.

See [the animation review](ANIMATION_REVIEW.md) for narrative changes, model
qualifications, and verification details.

## Requirements

Use Linux or WSL with Python 3.12, FFmpeg/ffprobe with libx264, Cairo/Pango,
DejaVu Sans, and LaTeX/dvisvgm.

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Private inputs

The original branding assets are private. Place authorized copies at:

```text
assets/logo/cygno-logo.jpg
assets/logo/QR_website.png
assets/logo/cygno.exp_Instagram-qr.png
```

Scene 05 uses the unaltered private image
`assets/LNGS/View_exp_underground_2.png` for its underground route. Hall F is
marked on the small connector between Halls A and B. The dot follows an
illustrative route on the image; its pixel positions are not surveyed geometry.

Scene 05, and therefore `all`, also requires the complete authorized private
overlay at `config/local.yaml`. A file elsewhere can be selected with:

```bash
export CYGNO_LOCAL_CONFIG=/absolute/path/to/local.yaml
```

The public placeholders are not a template for inventing missing values. Obtain
the cleared overlay from the project maintainers. Never publish `assets/`,
`config/local.yaml`, `media/`, or `dist/`.

## Render

With the virtual environment active:

```bash
python scripts/render.py all
python scripts/render.py scene 04_cygno04_full_track
python scripts/render.py verify
```

Each scene is written below `media/videos/` in three forms:

| Artifact | Output |
|---|---|
| Preview | 854×480, 30 fps, H.264/yuv420p MP4 |
| GIF | 854×480, looping, derived from the preview |
| Master | 1920×1080, 60 fps, H.264/yuv420p, CRF 18 |

## Prepare publication files

After branding, technical-data, and Scene 05 approvals are recorded in the
private overlay, run:

```bash
python scripts/render.py package --tag release-2026-01
```

This verifies all outputs and writes ten low-resolution media files plus
`SHA256SUMS` below `dist/<tag>/`; it does not upload or publish anything.

Code is BSD-3-Clause and original released media is CC BY 4.0. CYGNO,
Instagram, and third-party marks and assets are excluded from those grants; see
`LICENSE` and `TRADEMARKS.md`.
