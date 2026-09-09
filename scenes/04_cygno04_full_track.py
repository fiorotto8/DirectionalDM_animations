from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arc,
    Arrow,
    Circle,
    Create,
    CubicBezier,
    DashedLine,
    Dot,
    Ellipse,
    FadeIn,
    FadeOut,
    Indicate,
    LaggedStart,
    Line,
    ManimColor,
    MoveAlongPath,
    MovingCameraScene,
    Rectangle,
    ReplacementTransform,
    Restore,
    RoundedRectangle,
    Text,
    Transform,
    VGroup,
    VMobject,
    Write,
    UpdateFromAlphaFunc,
    Succession,
    linear,
    smooth,
    interpolate_color,
)

# Keep this scene directly renderable from either the repository root or the
# scenes directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cygno_anim.branding import add_brand_signature, show_brand_outro
from cygno_anim.config import (
    ConfigurationError,
    load_science,
    require_positive_integer,
)
from cygno_anim.detector import camera_icon, gem_stack, pmt_icon
from cygno_anim.events import diffuse_track, simulate_nr_track
from cygno_anim.visuals import (
    BACKGROUND,
    CHAMBER_FILL,
    CYGNUS,
    ELECTRON,
    FIELD,
    FONT,
    FOREGROUND,
    GEM,
    MUTED,
    NUCLEUS,
    PHOTON,
    PIPELINE_PANEL,
    READOUT_PANEL,
    ScientificScene,
    electron_marker,
    label,
    nucleus_marker,
    semantic_arrow,
)


