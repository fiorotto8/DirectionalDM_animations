# Third-party notices

This repository does not vendor third-party Python packages, FFmpeg, fonts, or
LaTeX. They are installed separately by the user and retain their own terms.

Direct runtime dependencies:

| Component | Version | License | Purpose |
|---|---:|---|---|
| Manim Community | 0.18.1 | MIT | Animation engine |
| NumPy | 1.26.4 | BSD-3-Clause | Deterministic scientific geometry |
| OpenCV Python Headless | 4.10.0.84 | Apache-2.0 | QR verification |
| Pillow | 10.2.0 | HPND | In-memory official-logo mask |
| PyYAML | 6.0.1 | MIT | Configuration loading |
| qrcode | 8.2 | BSD-3-Clause | Standard Instagram-page QR generation |

Manim brings transitive dependencies; consult the installed distributions for
their notices.

FFmpeg/ffprobe and libx264 are system tools, not redistributed here. DejaVu
Sans and the LaTeX toolchain are likewise external. Distributing a container
or bundled binary requires a separate license-compliance review.
