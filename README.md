# CYGNO Directional Dark Matter Animations

Created by **[Davide Fiorina](https://fiorotto8.github.io/)**
([ORCID 0000-0002-7104-257X](https://orcid.org/0000-0002-7104-257X)).

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

Git includes only the 854×480 landscape MP4s and GIFs and the 360×640 portrait
and Story MP4s. High-resolution masters and posting files, render caches,
manifests and local review material stay untracked.

## Vertical videos and Stories

The portrait catalog in `config/vertical.yaml` defines four complete animations
(01, 02, 04 and 05) and 14 independent Stories. Scene 03 stays horizontal.
The section implementations in `scenes/vertical/` serve both formats; Story
entry builders initialize their own event or detector state.

```bash
python scripts/render.py vertical all
python scripts/render.py vertical scene 02_wimp_recoil
python scripts/render.py vertical stories 02_wimp_recoil
python scripts/render.py vertical story 04_readout
python scripts/render.py verify --target all
```

`verify --target horizontal|vertical|stories|all` selects the delivery family.
The default remains `horizontal`; existing `all`, `scene` and `package`
commands keep their horizontal behavior.

| Scene | Ordered Story IDs |
|---|---|
| 01 | `01_halo`, `01_cygnus_wind` |
| 02 | `02_recoil`, `02_ionization`, `02_sense` |
| 04 | `04_recoil`, `04_drift`, `04_gem`, `04_readout`, `04_daq_cloud`, `04_offline` |
| 05 | `05_gran_sasso`, `05_hall_f`, `05_assembly` |

Every portrait target has two silent H.264/yuv420p, CRF 18, fast-start MP4s at
30 fps: a **1080×1920** posting file and a **360×640** review preview.
The 18 targets produce **36 files**, with no vertical GIFs or 60 fps masters.

```text
media/vertical/<scene-id>/<resolution>/<class-name>.mp4
media/stories/<scene-id>/<section-id>/<resolution>/<section-id>.mp4
```

The local delivery review page is `media/review/portrait/index.html`.

Resolution folders are `1080x1920p30` and `360x640p30`. Stories last 15–21 seconds
and initialize their own visual context. Titles and narration captions are omitted;
diagram labels remain, with narration reserved for later editing. The catalog's
context and takeaway text is editorial metadata, not rendered text.
Stories end with the logo, @cygno.exp and the original website QR. Full videos use
the original equal-size website and Instagram QR squares stacked vertically.
The exact author watermark remains throughout every video.

Portrait scenes reuse the baseline's detailed Galaxy and Solar System markers,
including Cygnus in the Galactic view; Scene 02 uses the original collision,
recoil-direction fan, microscopic track samples and head–tail callouts.
Other shared elements include the two-sided detector and sensors, camera pixels,
PMT waveform, data packets and 3D depth guides. During GEM multiplication,
daughter markers retain their parent size and branch locally, preserving the
cloud profile. Marker counts illustrate multiplication without specifying a
physical gain. Scene 05 presents each shielding
component before insertion and retains the camera and PMT sketches.

The section catalog controls motion speed and explicit settling holds. Narration
metadata adds no waiting time. Pauses within actions remain capped at 0.2 seconds;
completed diagrams can have a configured hold before the next stage. Scene 02
and the stages after light propagation use slower motion. Scene 05 has a slower
opening and a 2.2-second hold on the completed assembly. Stories use the same
choreography with their own timing. QR closing cards retain their reading time.

Critical content uses the project region x=120–900, y=250–1500 at posting size.
Diagram labels are at least 36 pixels high;
branding and the small author watermark are exceptions. These project margins
are conservative composition choices; platform overlays vary.

Verification checks the inventory, codecs, dimensions, frame rate, silence,
CRF marker, fast-start placement, full decoding, timing and closing artwork.
Every posting file, including Stories, additionally undergoes website QR decoding. Instagram
artwork matching establishes preservation of the original image, not an
Instagram app scan. Content fingerprints and layout audit checkpoints live
under `media/manifests/`, separately for horizontal, vertical and Stories.
Each target is staged and verified before replacing its previous delivery;
cleanup removes only its own temporary render. Horizontal baseline hashes are
retained at `media/manifests/horizontal/baseline.json`.

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
