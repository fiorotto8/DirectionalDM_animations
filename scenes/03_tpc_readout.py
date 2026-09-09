from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circle,
    Create,
    CubicBezier,
    DashedLine,
    Dot,
    DoubleArrow,
    Ellipse,
    FadeIn,
    FadeOut,
    Indicate,
    LaggedStart,
    Line,
    MoveAlongPath,
    Rectangle,
    ReplacementTransform,
    RoundedRectangle,
    Transform,
    VGroup,
    VMobject,
    Write,
)

# Manim loads scene modules with ``scenes/`` at the front of sys.path.  Add the
# repository root so this file remains directly renderable from any directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cygno_anim.detector import camera_icon, gem_stack, pmt_icon
from cygno_anim.events import diffuse_track, simulate_nr_track
from cygno_anim.branding import add_brand_signature, show_brand_outro
from cygno_anim.config import (
    ConfigurationError,
    load_science,
    require_positive_integer,
)
from cygno_anim.visuals import (
    CHAMBER_FILL,
    CYGNUS,
    ELECTRON,
    FIELD,
    FOREGROUND,
    GEM,
    MUTED,
    NUCLEUS,
    PHOTON,
    READOUT_PANEL,
    ScientificScene,
    electron_marker,
    label,
    semantic_arrow,
)


