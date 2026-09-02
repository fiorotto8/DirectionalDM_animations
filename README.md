# CYGNO Directional Dark Matter Animations

Five Manim scenes with a fixed CYGNO signature and Instagram outro. Valid scene
IDs are defined in `config/scenes.yaml`.

## Requirements

Use Linux or WSL with Python 3.12, FFmpeg/ffprobe with libx264, Cairo/Pango,
DejaVu Sans, and LaTeX/dvisvgm.

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Private inputs

The official logo is intentionally not published. Place an authorized copy at:

```text
assets/logo/cygno-logo.jpg
```

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
python scripts/render.py scene 03_tpc_readout
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
