<!-- SPDX-FileCopyrightText: 2026 CYGNO animation contributors -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Animation review

Review date: 2026-09-09. Scenes 01, 02, 04 and 05 have narrative refinements;
all five scenes use the shared branding and author credit.

## Horizontal presentation

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

## Horizontal baseline verification

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

## Portrait presentation

Scenes 01, 02, 04 and 05 have portrait section implementations and 14 standalone
Stories, defined in `config/vertical.yaml`. Full videos carry state between
sections; Stories initialize the necessary state independently. Titles and
narration captions are omitted, while English diagram labels remain. Catalog
context and takeaway sentences are reserved for later editing. The existing
scientific conventions and deterministic event seeds are retained. Scene 03
has no portrait derivative.

The halo appears before the luminous Galaxy, with spiral arms, stellar layers,
the Galactic Solar orbit, a revolving Earth and the Cygnus constellation linked
to the Solar motion direction. Repeated particle waves retain
the distinction between incoming velocity and the sightline toward Cygnus.
Scene 02 reuses the baseline's exact collision solution, recoil-direction fan,
microscopic track samples, uneven deposit spacing and colour palette. The same
nucleus moves into the close-up, with bound electrons released as it passes.
Momentum labels, head–tail callouts and the energy-loss diagram are retained.
Scene 04 begins with both
drift volumes and focuses on one without changing the reference system between
drift and GEM amplification. Each amplification stage adds daughter markers at
the parent positions, preserving their size and the transverse cloud profile.
The camera, acquisition and offline stages use slower motion and short settling
holds after the completed diagrams. Original camera pixels and the irregular PMT trace
are stacked, followed by moving acquisition packets, INFN Cloud storage and
offline analysis with depth guides and ER/NR topology icons. Scene 05 uses the exact
underground PNG and the baseline route coordinates, with an overview followed
by a controlled enlargement. The destination is the narrow Hall F connector.
Shielding and sensor geometry reuse the horizontal assembly builder. Each
component appears separately before insertion, with configured dimensions and
masses where known. The unspecified detector envelope is not assigned a value.
Cameras and PMTs remain visible during insertion and in the final assembly.

Full portrait endings place the logo and CYGNO EXPERIMENT above two equal
320-pixel QR ink squares, stacked vertically, with the original full artwork
retained. Stories end with a compact logo, @cygno.exp and the same 320-pixel
website QR square. No website URL is
displayed. The author watermark sits within the safe lower edge throughout.
The scientific qualifications above also apply to these portrait derivatives.

Narration metadata creates no hidden waits. Internal pauses are capped at
0.2 seconds, with unallocated section padding below 0.6 seconds. Explicit
settling holds in the catalog give completed diagrams time to register:
0.7 seconds in Scene 02, 0.8–1.2 seconds after readout/acquisition/analysis,
1.3 seconds after the Gran Sasso opening and 2.2 seconds on the final assembly.
Motion pacing and holds are defined separately for full videos and Stories.

## Portrait verification

The delivery contains eight full-animation MP4s and 28 Story MP4s: one posting
file and one preview for every target. All are silent H.264/yuv420p at 30 fps,
CRF 18, with fast-start metadata. Full videos run approximately 27.2, 34.0,
58.0 and 50.6 seconds; Stories run approximately 15–21 seconds.

Verification covers full decoding, frame counts, profiles, durations, exact
inventory and source/output fingerprints. Website QR decoding succeeds at
three posting-size closing frames per full animation and two per Story. Original Instagram
artwork and logo matching succeed in both resolutions; Instagram app scanning
remains untested. The closing QR ink bounds are 320 × 320 pixels, allowing a
one-pixel rasterization difference.

Opening, explanation, transition and closing frames were inspected at phone
scale for every Story, together with the full-video section transitions. The
route review checks intermediate dot positions as well as the Hall F endpoint;
assembly checkpoints also show each component before insertion.

The verification report records layout checkpoints, text-box overlaps,
safe-region bounds, QR ink dimensions, explicit settling holds and watermark
contrast throughout both resolutions. Five pilot previews match the final
exports byte for byte; the remaining revised Stories were inspected directly.
A frame-change check distinguishes unintended freezes from cataloged viewing
holds. The GEM checks verify increasing marker counts, constant particle sizes
and preservation of the transverse cloud extent. All 47 local tests,
whitespace checks and REUSE lint pass.
Cleanup removes only temporary portrait renders; all 15
horizontal exports retain their baseline SHA-256 hashes from commit `6719088`.

Local review players, frame sheets and the machine-readable verification report
are available at `media/review/portrait/index.html` and
`media/review/portrait/verification.json`. Rendering and technical verification
do not establish collaboration approval.