class TPCReadout(ScientificScene):
    """CAD-informed functional view with illustrative microscopic scales."""

    def construct(self):
        self.science = load_science(include_local=False)
        reconstruction_default = self.science["conventions"][
            "reconstructed_track_default"
        ]
        if reconstruction_default != "unoriented_axis":
            raise ConfigurationError(
                f"Unsupported reconstruction convention: {reconstruction_default!r}"
            )
        add_brand_signature(self)
        title = self.title_block("CYGNO-04", "From ionization to optical readout")
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=1.15)

        overview = self.build_cad_overview()
        overview_label = label("CYGNO-04 LAYOUT", color=FOREGROUND, scale=0.30, weight="BOLD")
        overview_label.next_to(overview, DOWN, buff=0.25)

        self.play(FadeIn(overview, lag_ratio=0.04), Write(overview_label), run_time=2.2)
        # Let the complete detector overview settle before entering the drift view.
        self.wait(2.7)

        self.play(
            FadeOut(overview),
            FadeOut(overview_label),
            run_time=1.1,
        )

        chamber, cathode, stack, recoil, electrons = self.build_half_chamber()
        step = label("1  DRIFT + DIFFUSION", color=ELECTRON, scale=0.28, weight="BOLD")
        step.move_to([0, 2.75, 0])
        primary_note = label("asymmetric ionization track", color=NUCLEUS, scale=0.24, weight="BOLD")
        primary_note.next_to(recoil, UP, buff=0.18)

        self.play(FadeIn(chamber), Create(cathode), FadeIn(stack), FadeIn(step), run_time=1.4)
        self.play(Create(recoil), FadeIn(electrons, lag_ratio=0.035), FadeIn(primary_note), run_time=1.5)

        e_field = semantic_arrow(
            np.array([0.4, 1.55, 0]),
            np.array([-3.35, 1.55, 0]),
            "conventional electric field  E",
            FIELD,
            label_direction=UP,
            stroke_width=3.0,
        )
        e_drift = semantic_arrow(
            np.array([-3.35, -1.48, 0]),
            np.array([0.4, -1.48, 0]),
            "electron drift",
            ELECTRON,
            label_direction=DOWN,
            stroke_width=3.4,
        )
        e_field[1].scale(1.12)
        e_drift[1].scale(1.12)
        self.play(Create(e_field[0]), FadeIn(e_field[1]), Create(e_drift[0]), FadeIn(e_drift[1]), run_time=1.4)
        self.wait(0.9)

        drift_animations = []
        rng_drift = np.random.default_rng(307)
        start_y = np.array([dot.get_center()[1] for dot in electrons])
        end_y = start_y + rng_drift.normal(0.0, 0.27, len(electrons))
        end_x = rng_drift.uniform(-0.10, 0.25, len(electrons))
        for index, (dot, x_end, y_end) in enumerate(zip(electrons, end_x, end_y)):
            start = dot.get_center()
            path = CubicBezier(
                start,
                start + np.array([1.10, rng_drift.normal(0.0, 0.24), 0]),
                np.array([-0.60, y_end + rng_drift.normal(0.0, 0.22), 0]),
                np.array([x_end, y_end, 0]),
            )
            drift_animations.append(MoveAlongPath(dot, path, run_time=3.1))

        self.play(
            LaggedStart(*drift_animations, lag_ratio=0.045),
            recoil.animate.set_stroke(opacity=0.18),
            FadeOut(primary_note, run_time=1.4),
            run_time=3.2,
        )
        cloud_envelope = Ellipse(
            width=0.78,
            height=max(1.20, float(np.ptp(end_y) + 0.38)),
            stroke_color=ELECTRON,
            stroke_width=1.4,
            fill_color=ELECTRON,
            fill_opacity=0.045,
        ).move_to([0.08, float(np.mean(end_y)), 0])
        cloud_note = label("diffused electron cloud", color=ELECTRON, scale=0.24, weight="BOLD")
        cloud_note.next_to(cloud_envelope, UP, buff=0.20).shift(LEFT * 0.52)
        self.play(Create(cloud_envelope), FadeIn(cloud_note), run_time=1.0)
        self.wait(1.0)

        selected = electrons[0]
        selected_ring = Circle(radius=0.16, color=PHOTON, stroke_width=2.4).move_to(selected)
        selected_note = label("primary electron", color=PHOTON, scale=0.24, weight="BOLD")
        selected_note.next_to(selected_ring, LEFT, buff=0.42).shift(DOWN * 0.10)
        self.play(FadeOut(e_field), FadeOut(e_drift), Indicate(selected, color=PHOTON), Create(selected_ring), FadeIn(selected_note), run_time=1.15)
        self.wait(1.8)

        chamber_group = VGroup(chamber, cathode, stack, electrons, recoil, cloud_envelope, cloud_note, selected_ring, selected_note, step)
        self.play(FadeOut(chamber_group), run_time=1.1)

        close_stack = gem_stack(height=4.05, spacing=0.85).move_to([-0.2, 0.05, 0])
        gem_labels = VGroup(
            *[
                label(f"GEM {index + 1}", color=GEM, scale=0.22, weight="BOLD").next_to(foil, DOWN, buff=0.15)
                for index, foil in enumerate(close_stack)
            ]
        )
        step2 = label("2  AVALANCHE + SCINTILLATION", color=PHOTON, scale=0.28, weight="BOLD")
        step2.move_to([0, 2.75, 0])
        self.play(FadeIn(close_stack), FadeIn(gem_labels), FadeIn(step2), run_time=1.3)

        incoming = VGroup(electron_marker(0.060).move_to([-3.2, 0.02, 0]))
        incoming_label = label("one primary electron", color=ELECTRON, scale=0.24, weight="BOLD")
        incoming_label.next_to(incoming, UP, buff=0.16)
        self.play(FadeIn(incoming), FadeIn(incoming_label), run_time=0.85)

        rng = np.random.default_rng(103)
        current = incoming
        stage_centres = [foil.get_center()[0] for foil in close_stack]
        multiplicities = [18, 55, 120]
        for stage_index, (stage_x, count) in enumerate(zip(stage_centres, multiplicities)):
            radius = (0.025, 0.017, 0.011)[stage_index]
            next_cloud = VGroup(
                *[
                    electron_marker(radius).move_to(
                        [
                            stage_x + 0.30 + rng.normal(0.0, 0.055 + stage_index * 0.015),
                            rng.normal(0.02, 0.22 + 0.08 * stage_index),
                            0,
                        ]
                    )
                    for _ in range(count)
                ]
            )
            target = current.copy().move_to([stage_x - 0.10, 0.02, 0])
            flash = self.photon_flash(np.array([stage_x, 0.02, 0]), rays=16 + stage_index * 6)
            sparks = self.photon_cloud(np.array([stage_x, 0.02, 0]), count=14 + stage_index * 9, seed=500 + stage_index)
            self.play(
                Transform(current, target),
                run_time=0.85,
            )
            stage_animations = [
                ReplacementTransform(current, next_cloud),
                FadeIn(flash, lag_ratio=0.03),
                FadeIn(sparks, lag_ratio=0.02),
            ]
            if stage_index == 0:
                stage_animations.append(FadeOut(incoming_label))
            self.play(*stage_animations, run_time=0.85)
            self.play(FadeOut(flash), FadeOut(sparks), run_time=0.40)
            current = next_cloud

        multiplication_note = label("primary electron → avalanche + scintillation", color=PHOTON, scale=0.24, weight="BOLD")
        multiplication_note.to_edge(DOWN, buff=0.55)
        self.play(FadeIn(multiplication_note), run_time=0.75)
        self.wait(2.4)
        self.play(
            FadeOut(close_stack),
            FadeOut(gem_labels),
            FadeOut(current),
            FadeOut(multiplication_note),
            run_time=1.0,
        )

        self.show_readout(step2)
        self.wait(1.5)
        show_brand_outro(self)

    def build_cad_overview(self) -> VGroup:
        central = Line([0, -1.66, 0], [0, 1.66, 0], color=FOREGROUND, stroke_width=4.2)
        left_volume = Rectangle(
            width=3.65,
            height=3.35,
            stroke_color=MUTED,
            stroke_width=1.4,
            fill_color=CHAMBER_FILL,
            fill_opacity=0.34,
        ).next_to(central, LEFT, buff=0)
        right_volume = left_volume.copy().next_to(central, RIGHT, buff=0)

        left_stack = gem_stack(height=2.75, spacing=0.10).scale(0.64)
        left_stack.move_to(left_volume.get_left() + RIGHT * 0.24)
        right_stack = gem_stack(height=2.75, spacing=0.10).scale(0.64)
        right_stack.move_to(right_volume.get_right() + LEFT * 0.24)

        cage = VGroup()
        for volume in (left_volume, right_volume):
            for fraction in (0.22, 0.44, 0.66, 0.88):
                x = volume.get_left()[0] + fraction * volume.width
                cage.add(
                    Line([x, -1.47, 0], [x, 1.47, 0], color=FIELD, stroke_width=0.55).set_opacity(0.25)
                )

        sensors = VGroup()
        for sign in (-1, 1):
            camera_count = require_positive_integer(
                self.science["geometry"]["cameras_per_optical_end"],
                "geometry.cameras_per_optical_end",
            )
            pmt_count = require_positive_integer(
                self.science["presentation_projection"]["pmts_visible_per_optical_end"],
                "presentation_projection.pmts_visible_per_optical_end",
            )
            sensor_centre_x = sign * 4.88
            for y in np.linspace(-0.70, 0.70, camera_count):
                icon = camera_icon(0.42)
                if sign > 0:
                    icon.flip(UP)
                icon.move_to([sensor_centre_x, y, 0])
                sensors.add(icon)

            pmt_x = sensor_centre_x - sign * 0.44
            for y in np.linspace(-1.05, 1.05, pmt_count):
                icon = pmt_icon(0.42)
                if sign > 0:
                    icon.flip(UP)
                icon.move_to([pmt_x, y, 0])
                sensors.add(icon)

        cathode_label = label("central cathode", color=FOREGROUND, scale=0.24)
        cathode_label.next_to(central, UP, buff=0.12)
        return VGroup(left_volume, right_volume, cage, central, left_stack, right_stack, sensors, cathode_label)

    def build_half_chamber(self):
        chamber = Rectangle(
            width=5.35,
            height=3.85,
            stroke_color=MUTED,
            stroke_width=1.4,
            fill_color=CHAMBER_FILL,
            fill_opacity=0.28,
        ).move_to([-1.4, 0.0, 0])
        cathode = Line([-4.05, -1.68, 0], [-4.05, 1.68, 0], color=FOREGROUND, stroke_width=4)
        stack = gem_stack(height=3.25, spacing=0.14).scale(0.72).move_to([1.16, 0.0, 0])

        primary = simulate_nr_track(seed=177, visible_integral=1.0)
        sample_indices = np.arange(0, len(primary.points), 2)
        raw_points = primary.points[sample_indices]
        raw_points = raw_points - raw_points.mean(axis=0)
        angle = np.deg2rad(-23.0)
        rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        transformed = (raw_points @ rotation.T) * 1.55
        track_points = [np.array([-3.20 + point[0], 0.08 + point[1], 0]) for point in transformed]
        recoil = VMobject(color=NUCLEUS, stroke_width=5.5)
        recoil.set_points_smoothly(track_points)
        sampled_weights = primary.weights[sample_indices]
        sampled_weights = sampled_weights / sampled_weights.max()
        electrons = VGroup(
            *[
                electron_marker(0.025 + 0.030 * weight)
                .set_opacity(0.55 + 0.45 * weight)
                .move_to(point + np.array([0.0, 0.04 * (-1) ** index, 0]))
                for index, (point, weight) in enumerate(zip(track_points, sampled_weights))
            ]
        )
        return chamber, cathode, stack, recoil, electrons

    def photon_flash(self, centre: np.ndarray, rays: int = 8) -> VGroup:
        group = VGroup()
        for index in range(rays):
            angle = 2 * np.pi * index / rays
            inner = centre + 0.13 * np.array([np.cos(angle), np.sin(angle), 0])
            outer = centre + (0.32 + 0.04 * (index % 2)) * np.array([np.cos(angle), np.sin(angle), 0])
            group.add(Line(inner, outer, color=PHOTON, stroke_width=2.0))
        return group

    def photon_cloud(self, centre: np.ndarray, count: int, seed: int) -> VGroup:
        rng = np.random.default_rng(seed)
        photons = VGroup()
        for _ in range(count):
            angle = rng.uniform(0.0, 2.0 * np.pi)
            radius = rng.uniform(0.22, 0.72)
            point = centre + radius * np.array([np.cos(angle), np.sin(angle), 0])
            photons.add(Dot(point, radius=rng.uniform(0.012, 0.026), color=PHOTON).set_opacity(rng.uniform(0.55, 0.95)))
        return photons

    def show_readout(self, old_step):
        step3 = label("3  OPTICAL READOUT", color=CYGNUS, scale=0.28, weight="BOLD")
        step3.move_to([0, 2.75, 0])
        self.play(Transform(old_step, step3), run_time=0.75)

        gem_plane = VGroup(
            Rectangle(
                width=0.18,
                height=3.4,
                stroke_color=GEM,
                stroke_width=2.0,
                fill_color=GEM,
                fill_opacity=0.55,
            ),
            label("GEM light plane", color=GEM, scale=0.23, weight="BOLD").rotate(np.pi / 2),
        ).move_to([-4.25, -0.05, 0])

        projection = self.science["presentation_projection"]
        pmt_count = require_positive_integer(
            projection["pmts_visible_per_optical_end"],
            "presentation_projection.pmts_visible_per_optical_end",
        )
        sensor_centre = np.array([0.15, 0.18, 0])
        camera = camera_icon(1.35).flip(UP).move_to(sensor_centre)
        camera_label = label(
            projection["camera_label"], color=CYGNUS, scale=0.27, weight="BOLD"
        ).next_to(camera, UP, buff=0.12)
        sightline = DashedLine(camera.get_left(), gem_plane.get_center(), color=CYGNUS, stroke_width=2.0)

        pmts = VGroup(
            *[
                pmt_icon(0.90)
                .flip(UP)
                .move_to(
                    sensor_centre
                    + np.array([1.30 * np.cos(angle), 1.02 * np.sin(angle), 0])
                )
                for angle in np.linspace(np.pi / 4, 2 * np.pi + np.pi / 4, pmt_count, endpoint=False)
            ]
        )
        pmt_label = label(f"{pmt_count} PMTs", color=PHOTON, scale=0.24, weight="BOLD")
        pmt_label.next_to(pmts, DOWN, buff=0.14)
        pmt_rays = VGroup(
            *[
                Line(
                    gem_plane.get_center() + UP * (0.30 - 0.20 * index),
                    pmt.get_left(),
                    color=PHOTON,
                    stroke_width=1.25,
                )
                for index, pmt in enumerate(pmts)
            ]
        ).set_opacity(0.58)

        self.play(
            FadeIn(gem_plane),
            FadeIn(camera),
            FadeIn(camera_label),
            Create(sightline),
            FadeIn(pmts),
            FadeIn(pmt_label),
            Create(pmt_rays),
            run_time=1.6,
        )
        self.wait(1.5)

        image_panel = RoundedRectangle(
            width=3.1,
            height=2.05,
            corner_radius=0.12,
            stroke_color=CYGNUS,
            stroke_width=1.5,
            fill_color=READOUT_PANEL,
            fill_opacity=0.92,
        ).move_to([4.25, 0.82, 0])
        image_title = label("qCMOS: x–y shape + charge asymmetry", color=CYGNUS, scale=0.21, weight="BOLD")
        image_title.next_to(image_panel, UP, buff=0.10)
        provenance = label("Light signals from one recoil", color=MUTED, scale=0.18)
        provenance.next_to(image_title, UP, buff=0.10)
        glow_track = VGroup()
        mock_nr = diffuse_track(simulate_nr_track(seed=211), sigma=0.065, seed=212)
        centred = mock_nr.points - mock_nr.points.mean(axis=0)
        span = np.ptp(centred, axis=0)
        scale = min(1.75 / max(span[0], 1e-6), 0.86 / max(span[1], 1e-6))
        weights = mock_nr.weights / mock_nr.weights.max()
        mapped_points = []
        for point, weight in zip(centred, weights):
            x = 4.25 + scale * point[0]
            y = 0.72 + scale * point[1]
            mapped_points.append(np.array([x, y, 0]))
            glow_track.add(
                Dot([x, y, 0], radius=0.018 + 0.025 * weight, color=PHOTON).set_opacity(0.28 + 0.70 * weight)
            )
        charge_arrow = Arrow(
            mapped_points[0],
            mapped_points[-1],
            buff=0.08,
            color=NUCLEUS,
            stroke_width=2.3,
            tip_length=0.13,
        )
        charge_note = label("asymmetric dE/dx → head–tail estimate", color=NUCLEUS, scale=0.19, weight="BOLD")
        charge_note.move_to([4.25, -0.02, 0])

        waveform_panel = RoundedRectangle(
            width=3.1,
            height=1.35,
            corner_radius=0.12,
            stroke_color=PHOTON,
            stroke_width=1.5,
            fill_color=READOUT_PANEL,
            fill_opacity=0.92,
        ).move_to([4.25, -1.35, 0])
        waveform_title = label("PMTs: time spread → inclination", color=PHOTON, scale=0.21, weight="BOLD")
        waveform_title.next_to(waveform_panel, UP, buff=0.09)
        waveform = VMobject(color=PHOTON, stroke_width=2.6)
        wave_points = []
        pulse_values = []
        for index in range(110):
            t = index / 109
            u = np.clip((t - 0.10) / 0.82, 0.0, 1.0)
            pulse = (u**1.6) * np.exp(-4.8 * u) if 0.0 < u < 1.0 else 0.0
            pulse *= 0.82 + 0.18 * np.sin(index * 0.83) ** 2
            pulse_values.append(pulse)
        pulse_values = np.asarray(pulse_values)
        pulse_values /= pulse_values.max()
        for index, pulse in enumerate(pulse_values):
            x = 2.90 + 0.0248 * index
            y = -1.62 + 0.55 * pulse
            wave_points.append([x, y, 0])
        waveform.set_points_smoothly(wave_points)
        time_start = 3.13
        time_end = 5.37
        time_markers = VGroup(
            DashedLine([time_start, -1.70, 0], [time_start, -1.10, 0], color=MUTED, stroke_width=1.0),
            DashedLine([time_end, -1.70, 0], [time_end, -1.10, 0], color=MUTED, stroke_width=1.0),
            DoubleArrow(
                [time_start, -1.84, 0],
                [time_end, -1.84, 0],
                buff=0,
                color=PHOTON,
                stroke_width=1.5,
                tip_length=0.09,
            ),
        )
        time_note = label("extended Δt", color=PHOTON, scale=0.18, weight="BOLD")
        time_note.move_to([4.25, -1.91, 0])

        self.play(FadeIn(image_panel), FadeIn(image_title), FadeIn(provenance), run_time=0.85)
        self.play(LaggedStart(*[FadeIn(dot) for dot in glow_track], lag_ratio=0.025), run_time=1.5)
        self.play(Create(charge_arrow), FadeIn(charge_note), run_time=0.85)
        self.wait(1.5)
        self.play(FadeIn(waveform_panel), FadeIn(waveform_title), Create(waveform), run_time=1.5)
        self.play(FadeIn(time_markers), FadeIn(time_note), run_time=0.85)
        self.wait(1.7)

        summary = label("qCMOS: head–tail estimate · PMTs: inclination in time", color=FOREGROUND, scale=0.26, weight="BOLD")
        summary.to_edge(DOWN, buff=0.28)
        self.play(FadeIn(summary, shift=UP * 0.08), run_time=0.85)