class CYGNO04FullTrack(MovingCameraScene):
    """Follow one recoil from primary ionization to 3D reconstruction."""

    def setup(self):
        super().setup()
        self.camera.background_color = BACKGROUND

    def title_block(self, kicker: str, title: str) -> VGroup:
        return ScientificScene.title_block(self, kicker, title)

    def construct(self):
        self.camera.frame.save_state()
        self.science = load_science(include_local=False)
        reconstruction_default = self.science["conventions"][
            "reconstructed_track_default"
        ]
        if reconstruction_default != "unoriented_axis":
            raise ConfigurationError(
                f"Unsupported reconstruction convention: {reconstruction_default!r}"
            )

        title = self.title_block("CYGNO-04", "One recoil, from gas to 3D")
        add_brand_signature(self)
        self.play(FadeIn(title, shift=DOWN * 0.10), run_time=1.15)

        detector = self.build_detector()
        detector_label = label(
            "two back-to-back drift volumes",
            color=FOREGROUND,
            scale=0.26,
            weight="BOLD",
        ).move_to([-1.63, 1.92, 0])
        self.play(FadeIn(detector, lag_ratio=0.035), Write(detector_label), run_time=2.5)
        self.wait(2.5)

        phase = self.phase_label("1 · Recoil + primary ionization", NUCLEUS)
        self.play(FadeIn(phase, shift=UP * 0.08), run_time=0.85)

        event = self.build_primary_track()
        recoil_path, recoil_nucleus, primary_electrons, asymmetry_note = event
        recoil_nucleus.move_to(recoil_path.get_start())
        impact = Circle(radius=0.12, color=NUCLEUS, stroke_width=2.4).move_to(recoil_path.get_start())
        self.play(FadeIn(impact), FadeIn(recoil_nucleus), run_time=0.65)
        full_recoil_path = recoil_path.copy()
        samples = np.linspace(0.0, 1.0, 401)
        positions = np.array([full_recoil_path.copy().pointwise_become_partial(
            full_recoil_path, 0.0, t).get_end() for t in samples])
        thresholds = [samples[np.argmin(np.linalg.norm(positions-dot.get_center(), axis=1))]
                      for dot in primary_electrons]
        opacities = [dot.get_fill_opacity() for dot in primary_electrons]
        event_group = VGroup(recoil_path, recoil_nucleus, primary_electrons)

        def form_primary(_group, alpha):
            recoil_path.pointwise_become_partial(full_recoil_path, 0.0, alpha)
            recoil_nucleus.move_to(recoil_path.get_end())
            for dot, threshold, opacity in zip(primary_electrons, thresholds, opacities):
                dot.set_opacity(opacity * float(np.clip((alpha-threshold)/.025, 0, 1)))

        form_primary(event_group, 0)
        self.add(event_group)
        self.play(UpdateFromAlphaFunc(event_group, form_primary, rate_func=linear), run_time=3.0)
        for dot, opacity in zip(primary_electrons, opacities):
            dot.set_opacity(opacity)
        self.play(FadeOut(impact), FadeOut(recoil_nucleus), FadeIn(asymmetry_note), run_time=0.85)
        self.wait(2.3)

        next_phase = self.phase_label("2 · Electron drift + diffusion", ELECTRON)
        next_phase.scale(0.82).move_to([0.0, 1.89, 0.0])
        inactive_half = VGroup(
            detector.left_volume,
            detector.left_cage,
            detector.left_stack,
            detector.left_cameras,
            detector.left_pmts,
            detector.left_gem_label,
        )
        self.play(FadeOut(title), FadeOut(detector_label), FadeOut(phase), run_time=0.75)
        self.play(
            FadeOut(asymmetry_note),
            FadeOut(inactive_half),
            self.camera.frame.animate.scale(0.65).move_to([-0.15, -0.50, 0.0]),
            run_time=2.3,
        )
        phase = next_phase
        self.play(FadeIn(phase, shift=UP * 0.06), run_time=0.75)
        field_arrow = semantic_arrow(
            np.array([0.68, 0.95, 0]),
            np.array([-1.15, 0.95, 0]),
            "conventional E field",
            FIELD,
            label_direction=UP,
            stroke_width=2.7,
        )
        drift_arrow = semantic_arrow(
            np.array([-1.15, -0.96, 0]),
            np.array([0.72, -0.96, 0]),
            "electron drift",
            ELECTRON,
            label_direction=DOWN,
            stroke_width=2.9,
        )
        self.play(Create(field_arrow[0]), FadeIn(field_arrow[1]), Create(drift_arrow[0]), FadeIn(drift_arrow[1]), run_time=1.35)
        self.wait(1.4)

        end_points = self.diffused_end_points(primary_electrons)
        drift_animations = []
        rng = np.random.default_rng(404)
        for dot, end in zip(primary_electrons, end_points):
            start = dot.get_center()
            path = CubicBezier(
                start,
                start + np.array([0.48, rng.normal(0.0, 0.12), 0]),
                end + np.array([-0.38, rng.normal(0.0, 0.13), 0]),
                end,
            )
            drift_animations.append(MoveAlongPath(dot, path))
        self.play(
            LaggedStart(*drift_animations, lag_ratio=0.035),
            recoil_path.animate.set_stroke(opacity=0.18),
            run_time=3.8,
        )
        envelope = Ellipse(
            width=0.32,
            height=max(0.62, float(np.ptp(np.asarray(end_points)[:, 1]) + 0.22)),
            stroke_color=ELECTRON,
            stroke_width=1.3,
            fill_color=ELECTRON,
            fill_opacity=0.045,
        ).move_to([0.76, float(np.mean(np.asarray(end_points)[:, 1])), 0])
        diffusion_note = label("diffused track cloud", color=ELECTRON, scale=0.20, weight="BOLD")
        diffusion_note.next_to(envelope, LEFT, buff=0.20).shift(UP * 0.62)
        self.play(Create(envelope), FadeIn(diffusion_note), run_time=0.95)
        self.wait(2.0)

        next_phase = self.phase_label("3 · Triple-GEM avalanche + light", PHOTON)
        next_phase.scale(0.82).move_to(phase)
        self.play(
            Transform(phase, next_phase),
            FadeOut(field_arrow),
            FadeOut(drift_arrow),
            FadeOut(diffusion_note),
            FadeOut(envelope),
            run_time=1.0,
        )

        current_cloud, final_flash = self.show_gem_amplification(detector, primary_electrons)

        avalanche_note = label(
            "large multiplication · abundant scintillation",
            color=PHOTON,
            scale=0.20,
            weight="BOLD",
        ).move_to([0.20, -1.35, 0])
        self.play(FadeIn(avalanche_note), Indicate(detector.right_stack, color=PHOTON), run_time=0.95)
        self.wait(1.9)

        next_phase = self.phase_label("4 · Optical propagation + readout", CYGNUS)
        next_phase.scale(0.82).move_to(phase)
        self.play(Transform(phase, next_phase), FadeOut(avalanche_note), run_time=0.90)
        optical_paths, travelling_photons = self.build_optical_paths(detector)
        self.play(Create(optical_paths), run_time=1.2)
        self.play(
            LaggedStart(*[MoveAlongPath(dot, path) for dot, path in travelling_photons], lag_ratio=0.06),
            run_time=2.0,
        )
        self.play(
            Indicate(detector.right_cameras, color=CYGNUS),
            Indicate(detector.right_pmts, color=PHOTON),
            run_time=1.2,
        )
        self.wait(1.6)

        image_panel, image_content, waveform_panel, waveform, provenance = self.build_readout_panels()
        image_link = VMobject(color=CYGNUS, stroke_width=1.6)
        image_link.set_points_as_corners([
            detector.right_cameras.get_right(), [2.10, 0.20, 0], [2.10, -1.145, 0],
            [-4.02, -1.145, 0], [-4.02, -2.10, 0], image_panel[0].get_left(),
        ])
        time_link = VMobject(color=PHOTON, stroke_width=1.6)
        time_link.set_points_as_corners([
            detector.right_pmts[-1].get_top(), [3.50, 1.40, 0],
            [3.50, -2.10, 0], waveform_panel[0].get_right(),
        ])
        sensor_links = VGroup(image_link, time_link)
        self.play(FadeIn(image_panel), FadeIn(waveform_panel), Create(sensor_links), run_time=1.05)
        self.play(
            LaggedStart(*[FadeIn(layer) for layer in image_content], lag_ratio=0.018),
            FadeIn(waveform),
            run_time=2.8,
        )
        self.play(FadeIn(provenance, shift=UP * 0.06), run_time=0.75)
        self.wait(3.2)

        self.play(
            FadeOut(optical_paths),
            FadeOut(VGroup(*[dot for dot, _path in travelling_photons])),
            FadeOut(final_flash),
            current_cloud.animate.set_opacity(0.28),
            run_time=1.0,
        )
        chain = self.build_signal_chain()
        active_detector = VGroup(
            detector.right_volume,
            detector.right_cage,
            detector.cathode,
            detector.right_stack,
            detector.right_cameras,
            detector.right_pmts,
            detector.cathode_label,
            detector.right_gem_label,
        )
        # Lift the image first, then move the waveform into the cleared space.
        self.play(
            Restore(self.camera.frame, rate_func=lambda t: smooth(min(2*t, 1.0))),
            FadeOut(active_detector),
            FadeOut(recoil_path),
            FadeOut(current_cloud),
            FadeOut(phase),
            FadeOut(sensor_links),
            ReplacementTransform(image_panel[0], chain.image_source[0], rate_func=lambda t: smooth(min(2*t, 1.0))),
            ReplacementTransform(image_content, chain.image_source[2], rate_func=lambda t: smooth(min(2*t, 1.0))),
            FadeOut(image_panel[1]),
            Succession(FadeOut(VGroup(image_panel[2], image_panel[3]), run_time=1.2),
                       FadeIn(chain.image_source[1], run_time=1.2)),
            ReplacementTransform(waveform_panel[0], chain.wave_source[0], rate_func=lambda t: smooth(max(2*t-1, 0.0))),
            ReplacementTransform(waveform_panel[2], chain.wave_source[2], rate_func=lambda t: smooth(max(2*t-1, 0.0))),
            ReplacementTransform(waveform, chain.wave_source[3], rate_func=lambda t: smooth(max(2*t-1, 0.0))),
            Succession(FadeOut(VGroup(waveform_panel[1], waveform_panel[3]), run_time=1.2),
                       FadeIn(chain.wave_source[1], run_time=1.2)),
            ReplacementTransform(provenance, chain.provenance),
            run_time=2.4,
        )
        self.play(
            FadeIn(chain.header, shift=DOWN * 0.08),
            FadeIn(chain.daq, shift=RIGHT * 0.08),
            Create(chain.image_link),
            Create(chain.wave_link),
            run_time=1.8,
        )
        self.play(
            FadeIn(chain.image_packet),
            FadeIn(chain.wave_packet),
            run_time=0.45,
        )
        self.play(
            MoveAlongPath(chain.image_packet, chain.image_path),
            MoveAlongPath(chain.wave_packet, chain.wave_path),
            run_time=2.0,
        )
        self.play(FadeOut(chain.image_packet), FadeOut(chain.wave_packet),
                  Indicate(chain.daq, color=ELECTRON), FadeIn(chain.local_record), run_time=1.2)
        self.wait(1.3)
        self.play(Create(chain.cloud_link), FadeIn(chain.cloud),
                  FadeIn(chain.event_packet), run_time=1.2)
        self.play(MoveAlongPath(chain.event_packet, chain.event_path), run_time=2.0)
        self.play(FadeOut(chain.event_packet), Indicate(chain.cloud, color=CYGNUS),
                  FadeIn(chain.archive), run_time=1.2)
        self.wait(2.5)

        offline_header = VGroup(
            label("CYGNO-04", color=CYGNUS, scale=.22, weight="BOLD"),
            label("Offline analysis of stored events", color=FOREGROUND, scale=.40, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=.10).move_to(chain.header)
        self.play(Succession(FadeOut(chain.header, run_time=.6), FadeIn(offline_header, run_time=.8)),
                  Create(chain.reconstruction_link), FadeIn(chain.reconstruction), run_time=1.4)
        chain.header = offline_header
        self.wait(2.0)
        self.show_reconstruction(chain)

    def build_detector(self) -> VGroup:
        centre_x = -1.70
        centre_y = 0.20
        volume_width = 3.05
        volume_height = 2.70

        cathode = Line(
            [centre_x, centre_y - 1.20, 0],
            [centre_x, centre_y + 1.20, 0],
            color=FOREGROUND,
            stroke_width=3.8,
        )
        left_volume = Rectangle(
            width=volume_width,
            height=volume_height,
            stroke_color=MUTED,
            stroke_width=1.3,
            fill_color=CHAMBER_FILL,
            fill_opacity=0.30,
        ).move_to([centre_x - volume_width / 2, centre_y, 0])
        right_volume = left_volume.copy().move_to([centre_x + volume_width / 2, centre_y, 0])

        left_cage = VGroup()
        right_cage = VGroup()
        for volume, half_cage in ((left_volume, left_cage), (right_volume, right_cage)):
            for fraction in (0.20, 0.40, 0.60, 0.80):
                x = volume.get_left()[0] + fraction * volume_width
                half_cage.add(
                    Line(
                        [x, centre_y - 1.17, 0],
                        [x, centre_y + 1.17, 0],
                        color=FIELD,
                        stroke_width=0.55,
                    ).set_opacity(0.24)
                )
        cage = VGroup(left_cage, right_cage)

        left_stack = gem_stack(height=2.12, spacing=0.075).move_to([centre_x - volume_width + 0.23, centre_y, 0])
        right_stack = gem_stack(height=2.12, spacing=0.075).move_to([centre_x + volume_width - 0.23, centre_y, 0])

        left_cameras, left_pmts = self.sensor_end(-1, centre_x - volume_width - 0.60, centre_y)
        right_cameras, right_pmts = self.sensor_end(1, centre_x + volume_width + 0.60, centre_y)

        cathode_label = label("central cathode", color=FOREGROUND, scale=0.18)
        cathode_label.next_to(cathode, UP, buff=0.28).shift(LEFT * 0.65)
        left_gem_label = label("triple GEM", color=GEM, scale=0.18, weight="BOLD")
        left_gem_label.next_to(left_stack, DOWN, buff=0.12)
        right_gem_label = label("triple GEM", color=GEM, scale=0.18, weight="BOLD")
        right_gem_label.next_to(right_stack, DOWN, buff=0.12)

        group = VGroup(
            left_volume,
            right_volume,
            cage,
            cathode,
            left_stack,
            right_stack,
            left_cameras,
            right_cameras,
            left_pmts,
            right_pmts,
            cathode_label,
            left_gem_label,
            right_gem_label,
        )
        group.left_stack = left_stack
        group.right_stack = right_stack
        group.left_volume = left_volume
        group.right_volume = right_volume
        group.left_cage = left_cage
        group.right_cage = right_cage
        group.left_cameras = left_cameras
        group.right_cameras = right_cameras
        group.left_pmts = left_pmts
        group.right_pmts = right_pmts
        group.cathode = cathode
        group.cathode_label = cathode_label
        group.left_gem_label = left_gem_label
        group.right_gem_label = right_gem_label
        return group

    def sensor_end(self, side: int, camera_x: float, centre_y: float):
        camera_count = require_positive_integer(
            self.science["geometry"]["cameras_per_optical_end"],
            "geometry.cameras_per_optical_end",
        )
        pmt_count = require_positive_integer(
            self.science["presentation_projection"]["pmts_visible_per_optical_end"],
            "presentation_projection.pmts_visible_per_optical_end",
        )
        cameras = VGroup()
        for y_offset in np.linspace(-0.70, 0.70, camera_count):
            icon = camera_icon(0.34)
            if side > 0:
                icon.flip(UP)
            icon.move_to([camera_x, centre_y + y_offset, 0])
            cameras.add(icon)

        pmts = VGroup()
        pmt_x = camera_x - side * 0.39
        for y_offset in np.linspace(-0.90, 0.90, pmt_count):
            icon = pmt_icon(0.34)
            if side > 0:
                icon.flip(UP)
            icon.move_to([pmt_x, centre_y + y_offset, 0])
            pmts.add(icon)
        return cameras, pmts

    def build_primary_track(self):
        primary = simulate_nr_track(seed=410, visible_integral=1.0)
        sample_indices = np.arange(0, len(primary.points), 2)
        points = primary.points[sample_indices]
        points = points - points.mean(axis=0)
        angle = np.deg2rad(-24.0)
        rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        points = (points @ rotation.T) * 1.12
        mapped = [np.array([-0.72 + point[0], 0.20 + point[1], 0]) for point in points]

        recoil_path = VMobject(color=NUCLEUS, stroke_width=4.2)
        recoil_path.set_points_smoothly(mapped)
        sampled_weights = primary.weights[sample_indices]
        sampled_weights /= sampled_weights.max()
        electrons = VGroup(
            *[
                electron_marker(0.020 + 0.022 * weight)
                .set_opacity(0.52 + 0.48 * weight)
                .move_to(point + np.array([0, 0.028 * (-1) ** index, 0]))
                for index, (point, weight) in enumerate(zip(mapped, sampled_weights))
            ]
        )
        asymmetry_note = label(
            "charge gradient → head–tail information",
            color=NUCLEUS,
            scale=0.20,
            weight="BOLD",
        ).next_to(recoil_path, DOWN, buff=0.13)
        return recoil_path, nucleus_marker(0.12).scale(0.72), electrons, asymmetry_note

    def diffused_end_points(self, electrons: VGroup):
        rng = np.random.default_rng(411)
        result = []
        start_y = np.asarray([dot.get_center()[1] for dot in electrons])
        for y in start_y:
            result.append(np.array([rng.uniform(0.68, 0.82), y + rng.normal(0.0, 0.18), 0]))
        return result

    def photon_flash(self, centre: np.ndarray, rays: int) -> VGroup:
        result = VGroup()
        for index in range(rays):
            angle = 2 * np.pi * index / rays
            direction = np.array([np.cos(angle), np.sin(angle), 0])
            result.add(
                Line(
                    centre + 0.06 * direction,
                    centre + (0.18 + 0.025 * (index % 2)) * direction,
                    color=PHOTON,
                    stroke_width=1.6,
                )
            )
        return result

    def build_optical_paths(self, detector: VGroup):
        source = detector.right_stack.get_center()
        targets = [camera.get_left() for camera in detector.right_cameras]
        targets.extend(pmt.get_left() for pmt in detector.right_pmts)
        paths = VGroup(
            *[
                DashedLine(source, target, color=PHOTON, stroke_width=1.05, dash_length=0.07).set_opacity(0.48)
                for target in targets
            ]
        )
        travellers = VGroup()
        pairs = []
        for index, (path, target) in enumerate(zip(paths, targets)):
            photon = Dot(source, radius=0.018 + 0.003 * (index % 2), color=PHOTON)
            travellers.add(photon)
            pairs.append((photon, Line(source, target)))
        return paths, pairs

    def build_readout_panels(self):
        image_box = RoundedRectangle(
            width=3.42,
            height=1.42,
            corner_radius=0.10,
            stroke_color=CYGNUS,
            stroke_width=1.35,
            fill_color=READOUT_PANEL,
            fill_opacity=0.94,
        ).move_to([-2.18, -2.10, 0])
        image_title = label("qCMOS · projected light pattern", color=CYGNUS, scale=0.18, weight="BOLD")
        image_title.next_to(image_box, UP, buff=0.08)
        image_grid = VGroup()
        for x in np.linspace(-3.55, -0.81, 10):
            image_grid.add(Line([x, -2.56, 0], [x, -1.66, 0], color=CYGNUS, stroke_width=0.35).set_opacity(0.12))
        for y in np.linspace(-2.52, -1.70, 5):
            image_grid.add(Line([-3.58, y, 0], [-0.78, y, 0], color=CYGNUS, stroke_width=0.35).set_opacity(0.12))
        image_content = self.build_projected_light_pattern(
            np.array([-2.18, -2.10, 0]),
            width=2.66,
            height=0.78,
        )
        image_note = label("light gradient · charge proxy", color=NUCLEUS, scale=0.16, weight="BOLD")
        image_note.move_to([-2.18, -2.69, 0])
        image_panel = VGroup(image_box, image_grid, image_title, image_note)

        waveform_box = RoundedRectangle(
            width=3.42,
            height=1.42,
            corner_radius=0.10,
            stroke_color=PHOTON,
            stroke_width=1.35,
            fill_color=READOUT_PANEL,
            fill_opacity=0.94,
        ).move_to([1.55, -2.10, 0])
        waveform_title = label("PMTs · time profile → z inclination", color=PHOTON, scale=0.18, weight="BOLD")
        waveform_title.next_to(waveform_box, UP, buff=0.08)
        baseline_y = -2.55
        baseline = Line([0.20, baseline_y, 0], [2.90, baseline_y, 0], color=MUTED, stroke_width=0.8)
        time_label = label("time", color=MUTED, scale=0.16).next_to(baseline, DOWN, buff=0.05)
        waveform_panel = VGroup(waveform_box, waveform_title, baseline, time_label)

        waveform = self.build_time_profile(
            np.array([1.55, -2.15, 0]),
            width=2.64,
            height=0.80,
        )
        provenance = label(
            "One event · two readouts",
            color=FOREGROUND,
            scale=0.20,
        ).move_to([-0.20, -2.92, 0])
        return image_panel, image_content, waveform_panel, waveform, provenance

    def build_projected_light_pattern(
        self,
        centre: np.ndarray,
        width: float,
        height: float,
    ) -> VGroup:
        """Layered qCMOS pattern after diffusion and GEM optical projection."""

        mock = self.illustrated_event()
        points = mock.points - mock.points.mean(axis=0)
        angle = np.deg2rad(-19.0)
        rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        points = points @ rotation.T
        span = np.ptp(points, axis=0)
        scale = min(width / max(span[0], 1e-6), height / max(span[1], 1e-6))
        mapped = np.column_stack(
            (
                centre[0] + scale * points[:, 0],
                centre[1] + scale * points[:, 1],
                np.zeros(len(points)),
            )
        )
        weights = mock.weights / mock.weights.max()
        rng = np.random.default_rng(413)

        # Integrate a diffuse light field onto camera pixels. No lines connect
        # the samples; diffusion and counting fluctuations supply the profile.
        cols, rows = 80, 38
        dx, dy = width/cols, height/rows
        xs = np.linspace(centre[0]-width/2+dx/2, centre[0]+width/2-dx/2, cols)
        ys = np.linspace(centre[1]-height/2+dy/2, centre[1]+height/2-dy/2, rows)
        xx, yy = np.meshgrid(xs, ys)
        field = np.zeros_like(xx)
        colour_field = np.zeros_like(xx)
        mapped = centre + .78*(mapped-centre)
        sigma = width*.022
        for index, (point, weight) in enumerate(zip(mapped, weights)):
            light = weight*np.exp(-((xx-point[0])**2+(yy-point[1])**2)/(2*sigma**2))
            field += light
            colour_field += light*index/max(len(mapped)-1,1)
        fractions = colour_field/np.maximum(field,1e-9)
        field /= max(float(field.max()),1e-9)
        counts = rng.poisson(field*45)
        pixels = VGroup()
        for row in range(rows):
            strip = VGroup()
            for col in range(cols):
                if counts[row,col] < 2:
                    continue
                intensity = min(1.0, counts[row,col]/45)**.65
                colour = interpolate_color(ManimColor(NUCLEUS), ManimColor(CYGNUS), fractions[row,col])
                strip.add(Rectangle(width=dx*.98, height=dy*.98, stroke_width=0,
                                    fill_color=colour, fill_opacity=.95*intensity)
                          .move_to([xx[row,col], yy[row,col], 0]))
            pixels.add(strip)
        return pixels

    def build_time_profile(self, centre: np.ndarray, width: float, height: float) -> VMobject:
        """A repeatable pulse with substructure and baseline fluctuations."""
        samples = np.linspace(0,1,260)
        elapsed = np.maximum(samples-.16,0)
        values = np.exp(-elapsed/.18)-np.exp(-elapsed/.022)
        values += .14*np.exp(-((samples-.32)/.023)**2)
        values += .09*np.exp(-((samples-.46)/.038)**2)
        rng = np.random.default_rng(414)
        noise = np.convolve(rng.normal(size=len(samples)), [.2,.6,.2], mode="same")
        values += noise*(.018+.095*values)
        values /= max(float(values.max()),1e-9)
        baseline = centre[1]-height/2+.03*height
        points = [[centre[0]-width/2+width*t, baseline+height*.82*v,0]
                  for t,v in zip(samples,values)]
        return VMobject(color=PHOTON, stroke_width=2.2).set_points_as_corners(points)

    def mini_image_packet(self, centre: np.ndarray) -> VGroup:
        frame = RoundedRectangle(
            width=0.60,
            height=0.38,
            corner_radius=0.05,
            stroke_color=CYGNUS,
            stroke_width=1.2,
            fill_color=BACKGROUND,
            fill_opacity=0.96,
        ).move_to(centre)
        track = VGroup()
        for index in range(7):
            t = index / 6
            track.add(
                Dot(
                    centre + np.array([-0.20 + 0.065 * index, -0.07 + 0.12 * t + 0.020 * np.sin(index), 0]),
                    radius=0.012 + 0.009 * (1.0 - t),
                    color=interpolate_color(ManimColor(NUCLEUS), ManimColor(CYGNUS), t),
                )
            )
        return VGroup(frame, track)

    def mini_wave_packet(self, centre: np.ndarray) -> VGroup:
        frame = RoundedRectangle(
            width=0.60,
            height=0.38,
            corner_radius=0.05,
            stroke_color=PHOTON,
            stroke_width=1.2,
            fill_color=BACKGROUND,
            fill_opacity=0.96,
        ).move_to(centre)
        wave = self.build_time_profile(centre, width=.46, height=.23)
        wave.set_stroke(width=1.2)
        return VGroup(frame, wave)

    def event_packet(self, centre: np.ndarray, scale: float = 1.0) -> VGroup:
        frame = RoundedRectangle(
            width=0.86 * scale,
            height=0.52 * scale,
            corner_radius=0.07 * scale,
            stroke_color=CYGNUS,
            stroke_width=1.4,
            fill_color=CHAMBER_FILL,
            fill_opacity=0.98,
        ).move_to(centre)
        cyan_bar = Line(
            centre + np.array([-0.29, 0.11, 0]) * scale,
            centre + np.array([0.29, 0.11, 0]) * scale,
            color=CYGNUS,
            stroke_width=2.0,
        )
        gold_bar = Line(
            centre + np.array([-0.29, -0.11, 0]) * scale,
            centre + np.array([0.29, -0.11, 0]) * scale,
            color=PHOTON,
            stroke_width=2.0,
        )
        return VGroup(frame, cyan_bar, gold_bar)

    def build_signal_chain(self) -> VGroup:
        kicker = label("CYGNO-04", color=CYGNUS, scale=0.22, weight="BOLD")
        title = label("Trigger, record and store the event", color=FOREGROUND, scale=0.40, weight="BOLD")
        header = VGroup(kicker, title).arrange(DOWN, aligned_edge=LEFT, buff=0.10)
        header.move_to([-2.35, 3.17, 0])

        image_box = RoundedRectangle(
            width=2.20,
            height=1.25,
            corner_radius=0.10,
            stroke_color=CYGNUS,
            stroke_width=1.35,
            fill_color=PIPELINE_PANEL,
            fill_opacity=0.94,
        ).move_to([-5.18, 0.82, 0])
        image_title = label("qCMOS · x–y image", color=CYGNUS, scale=0.18, weight="BOLD")
        image_title.next_to(image_box, UP, buff=0.09)
        image_content = self.build_projected_light_pattern(
            np.array([-5.18, 0.82, 0]),
            width=1.72,
            height=1.72 * 0.78 / 2.66,
        )

        wave_box = RoundedRectangle(
            width=2.20,
            height=1.00,
            corner_radius=0.10,
            stroke_color=PHOTON,
            stroke_width=1.35,
            fill_color=PIPELINE_PANEL,
            fill_opacity=0.94,
        ).move_to([-5.18, -1.00, 0])
        wave_title = label("PMTs · time profile", color=PHOTON, scale=0.18, weight="BOLD")
        wave_title.next_to(wave_box, UP, buff=0.09)
        wave_baseline = Line([-6.02, -1.30, 0], [-4.34, -1.30, 0], color=MUTED, stroke_width=0.65)
        wave_content = self.build_time_profile(
            np.array([-5.18, -1.00, 0]),
            width=1.66,
            height=0.60,
        )
        image_source = VGroup(image_box, image_title, image_content)
        wave_source = VGroup(wave_box, wave_title, wave_baseline, wave_content)
        sources = VGroup(image_source, wave_source)
        provenance = label("One event · two readouts", color=MUTED, scale=0.18)
        provenance.move_to([-5.18, -1.72, 0])

        daq_centre = np.array([-1.86, 0.0, 0])
        daq = VGroup(
            Circle(
                radius=0.80,
                stroke_color=ELECTRON,
                stroke_width=1.7,
                fill_color=ELECTRON,
                fill_opacity=0.06,
            ).move_to(daq_centre),
            Arc(radius=0.61, start_angle=0.25, angle=5.4, color=CYGNUS, stroke_width=2.0).move_to(daq_centre),
            label("Trigger + DAQ", color=FOREGROUND, scale=0.21, weight="BOLD").move_to(daq_centre + UP * 0.12),
            label("Select + record", color=MUTED, scale=0.16).move_to(daq_centre + DOWN * 0.24),
        )

        image_link = CubicBezier(
            np.array([-4.07, 0.82, 0]),
            np.array([-3.42, 0.82, 0]),
            np.array([-2.98, 0.34, 0]),
            np.array([-2.64, 0.28, 0]),
            color=CYGNUS,
            stroke_width=2.1,
        )
        wave_link = CubicBezier(
            np.array([-4.07, -1.00, 0]),
            np.array([-3.42, -1.00, 0]),
            np.array([-2.98, -0.36, 0]),
            np.array([-2.64, -0.28, 0]),
            color=PHOTON,
            stroke_width=2.1,
        )
        image_path = image_link.copy().set_stroke(opacity=0)
        wave_path = wave_link.copy().set_stroke(opacity=0)
        image_packet = self.mini_image_packet(image_path.get_start()).scale(0.72)
        wave_packet = self.mini_wave_packet(wave_path.get_start()).scale(0.72)

        cloud = self.build_cloud_icon(np.array([0.93, 0.0, 0]), scale=0.78)
        cloud_link = Arrow(
            [-1.03, 0.0, 0],
            [-0.10, 0.0, 0],
            buff=0,
            color=ELECTRON,
            stroke_width=2.5,
            tip_length=0.13,
        )
        event_path = Line([-1.03, 0.0, 0], [-0.10, 0.0, 0]).set_stroke(opacity=0)
        event_packet = self.event_packet(event_path.get_start(), scale=0.48)

        reconstruction_centre = np.array([4.55, 0.0, 0])
        reconstruction_box = RoundedRectangle(
            width=2.35,
            height=2.45,
            corner_radius=0.12,
            stroke_color=NUCLEUS,
            stroke_width=1.45,
            fill_color=PIPELINE_PANEL,
            fill_opacity=0.94,
        ).move_to(reconstruction_centre)
        origin = reconstruction_centre + np.array([-0.64, -0.60, 0])
        axes = VGroup(
            Arrow(origin, origin + np.array([1.20, 0.0, 0]), buff=0, color=CYGNUS, stroke_width=1.4, tip_length=0.10),
            Arrow(origin, origin + np.array([0.0, 1.20, 0]), buff=0, color=ELECTRON, stroke_width=1.4, tip_length=0.10),
            Arrow(origin, origin + np.array([-0.34, 0.48, 0]), buff=0, color=PHOTON, stroke_width=1.4, tip_length=0.10),
        )
        recoil_points, _, recoil_weights = self.event_view_points(
            reconstruction_centre + np.array([-0.65, -0.95, 0]), scale=0.48)
        recoil = VGroup(*[
            Dot(point, radius=0.020 + .018 * weight,
                color=interpolate_color(ManimColor(NUCLEUS), ManimColor(CYGNUS), i/(len(recoil_points)-1)))
            for i, (point, weight) in enumerate(zip(recoil_points, recoil_weights))
        ])
        recoil.add(Line(recoil_points[0] + RIGHT*.08, recoil_points[-1] + RIGHT*.08,
                        color=NUCLEUS, stroke_width=2.0))
        reconstruction_title = label("Offline analysis", color=NUCLEUS, scale=0.22, weight="BOLD")
        reconstruction_title.move_to(reconstruction_centre + UP * 0.94)
        reconstruction = VGroup(reconstruction_box, axes, recoil, reconstruction_title)
        reconstruction_link = Arrow(
            [1.80, 0.0, 0],
            [3.36, 0.0, 0],
            buff=0,
            color=CYGNUS,
            stroke_width=2.5,
            tip_length=0.13,
        )

        local_record = self.event_packet(np.array([-1.86,-1.25,0]), scale=.75)
        record_label = label("Recorded event", color=ELECTRON, scale=.18).next_to(local_record, DOWN, buff=.12)
        local_record.add(record_label)
        archive = VGroup(*[self.event_packet(np.array([.65+.24*i,-1.1-.10*i,0]),scale=.65)
                           for i in range(3)])
        archive_label = label("Stored events", color=CYGNUS, scale=.18).next_to(archive, DOWN, buff=.12)
        archive.add(archive_label)
        group = VGroup(
            header,
            sources,
            provenance,
            daq,
            image_link,
            wave_link,
            cloud,
            cloud_link,
            reconstruction_link,
            reconstruction,
        )
        group.local_record = local_record
        group.archive = archive
        group.header = header
        group.sources = sources
        group.image_source = image_source
        group.wave_source = wave_source
        group.provenance = provenance
        group.daq = daq
        group.image_link = image_link
        group.wave_link = wave_link
        group.image_path = image_path
        group.wave_path = wave_path
        group.image_packet = image_packet
        group.wave_packet = wave_packet
        group.cloud = cloud
        group.cloud_link = cloud_link
        group.event_path = event_path
        group.event_packet = event_packet
        group.reconstruction_link = reconstruction_link
        group.reconstruction = reconstruction
        return group

    def build_cloud_icon(self, centre: np.ndarray, scale: float = 1.0) -> VGroup:
        outline = VMobject(stroke_color=CYGNUS, stroke_width=1.5,
                           fill_color=PIPELINE_PANEL, fill_opacity=1.0)
        outline.set_points_smoothly([
            [-0.80, -0.35, 0], [-0.99, -0.08, 0], [-0.84, 0.26, 0],
            [-0.55, 0.35, 0], [-0.36, 0.70, 0], [0.12, 0.77, 0],
            [0.48, 0.46, 0], [0.83, 0.32, 0], [0.96, -0.05, 0],
            [0.75, -0.35, 0], [-0.80, -0.35, 0],
        ])
        outline.close_path()
        caption = label("INFN Cloud", color=FOREGROUND, scale=0.25, weight="BOLD")
        caption.move_to([0.0, .27, 0])
        storage = label("Data storage", color=CYGNUS, scale=.20).move_to([0,-.06,0])
        return VGroup(outline, caption, storage).scale(scale).shift(centre)

    def illustrated_event(self):
        """One deterministic optical event, shared by all presentations."""
        if not hasattr(self, "_optical_event"):
            self._optical_event = diffuse_track(simulate_nr_track(seed=410), sigma=0.060, seed=412)
        return self._optical_event

    def event_view_points(self, origin, scale=1.0):
        """Qualitative depth view of the same optical samples, not a fitted track."""
        event = self.illustrated_event()
        angle = np.deg2rad(-19.0)
        rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        xy = event.points @ rotation.T
        xy = (xy - xy.min(axis=0)) / max(float(np.ptp(xy, axis=0).max()), 1e-6)
        depth = np.linspace(0.08, 0.60, len(xy))
        ground = np.column_stack((0.35 + 2.8 * xy[:, 0] - 0.58 * depth,
                                  0.80 * depth, np.zeros(len(xy))))
        points = ground + np.column_stack((np.zeros(len(xy)), 0.20 + 2.8 * xy[:, 1], np.zeros(len(xy))))
        return origin + scale * points, origin + scale * ground, event.weights / event.weights.max()

    def show_gem_amplification(self, detector, primary_electrons):
        """Multiply charge at the actual foils, without changing reference frame."""
        cloud = primary_electrons
        centre_y = float(np.mean([dot.get_y() for dot in cloud]))
        rng = np.random.default_rng(405)
        for i, (foil, count) in enumerate(zip(detector.right_stack, (18, 45, 90))):
            x = foil.get_x()
            self.play(cloud.animate.move_to([x-.07, centre_y, 0]), run_time=.60)
            next_cloud = VGroup(*[
                electron_marker((.014, .012, .010)[i]).move_to(
                    [x+.055+rng.uniform(-.025,.025), rng.normal(centre_y,.12+.035*i),0])
                for _ in range(count)
            ])
            flash = self.photon_flash(np.array([x, centre_y, 0]), 10+i*3)
            old_cloud = cloud
            self.play(ReplacementTransform(cloud, next_cloud), FadeIn(flash),
                      Indicate(foil, color=PHOTON, scale_factor=1.03), run_time=.85)
            self.remove(*old_cloud.get_family())
            self.play(FadeOut(flash), run_time=.35)
            cloud = next_cloud
        self.wait(.8)
        flash = self.photon_flash(cloud.get_center(), 18)
        self.play(FadeIn(flash), run_time=.35)
        return cloud, flash

    def show_reconstruction(self, chain: VGroup):
        tableau = self.build_reconstruction_tableau()
        links = VGroup(
            Arrow(chain.image_source.get_right(), tableau.direction_frame.get_left() + UP * 0.70,
                  buff=0.12, color=CYGNUS, stroke_width=2.0, tip_length=0.12),
            Arrow(chain.wave_source.get_right(), tableau.direction_frame.get_left() + DOWN * 0.65,
                  buff=0.12, color=PHOTON, stroke_width=2.0, tip_length=0.12),
        )
        self.play(
            Succession(FadeOut(chain.header, run_time=0.8), FadeIn(tableau.header, run_time=1.0)),
            FadeOut(VGroup(chain.daq, chain.local_record, chain.archive, chain.image_link, chain.wave_link,
                           chain.cloud, chain.cloud_link, chain.reconstruction_link,
                           chain.reconstruction)),
            FadeIn(tableau.direction_frame), Create(links),
            run_time=1.8,
        )
        self.play(FadeIn(tableau.axes), FadeIn(tableau.perspective_grid), run_time=1.0)
        self.play(
            LaggedStart(*[Create(line) for line in tableau.depth_guides], lag_ratio=0.08),
            LaggedStart(*[FadeIn(voxel, scale=0.65) for voxel in tableau.voxels], lag_ratio=0.045),
            run_time=2.4,
        )
        self.play(Create(tableau.unoriented_axis), FadeIn(tableau.axis_caption), run_time=1.0)
        self.wait(1.5)
        self.play(
            ReplacementTransform(tableau.unoriented_axis, tableau.direction_arrow),
            FadeOut(tableau.axis_caption),
            FadeIn(tableau.sense_caption),
            FadeIn(tableau.tail_label), FadeIn(tableau.head_label),
            run_time=1.5,
        )
        self.wait(1.5)
        self.play(FadeIn(tableau.classification_title), FadeIn(tableau.er_card),
                  FadeIn(tableau.nr_card), run_time=1.4)
        self.play(Indicate(tableau.nr_card, color=NUCLEUS), FadeIn(tableau.outcome), run_time=1.0)
        self.play(FadeIn(tableau.summary), run_time=0.8)
        self.wait(5.0)
        show_brand_outro(self)

    def build_reconstruction_tableau(self) -> VGroup:
        header = VGroup(
            label("CYGNO-04", color=CYGNUS, scale=0.23, weight="BOLD"),
            label("Offline analysis · full 3D track", color=FOREGROUND, scale=0.43, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.10).move_to([0.0, 3.22, 0])
        box = RoundedRectangle(width=7.65, height=4.30, corner_radius=0.13,
                               stroke_color=NUCLEUS, stroke_width=1.5,
                               fill_color=PIPELINE_PANEL, fill_opacity=0.98).move_to([2.0, 0.25, 0])
        title = label("3D recoil axis", color=NUCLEUS, scale=0.30, weight="BOLD").move_to([2.0, 2.06, 0])
        caption = label("Camera image + PMT timing", color=FOREGROUND, scale=0.21)
        caption.move_to([2.0, -1.64, 0])
        direction_frame = VGroup(box, title, caption)
        origin = np.array([0.18, -1.40, 0])
        ends = (origin + [3.45, 0, 0], origin + [0, 3.0, 0], origin + [-0.88, .90, 0])
        axes = VGroup()
        for name, end, colour, side in zip(("x", "y", "z"), ends, (CYGNUS, ELECTRON, PHOTON), (RIGHT, UP, LEFT)):
            axis = Arrow(origin, end, buff=0, color=colour, stroke_width=1.5, tip_length=.12)
            axes.add(axis, label(name, color=colour, scale=.22, weight="BOLD").next_to(end, side, buff=.06))
        grid = VGroup(*[
            Line(origin + [x, 0, 0], origin + [x-.88, .90, 0], color=MUTED, stroke_width=.6).set_opacity(.20)
            for x in np.linspace(.45, 3.35, 7)
        ])
        points, ground, weights = self.event_view_points(origin)
        voxels, guides = VGroup(), VGroup()
        for i, (point, floor, weight) in enumerate(zip(points, ground, weights)):
            colour = interpolate_color(ManimColor(NUCLEUS), ManimColor(CYGNUS), i/(len(points)-1))
            voxels.add(VGroup(
                Circle(radius=.065+.025*weight, stroke_width=0, fill_color=colour, fill_opacity=.12).move_to(point),
                Dot(point, radius=.025+.025*weight, color=colour),
            ))
            if i % 5 == 0:
                guides.add(DashedLine(floor, point, color=ELECTRON, stroke_width=.8, dash_length=.05).set_opacity(.30))
        offset = RIGHT * .24
        unoriented_axis = Line(points[0]+offset, points[-1]+offset, color=NUCLEUS, stroke_width=2.8)
        direction_arrow = Arrow(points[0]+offset, points[-1]+offset, buff=0,
                                color=NUCLEUS, stroke_width=3.0, tip_length=.16)
        axis_caption = label("Recoil axis\nwithout a sense", color=FOREGROUND, scale=.24, weight="BOLD").move_to([4.32, .70, 0])
        sense_caption = label("Sense estimate\nstatistical", color=NUCLEUS, scale=.24, weight="BOLD").move_to(axis_caption)
        tail_text = label("Start / tail", color=NUCLEUS, scale=.21, weight="BOLD").move_to([-.90, 1.12, 0])
        tail = VGroup(tail_text, DashedLine(tail_text.get_right()+RIGHT*.08, points[0]+LEFT*.08,
                                          color=NUCLEUS, stroke_width=.9, dash_length=.05))
        head = label("Stop / head", color=CYGNUS, scale=.21, weight="BOLD").next_to(points[-1], DOWN, buff=.18).shift(RIGHT*.50)
        classification_title = label("Compare recoil topologies", color=FOREGROUND, scale=.24, weight="BOLD").move_to([2.0, -2.24, 0])
        er_box = RoundedRectangle(width=3.35, height=.70, corner_radius=.09, color=MUTED,
                                  stroke_width=1.2, fill_color=PIPELINE_PANEL, fill_opacity=.9).move_to([.06, -2.84, 0])
        nr_box = er_box.copy().set_stroke(NUCLEUS).move_to([3.93, -2.84, 0])
        er_label = label("ER-like\nDiffuse / tortuous", color=MUTED, scale=.21, weight="BOLD").move_to(er_box.get_center()+RIGHT*.38)
        nr_label = label("NR-like\nCompact / dense", color=NUCLEUS, scale=.21, weight="BOLD").move_to(nr_box.get_center()+RIGHT*.38)
        er_icon = VMobject(color=MUTED, stroke_width=1.5)
        er_icon.set_points_smoothly([[0,0,0],[.10,.25,0],[.22,-.06,0],[.35,.20,0],[.52,.02,0]])
        er_icon.move_to(er_box.get_left()+RIGHT*.48)
        nr_icon = voxels.copy().set_height(.36).move_to(nr_box.get_left()+RIGHT*.48)
        er_card, nr_card = VGroup(er_box, er_icon, er_label), VGroup(nr_box, nr_icon, nr_label)
        outcome = label("Nuclear recoil", color=NUCLEUS, scale=.21, weight="BOLD").next_to(nr_box, DOWN, buff=.13)
        summary = label("Recoil axis + a statistical sense estimate", color=FOREGROUND, scale=.25, weight="BOLD")
        summary.move_to([-3.0, -3.52, 0])
        group = VGroup(header, direction_frame, axes, grid, voxels, guides,
                       unoriented_axis, direction_arrow, axis_caption, sense_caption,
                       tail, head, classification_title, er_card, nr_card, outcome, summary)
        for key, value in dict(header=header, direction_frame=direction_frame, axes=axes,
                               perspective_grid=grid, voxels=voxels, depth_guides=guides,
                               unoriented_axis=unoriented_axis, direction_arrow=direction_arrow,
                               axis_caption=axis_caption, sense_caption=sense_caption,
                               tail_label=tail, head_label=head, classification_title=classification_title,
                               er_card=er_card, nr_card=nr_card, outcome=outcome, summary=summary).items():
            setattr(group, key, value)
        return group

    def phase_label(self, text: str, color: str) -> VGroup:
        caption = Text(text, font=FONT, color=color, weight="BOLD").scale(0.23)
        box = RoundedRectangle(
            width=caption.width + 0.30,
            height=caption.height + 0.16,
            corner_radius=0.07,
            stroke_color=color,
            stroke_width=1.1,
            fill_color=BACKGROUND,
            fill_opacity=0.90,
        )
        group = VGroup(box, caption)
        group.move_to([-1.70, -2.23, 0])
        return group
