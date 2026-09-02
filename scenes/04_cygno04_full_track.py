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
    SurroundingRectangle,
    Text,
    Transform,
    VGroup,
    VMobject,
    Write,
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
        self.play(
            Create(recoil_path),
            MoveAlongPath(recoil_nucleus, recoil_path),
            LaggedStart(*[FadeIn(dot) for dot in primary_electrons], lag_ratio=0.045),
            run_time=3.0,
        )
        self.play(FadeOut(impact), FadeOut(recoil_nucleus), FadeIn(asymmetry_note), run_time=0.85)
        self.wait(2.3)

        next_phase = self.phase_label("2 · Electron drift + diffusion", ELECTRON)
        next_phase.scale(0.82).move_to([0.0, 1.82, 0.0])
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
            np.array([0.68, 1.20, 0]),
            np.array([-1.15, 1.20, 0]),
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

        current_cloud = primary_electrons
        stage_centres = [foil.get_center()[0] for foil in detector.right_stack]
        avalanche_rng = np.random.default_rng(405)
        stage_counts = (24, 52, 96)
        stage_spreads = (0.18, 0.24, 0.31)
        final_flash = VGroup()
        for stage_index, (stage_x, count, spread) in enumerate(zip(stage_centres, stage_counts, stage_spreads)):
            centre_y = float(np.mean([dot.get_center()[1] for dot in current_cloud]))
            next_cloud = VGroup(
                *[
                    electron_marker((0.016, 0.012, 0.009)[stage_index]).move_to(
                        [
                            stage_x + 0.055,
                            centre_y + avalanche_rng.normal(0.0, spread),
                            0,
                        ]
                    )
                    for _ in range(count)
                ]
            )
            flash = self.photon_flash(np.array([stage_x, centre_y, 0]), 10 + 4 * stage_index)
            self.play(
                ReplacementTransform(current_cloud, next_cloud),
                FadeIn(flash, lag_ratio=0.025),
                run_time=1.0,
            )
            if stage_index < 2:
                self.play(FadeOut(flash), run_time=0.38)
            else:
                final_flash = flash
            current_cloud = next_cloud

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
        self.play(FadeIn(image_panel), FadeIn(waveform_panel), run_time=1.05)
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
        self.play(
            Restore(self.camera.frame),
            FadeOut(active_detector),
            FadeOut(recoil_path),
            FadeOut(current_cloud),
            FadeOut(phase),
            FadeOut(image_panel),
            FadeOut(image_content),
            FadeOut(waveform_panel),
            FadeOut(waveform),
            FadeOut(provenance),
            FadeIn(chain.header, shift=DOWN * 0.08),
            run_time=2.4,
        )
        self.play(
            FadeIn(chain.sources, shift=RIGHT * 0.10),
            FadeIn(chain.provenance, shift=UP * 0.05),
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
        self.play(
            FadeOut(chain.image_packet),
            FadeOut(chain.wave_packet),
            Indicate(chain.daq, color=ELECTRON),
            Create(chain.cloud_link),
            FadeIn(chain.cloud, shift=LEFT * 0.10),
            FadeIn(chain.event_packet),
            run_time=1.4,
        )
        self.play(MoveAlongPath(chain.event_packet, chain.event_path), run_time=2.0)
        self.play(
            FadeOut(chain.event_packet),
            Indicate(chain.cloud, color=CYGNUS),
            Create(chain.reconstruction_link),
            FadeIn(chain.reconstruction, shift=LEFT * 0.10),
            run_time=1.7,
        )
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
        cathode_label.next_to(cathode, UP, buff=0.08)
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
            seed=412,
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
            "Illustrative detector response",
            color=MUTED,
            scale=0.18,
        ).move_to([-0.20, -2.92, 0])
        return image_panel, image_content, waveform_panel, waveform, provenance

    def build_projected_light_pattern(
        self,
        centre: np.ndarray,
        width: float,
        height: float,
        seed: int,
    ) -> VGroup:
        """Layered qCMOS pattern after diffusion and GEM optical projection."""

        mock = diffuse_track(simulate_nr_track(seed=410), sigma=0.060, seed=seed)
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
        rng = np.random.default_rng(seed + 1)

        glow = VGroup()
        spine = VGroup()
        grains = VGroup()
        for index, (point, weight) in enumerate(zip(mapped, weights)):
            fraction = index / max(len(mapped) - 1, 1)
            colour = interpolate_color(ManimColor(NUCLEUS), ManimColor(CYGNUS), fraction)
            glow.add(
                Circle(
                    radius=0.040 + 0.040 * weight,
                    stroke_width=0,
                    fill_color=colour,
                    fill_opacity=0.055 + 0.075 * weight,
                ).move_to(point)
            )
            grains.add(
                Dot(point, radius=0.010 + 0.017 * weight, color=colour).set_opacity(0.55 + 0.42 * weight)
            )
            # A few low-opacity photoelectron grains give the image a camera
            # texture without changing the simulated longitudinal profile.
            for _ in range(1 + int(2 * weight)):
                offset = np.array(
                    [rng.normal(0.0, 0.020), rng.normal(0.0, 0.027), 0]
                )
                grains.add(
                    Dot(point + offset, radius=0.006 + 0.007 * weight, color=PHOTON).set_opacity(0.20 + 0.36 * weight)
                )
            if index:
                spine.add(
                    Line(mapped[index - 1], point, color=colour, stroke_width=4.5 + 2.5 * weight).set_opacity(0.11)
                )
                spine.add(
                    Line(mapped[index - 1], point, color=colour, stroke_width=1.0 + 1.2 * weight).set_opacity(0.58)
                )
        return VGroup(glow, spine, grains)

    def build_time_profile(self, centre: np.ndarray, width: float, height: float) -> VMobject:
        """Return a single, unfilled PMT pulse profile.

        A difference of exponentials gives the conventional fast rise and
        slower decay.  Keep this as one clean trace: the PMT timing panel is a
        schematic data product, not a multi-channel oscilloscope animation.
        """

        samples = np.linspace(0.0, 1.0, 140)
        start = 0.16
        tau_rise = 0.022
        tau_fall = 0.18
        values = np.zeros_like(samples)
        after_start = samples > start
        elapsed = samples[after_start] - start
        values[after_start] = np.exp(-elapsed / tau_fall) - np.exp(-elapsed / tau_rise)
        values /= max(float(values.max()), 1e-9)

        baseline_y = centre[1] - height / 2
        points = [
            [
                centre[0] - width / 2 + width * t,
                baseline_y + height * 0.82 * pulse,
                0,
            ]
            for t, pulse in zip(samples, values)
        ]
        trace = VMobject(color=PHOTON, stroke_width=2.6)
        trace.set_points_smoothly(points)
        return trace

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
        wave = VMobject(color=PHOTON, stroke_width=1.5)
        wave.set_points_smoothly(
            [
                centre + np.array([-0.23, -0.09, 0]),
                centre + np.array([-0.12, -0.09, 0]),
                centre + np.array([-0.05, 0.02, 0]),
                centre + np.array([0.03, 0.12, 0]),
                centre + np.array([0.11, -0.01, 0]),
                centre + np.array([0.22, -0.09, 0]),
            ]
        )
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
        title = label("From optical signals to a 3D recoil axis", color=FOREGROUND, scale=0.40, weight="BOLD")
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
            height=0.72,
            seed=416,
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
        sources = VGroup(
            image_box,
            image_title,
            image_content,
            wave_box,
            wave_title,
            wave_baseline,
            wave_content,
        )
        provenance = label("Illustrative detector response", color=MUTED, scale=0.18)
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
            label("DAQ", color=FOREGROUND, scale=0.25, weight="BOLD").move_to(daq_centre + UP * 0.12),
            label("event building", color=MUTED, scale=0.15).move_to(daq_centre + DOWN * 0.24),
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
        recoil_points = [
            reconstruction_centre + np.array([-0.54 + 0.14 * index, -0.30 + 0.105 * index, 0])
            for index in range(9)
        ]
        recoil = VGroup(
            *[
                Dot(
                    point,
                    radius=0.035 - 0.014 * index / 8,
                    color=interpolate_color(ManimColor(NUCLEUS), ManimColor(CYGNUS), index / 8),
                )
                for index, point in enumerate(recoil_points)
            ],
            Line(
                recoil_points[0] + UP * 0.14,
                recoil_points[-1] + UP * 0.14,
                color=NUCLEUS,
                stroke_width=2.4,
            ),
        )
        reconstruction_title = label("3D recoil axis", color=NUCLEUS, scale=0.22, weight="BOLD")
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
        group.header = header
        group.sources = sources
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
        cloud = VGroup(
            Circle(
                radius=0.48 * scale,
                stroke_color=CYGNUS,
                stroke_width=1.4,
                fill_color=CYGNUS,
                fill_opacity=0.14,
            ).move_to(centre + np.array([-0.45, 0.12, 0]) * scale),
            Circle(
                radius=0.62 * scale,
                stroke_color=CYGNUS,
                stroke_width=1.4,
                fill_color=CYGNUS,
                fill_opacity=0.14,
            ).move_to(centre + np.array([0.0, 0.24, 0]) * scale),
            Circle(
                radius=0.45 * scale,
                stroke_color=CYGNUS,
                stroke_width=1.4,
                fill_color=CYGNUS,
                fill_opacity=0.14,
            ).move_to(centre + np.array([0.47, 0.10, 0]) * scale),
            RoundedRectangle(
                width=1.80 * scale,
                height=0.68 * scale,
                corner_radius=0.25 * scale,
                stroke_color=CYGNUS,
                stroke_width=1.4,
                fill_color=CYGNUS,
                fill_opacity=0.14,
            ).move_to(centre + np.array([0.0, -0.18, 0]) * scale),
        )
        cloud.add(label("INFN Cloud", color=FOREGROUND, scale=0.23 * scale, weight="BOLD").move_to(centre + UP * 0.18 * scale))
        return cloud

    def show_reconstruction(self, chain: VGroup):
        tableau = self.build_reconstruction_tableau()
        detail_link = Arrow(
            chain.cloud.get_right(),
            tableau.direction_frame[0].get_left(),
            buff=0.08,
            color=CYGNUS,
            stroke_width=2.5,
            tip_length=0.12,
        )
        self.play(
            ReplacementTransform(chain.header, tableau.header),
            ReplacementTransform(chain.reconstruction_link, detail_link),
            FadeOut(chain.reconstruction, shift=RIGHT * 0.10),
            run_time=1.6,
        )

        self.play(
            FadeIn(tableau.direction_frame, shift=LEFT * 0.10),
            FadeIn(tableau.perspective_grid),
            LaggedStart(*[Create(axis) for axis in tableau.axes], lag_ratio=0.12),
            run_time=2.0,
        )
        self.play(
            LaggedStart(*[Create(line) for line in tableau.depth_guides], lag_ratio=0.08),
            LaggedStart(*[FadeIn(voxel, scale=0.65) for voxel in tableau.voxels], lag_ratio=0.07),
            run_time=2.45,
        )
        self.play(
            Create(tableau.direction_arrow),
            FadeIn(tableau.tail_label, shift=LEFT * 0.05),
            FadeIn(tableau.head_label, shift=RIGHT * 0.05),
            FadeIn(tableau.direction_caption, shift=UP * 0.05),
            run_time=1.65,
        )
        self.wait(1.5)

        self.play(
            FadeIn(tableau.classification_title, shift=UP * 0.06),
            FadeIn(tableau.er_card, shift=RIGHT * 0.08),
            FadeIn(tableau.nr_card, shift=LEFT * 0.08),
            Create(tableau.classification_arrow),
            run_time=1.75,
        )
        self.play(
            Indicate(tableau.nr_card, color=NUCLEUS),
            FadeIn(tableau.outcome, shift=UP * 0.05),
            run_time=1.15,
        )
        self.play(FadeIn(tableau.summary, shift=UP * 0.08), run_time=0.95)
        self.wait(5.0)
        show_brand_outro(self)

    def build_reconstruction_tableau(self) -> VGroup:
        kicker = label("From INFN Cloud", color=CYGNUS, scale=0.23, weight="BOLD")
        title = label(
            "Joint 3D reconstruction",
            color=FOREGROUND,
            scale=0.43,
            weight="BOLD",
        )
        header = VGroup(kicker, title).arrange(DOWN, buff=0.10).move_to([0.0, 3.26, 0])

        direction_box = RoundedRectangle(
            width=4.50,
            height=3.38,
            corner_radius=0.13,
            stroke_color=NUCLEUS,
            stroke_width=1.45,
            fill_color=PIPELINE_PANEL,
            fill_opacity=0.95,
        ).move_to([3.38, 0.40, 0])
        direction_title = label("3D recoil axis + sense estimate", color=NUCLEUS, scale=0.24, weight="BOLD")
        direction_title.move_to([3.38, 1.86, 0])
        direction_frame = VGroup(direction_box, direction_title)

        origin = np.array([2.05, -0.82, 0])
        x_axis = Arrow(origin, origin + np.array([2.50, 0.0, 0]), buff=0, color=CYGNUS, stroke_width=1.7, tip_length=0.12)
        y_axis = Arrow(origin, origin + np.array([0.0, 2.20, 0]), buff=0, color=ELECTRON, stroke_width=1.7, tip_length=0.12)
        z_axis = Arrow(origin, origin + np.array([-0.72, 1.02, 0]), buff=0, color=PHOTON, stroke_width=1.7, tip_length=0.12)
        axis_labels = VGroup(
            label("x", color=CYGNUS, scale=0.18, weight="BOLD").next_to(x_axis.get_end(), RIGHT, buff=0.05),
            label("y", color=ELECTRON, scale=0.18, weight="BOLD").next_to(y_axis.get_end(), UP, buff=0.04),
            label("z", color=PHOTON, scale=0.18, weight="BOLD").next_to(z_axis.get_end(), LEFT, buff=0.04),
        )
        axes = VGroup(x_axis, y_axis, z_axis, axis_labels)

        perspective_grid = VGroup()
        for x_fraction in (0.25, 0.50, 0.75, 1.0):
            start = origin + np.array([2.40 * x_fraction, 0.0, 0])
            perspective_grid.add(
                Line(start, start + np.array([-0.66, 0.94, 0]), color=MUTED, stroke_width=0.55).set_opacity(0.16)
            )
        for z_fraction in (0.25, 0.50, 0.75, 1.0):
            start = origin + np.array([-0.66 * z_fraction, 0.94 * z_fraction, 0])
            perspective_grid.add(
                Line(start, start + np.array([2.40, 0.0, 0]), color=MUTED, stroke_width=0.55).set_opacity(0.16)
            )

        ex = np.array([1.0, 0.0, 0])
        ey = np.array([0.0, 1.0, 0])
        ez = np.array([-0.58, 0.80, 0])
        track_points = []
        ground_points = []
        voxels = VGroup()
        depth_guides = VGroup()
        for index, t in enumerate(np.linspace(0.0, 1.0, 17)):
            x_value = 0.32 + 2.50 * t
            y_value = 0.22 + 0.92 * t + 0.075 * np.sin(3.2 * np.pi * t)
            z_value = 0.10 + 0.68 * t + 0.055 * np.sin(2.2 * np.pi * t)
            ground = origin + x_value * ex + z_value * ez
            point = ground + y_value * ey
            track_points.append(point)
            ground_points.append(ground)
            colour = interpolate_color(ManimColor(NUCLEUS), ManimColor(CYGNUS), t)
            charge_weight = 1.0 - 0.62 * t
            halo = Circle(
                radius=0.070 + 0.030 * charge_weight,
                stroke_width=0,
                fill_color=colour,
                fill_opacity=0.10,
            ).move_to(point)
            core = Dot(point, radius=0.020 + 0.020 * charge_weight, color=colour).set_opacity(0.94)
            voxels.add(VGroup(halo, core))
            if index in (0, 4, 8, 12, 16):
                depth_guides.add(
                    DashedLine(
                        ground,
                        point,
                        color=ELECTRON,
                        stroke_width=0.8,
                        dash_length=0.045,
                    ).set_opacity(0.30)
                )
        arrow_offset = np.array([0.0, 0.15, 0])
        direction_arrow = Arrow(
            track_points[0] + arrow_offset,
            track_points[-1] + arrow_offset,
            buff=0.03,
            color=NUCLEUS,
            stroke_width=3.6,
            tip_length=0.18,
        )
        tail_label = label("Tail", color=NUCLEUS, scale=0.19, weight="BOLD")
        tail_label.move_to(track_points[0] + np.array([0.22, -0.17, 0]))
        head_label = label("Head", color=CYGNUS, scale=0.19, weight="BOLD")
        head_label.next_to(track_points[-1], RIGHT, buff=0.10).shift(UP * 0.10)
        direction_caption = label(
            "x–y + z · charge asymmetry → head–tail estimate",
            color=FOREGROUND,
            scale=0.18,
            weight="BOLD",
        ).move_to([3.38, -1.05, 0])
        VGroup(
            direction_frame,
            perspective_grid,
            axes,
            depth_guides,
            voxels,
            direction_arrow,
            tail_label,
            head_label,
            direction_caption,
        ).shift(RIGHT * 0.92)

        classification_title = label(
            "ER / NR topology separation",
            color=FOREGROUND,
            scale=0.22,
            weight="BOLD",
        ).move_to([2.25, -1.73, 0])
        er_box = RoundedRectangle(
            width=2.45,
            height=0.92,
            corner_radius=0.09,
            stroke_color=MUTED,
            stroke_width=1.15,
            fill_color=MUTED,
            fill_opacity=0.055,
        ).move_to([0.72, -2.50, 0])
        er_track = VMobject(color=MUTED, stroke_width=1.7)
        er_track.set_points_smoothly(
            [
                [-0.30, -2.60, 0],
                [-0.18, -2.36, 0],
                [-0.05, -2.65, 0],
                [0.11, -2.33, 0],
                [0.30, -2.58, 0],
            ]
        )
        er_card = VGroup(
            er_box,
            er_track,
            label("ER-like\nDiffuse / tortuous", color=MUTED, scale=0.18, weight="BOLD").move_to([1.20, -2.50, 0]),
        )

        nr_box = RoundedRectangle(
            width=2.55,
            height=0.92,
            corner_radius=0.09,
            stroke_color=NUCLEUS,
            stroke_width=1.55,
            fill_color=NUCLEUS,
            fill_opacity=0.08,
        ).move_to([3.85, -2.50, 0])
        nr_icon = VGroup()
        for index in range(8):
            t = index / 7
            nr_icon.add(
                Dot(
                    [3.02 + 0.085 * index, -2.61 + 0.18 * t, 0],
                    radius=0.025 - 0.009 * t,
                    color=interpolate_color(ManimColor(NUCLEUS), ManimColor(CYGNUS), t),
                )
            )
        nr_card = VGroup(
            nr_box,
            nr_icon,
            label("NR-like\nCompact / dense", color=NUCLEUS, scale=0.18, weight="BOLD").move_to([4.38, -2.50, 0]),
        )
        classification_arrow = Arrow(
            [2.08, -2.50, 0],
            [2.55, -2.50, 0],
            buff=0,
            color=ELECTRON,
            stroke_width=2.0,
            tip_length=0.11,
        )
        outcome_text = label("NR-like topology", color=FOREGROUND, scale=0.18, weight="BOLD")
        outcome_box = SurroundingRectangle(
            outcome_text,
            color=NUCLEUS,
            buff=0.08,
            corner_radius=0.05,
            fill_color=BACKGROUND,
            fill_opacity=0.94,
            stroke_width=1.0,
        )
        outcome = VGroup(outcome_box, outcome_text).move_to([3.85, -3.12, 0])
        summary = label(
            "3D recoil axis · head–tail estimate",
            color=NUCLEUS,
            scale=0.28,
            weight="BOLD",
        ).move_to([-1.45, -3.38, 0])

        group = VGroup(
            header,
            direction_frame,
            perspective_grid,
            axes,
            depth_guides,
            voxels,
            direction_arrow,
            tail_label,
            head_label,
            direction_caption,
            classification_title,
            er_card,
            nr_card,
            classification_arrow,
            outcome,
            summary,
        )
        group.header = header
        group.direction_frame = direction_frame
        group.perspective_grid = perspective_grid
        group.axes = axes
        group.depth_guides = depth_guides
        group.voxels = voxels
        group.direction_arrow = direction_arrow
        group.tail_label = tail_label
        group.head_label = head_label
        group.direction_caption = direction_caption
        group.classification_title = classification_title
        group.er_card = er_card
        group.nr_card = nr_card
        group.classification_arrow = classification_arrow
        group.outcome = outcome
        group.summary = summary
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
