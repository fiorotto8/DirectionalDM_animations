<!-- SPDX-FileCopyrightText: 2026 CYGNO animation contributors -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Animation review

Review date: 2026-09-09. Scenes 01, 02, 04 and 05 have narrative refinements;
all five scenes use the shared branding and author credit.

## Shared presentation

The end card contains the CYGNO logo, the original `QR_website.png` pointing to
[the CYGNO website](https://web.infn.it/cygnus/), and the original pink/orange
`cygno.exp_Instagram-qr.png`. Both supplied images remain unmodified. The website
code has an added white quiet zone in the composition. Its existing URL fragment
is preserved in the artwork. The logo and **CYGNO EXPERIMENT** are centered above
two matching white panels. Both visible QR squares have the same dimensions and
vertical alignment in every scene; the website URL is not displayed.

The exact user-requested credit, **By Davide Fiorina via Local Qwen3.8**, appears
as a small watermark at the lower-right edge, including camera moves and the
outro. Presentation notes such as “Illustrative detector response” are removed
from the frames. Scientific qualifications are recorded below.

## Narrative

- **01:** The extended purple dark-matter halo appears first. Stars and gas
  then appear inside it, followed by the Solar System and the continuous change
  into the Solar rest frame. This distinguishes dark matter from the visible
  Galactic disk. Solar motion, sightline and incoming-velocity signs are preserved.
- **02:** A nucleus in ordinary detector gas receives the recoil from the
  incoming dark-matter particle. The close-up follows that same nucleus through
  gas atoms; bound electrons move away as positive ions remain behind. The trail
  endpoint follows the moving nucleus, and the legend identifies freed electrons
  and positive gas ions. Momentum conservation and statistical sense recognition
  are preserved.
- **04:** Electron drift and GEM multiplication share the same detector view.
  The camera image is a diffuse pixel field without connecting lines, and the
  PMT trace includes pulse substructure and baseline fluctuations. Trigger/DAQ
  selects and records the image and timing, then sends the event to INFN Cloud
  storage. A separate offline stage uses the stored event to explain full 3D
  track analysis, direction estimation and recoil-type identification.
- **05:** The original underground PNG is retained. The dot starts at the
  lower-right entrance and proceeds towards the narrow A–B connector, marked
  **HallF - CYGNO04**. The detector moves into place together with its qCMOS
  cameras and PMTs. The sensor sketches occupy the space between copper and
  water and remain visible in the final assembly. Temporary **Readout**,
  **qCMOS cameras** and **PMTs** labels introduce the sensors.
  The scene ends with the shielding assembly and the common end card.

**Scene 03 remains valid, but is deprecated as an animation in favor of
Scene 04.** It remains independently renderable and included in `all` and
packaging. Scene 05 remains pending collaboration validation.

## Scientific scope

These are explanatory animations, not measured detector events. Halo markers,
particle counts, atom symbols, multiplication, light intensity and pulse noise
are qualitative. The camera pixels use a deterministic diffusion model; they
are not real camera data. The 3D view reuses optical samples with assigned
qualitative depth, not a fitted track or inversion of the displayed waveform.
Direction/sense estimates and ER/NR classification represent the offline
analysis steps without claiming measured reconstruction performance.

The Scene 05 route follows image coordinates, not surveyed navigation geometry.
Camera and PMT sketches describe the readout arrangement, without specifying an
optical mount design. Each optical end uses the configured projection: three
cameras and four visible PMTs, matching Scenes 03 and 04. Existing configured shielding dimensions are retained.

## Verification

All 38 repository tests pass, including checks that the watermark follows pans
and zooms and that a QR pointing to a different website is rejected. The website
QR and original Instagram artwork pass checks at three outro frames in every
preview, 1080p master and GIF. Standard QR decoding is used for the website (with enlargement
when needed); template matching checks preservation of the original Instagram
nametag. Its stylized artwork is preserved; an Instagram app scan has not been
verified here.

Preview and master frames have been visually inspected for labels, particle/ionization
continuity, drift-to-GEM framing, image diffusion, pulse shape, data storage,
offline analysis, route placement, readout sketches and the closing card.
All 15 artifacts passed the standard media verifier before installation: five
480p30 previews, five 1080p60 masters and five looping GIFs. Checks include full
decoding, delivery profiles, frame counts, duration consistency, source freshness
and preview closing cards. Additional checks cover master and GIF closing cards.
QR squares measure exactly 432 × 432 pixels with matching top edges in every
1080p master. Preview and GIF edge measurements allow up to three pixels for
rasterization and palette dithering; their source geometry is identical.
The final 15-file delivery set is retained in `media/videos/`; temporary renders,
review copies and caches have been removed. All 38 tests,
`git diff --check` and REUSE lint pass.

Technical checks and visual inspection do not constitute collaboration approval.
