"""Elastic dark-matter-candidate scatter to recoil ionization.

All numerical values below are dimensionless illustration parameters used only
to construct a self-consistent elastic collision.  They are not CYGNO detector
settings, performance claims, or a proposed WIMP model.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    Arrow,
    Circle,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    Flash,
    GrowArrow,
    LaggedStart,
    Line,
    MathTex,
    MoveAlongPath,
    MovingCameraScene,
    RoundedRectangle,
    Text,
    VGroup,
    VMobject,
    Write,
    config,
    linear,
)


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cygno_anim.physics import elastic_scatter_lab
from cygno_anim.branding import add_brand_signature, show_brand_outro
from cygno_anim.config import ConfigurationError, load_science
from cygno_anim.visuals import (
    FONT,
    SCATTER_BACKGROUND as BACKGROUND,
    SCATTER_DIM as DIM,
    SCATTER_ELECTRON as ELECTRON,
    SCATTER_FOREGROUND as FOREGROUND,
    SCATTER_MUTED as MUTED,
    SCATTER_PANEL as PANEL,
    SCATTER_RECOIL as RECOIL,
    SCATTER_WIMP as WIMP,
)


def elastic_scatter() -> dict[str, np.ndarray]:
    """Return one exact nonrelativistic two-body elastic-scatter solution.

    A projectile hits a stationary target.  We rotate the projectile momentum
    in the centre-of-mass frame and transform back to the lab frame.  The
    dimensionless choices affect only the on-screen geometry.
    """

    state = elastic_scatter_lab()
    momentum_in = np.append(state.p_in, 0.0)
    momentum_out = np.append(state.p_out, 0.0)
    momentum_transfer = np.append(state.q, 0.0)
    recoil_momentum = np.append(state.p_recoil, 0.0)

    # These assertions protect the visual convention if the illustration
    # parameters are edited later.
    assert np.allclose(momentum_in, momentum_out + recoil_momentum)
    assert np.allclose(momentum_transfer, recoil_momentum)
    assert np.isclose(state.kinetic_energy_in, state.kinetic_energy_out)
    assert np.dot(recoil_momentum, momentum_in) > 0.0  # forward hemisphere
    assert abs(np.cross(momentum_in[:2], recoil_momentum[:2])) > 1.0e-6

    return {
        "p_in": momentum_in,
        "p_out": momentum_out,
        "q": momentum_transfer,
        "p_recoil": recoil_momentum,
    }


def unit(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def candidate_marker(radius: float = 0.13) -> VGroup:
    halo = Circle(
        radius=radius * 2.0,
        color=WIMP,
        stroke_width=2,
        stroke_opacity=0.28,
        fill_color=WIMP,
        fill_opacity=0.06,
    )
    ring = Circle(
        radius=radius,
        color=WIMP,
        stroke_width=2.5,
        fill_color=WIMP,
        fill_opacity=0.18,
    )
    core = Dot(radius=radius * 0.32, color=WIMP)
    return VGroup(halo, ring, core)


def nucleus_marker(radius: float = 0.34) -> VGroup:
    shell = Circle(
        radius=radius,
        color=RECOIL,
        stroke_width=2.5,
        fill_color=RECOIL,
        fill_opacity=0.10,
    )
    offsets = (
        (-0.12, 0.10),
        (0.05, 0.13),
        (0.15, 0.00),
        (-0.04, -0.03),
        (-0.15, -0.11),
        (0.08, -0.14),
    )
    nucleons = VGroup(
        *[
            Dot(
                np.array([x, y, 0.0]) * (radius / 0.34),
                radius=radius * 0.16,
                color=RECOIL if index % 2 == 0 else FOREGROUND,
                fill_opacity=0.92,
            )
            for index, (x, y) in enumerate(offsets)
        ]
    )
    return VGroup(shell, nucleons)


class WIMPRecoil(MovingCameraScene):
    """A deterministic, independently renderable recoil sequence."""

    def construct(self) -> None:
        self.camera.background_color = BACKGROUND
        add_brand_signature(self)

        momentum_rule = load_science(include_local=False)["conventions"][
            "momentum_transfer"
        ]
        if momentum_rule != "q = p_chi_in - p_chi_out":
            raise ConfigurationError(
                f"Unsupported momentum-transfer convention: {momentum_rule!r}"
            )

        collision = np.array([-1.10, 0.18, 0.0])
        momentum_scale = 5.60
        solution = elastic_scatter()

        p_in = solution["p_in"]
        p_out = solution["p_out"]
        q = solution["q"]

        incoming_start = collision - momentum_scale * p_in
        outgoing_end = collision + momentum_scale * p_out
        recoil_end = collision + momentum_scale * q

        title = Text(
            "Elastic scatter  →  recoil ionization",
            font=FONT,
            color=FOREGROUND,
            weight="MEDIUM",
        ).scale(0.62)
        title.to_corner(UP + LEFT, buff=0.34)

        top_rule = Line(
            LEFT * (config.frame_width / 2 - 0.34),
            RIGHT * (config.frame_width / 2 - 0.34),
            color=DIM,
            stroke_width=1,
            stroke_opacity=0.55,
        ).to_edge(UP, buff=0.91)
        fixed_header = VGroup(title, top_rule)

        incoming_arrow = Arrow(
            incoming_start,
            collision,
            buff=0.0,
            color=WIMP,
            stroke_width=5,
            max_tip_length_to_length_ratio=0.10,
        )
        incoming_label = Text(
            "incoming candidate",
            font=FONT,
            color=WIMP,
        ).scale(0.36)
        incoming_label.next_to(incoming_arrow, UP, buff=0.18)
        p_in_label = MathTex(r"\mathbf p_{\rm in}", color=WIMP).scale(0.60)
        p_in_label.next_to(incoming_arrow, DOWN, buff=0.13)

        target = nucleus_marker().move_to(collision)
        target_label = Text(
            "target nucleus",
            font=FONT,
            color=RECOIL,
        ).scale(0.34)
        target_label.next_to(target, DOWN, buff=0.18)

        candidate = candidate_marker().move_to(incoming_start)
        incoming_path = Line(incoming_start, collision)

        self.play(FadeIn(fixed_header, shift=UP * 0.08), run_time=0.85)
        self.play(
            GrowArrow(incoming_arrow),
            FadeIn(incoming_label, shift=UP * 0.08),
            FadeIn(p_in_label),
            FadeIn(target, scale=0.75),
            FadeIn(target_label),
            FadeIn(candidate),
            run_time=1.20,
        )
        self.play(MoveAlongPath(candidate, incoming_path, rate_func=linear), run_time=2.00)
        self.wait(0.45)
        self.play(
            Flash(collision, color=FOREGROUND, line_length=0.22, flash_radius=0.45),
            target.animate.scale(1.12),
            run_time=0.42,
        )
        self.play(target.animate.scale(1.0 / 1.12), run_time=0.30)

        outgoing_arrow = Arrow(
            collision,
            outgoing_end,
            buff=0.0,
            color=WIMP,
            stroke_width=5,
            max_tip_length_to_length_ratio=0.12,
        )
        recoil_arrow = Arrow(
            collision,
            recoil_end,
            buff=0.0,
            color=RECOIL,
            stroke_width=5.5,
            max_tip_length_to_length_ratio=0.12,
        )
        outgoing_label = Text(
            "outgoing candidate",
            font=FONT,
            color=WIMP,
        ).scale(0.34)
        outgoing_label.next_to(outgoing_arrow, LEFT, buff=0.12).shift(UP * 0.12)
        p_out_label = MathTex(r"\mathbf p_{\rm out}", color=WIMP).scale(0.59)
        p_out_label.next_to(outgoing_arrow, RIGHT, buff=0.12).shift(DOWN * 0.05)

        recoil_label = Text(
            "nuclear recoil",
            font=FONT,
            color=RECOIL,
        ).scale(0.35)
        recoil_label.next_to(recoil_arrow, RIGHT, buff=0.10)
        q_label = MathTex(
            r"\mathbf q=\mathbf p_{\rm recoil}", color=RECOIL
        ).scale(0.57)
        q_label.next_to(recoil_arrow, LEFT, buff=0.10).shift(DOWN * 0.13)

        outgoing_path = Line(collision, outgoing_end)
        recoil_path = Line(collision, recoil_end)

        self.play(
            AnimationGroup(
                GrowArrow(outgoing_arrow),
                GrowArrow(recoil_arrow),
                lag_ratio=0.08,
            ),
            FadeOut(target_label),
            FadeIn(outgoing_label),
            FadeIn(p_out_label),
            FadeIn(recoil_label),
            FadeIn(q_label),
            run_time=1.15,
        )
        self.play(
            MoveAlongPath(candidate, outgoing_path, rate_func=linear),
            MoveAlongPath(target, recoil_path, rate_func=linear),
            run_time=2.10,
        )
        self.wait(0.60)

        equation_panel = RoundedRectangle(
            width=6.35,
            height=0.82,
            corner_radius=0.12,
            stroke_color=DIM,
            stroke_width=1.2,
            fill_color=PANEL,
            fill_opacity=0.92,
        ).to_edge(DOWN, buff=0.28)
        equation = MathTex(
            r"\mathbf q=\mathbf p_{\rm in}-\mathbf p_{\rm out}"
            r"=\mathbf p_{\rm recoil}",
            color=FOREGROUND,
        ).scale(0.68)
        equation.move_to(equation_panel)
        equation.set_color_by_tex(r"\mathbf q", RECOIL)
        equation.set_color_by_tex(r"\mathbf p_{\rm recoil}", RECOIL)
        momentum_note = Text(
            "momentum is conserved",
            font=FONT,
            color=MUTED,
        ).scale(0.30)
        momentum_note.next_to(equation_panel, UP, buff=0.10)
        fixed_equation = VGroup(equation_panel, equation, momentum_note)
        self.play(FadeIn(equation_panel), Write(equation), FadeIn(momentum_note), run_time=1.25)
        self.wait(1.00)

        # One recoil is not an exact pointer back to one incoming WIMP.  The
        # ensemble is forward-biased around the physical incoming direction.
        # Every illustrated recoil below remains in that forward hemisphere;
        # the bright q arrow is the exact event constructed above.
        fan_angles = np.deg2rad(
            (-66, -53, -41, -30, -21, -14, -8, -3, 3, 8, 14, 21, 30, 41, 53, 66)
        )
        fan_arrows = VGroup()
        for angle in fan_angles:
            direction = np.array([np.cos(angle), np.sin(angle), 0.0])
            centrality = np.cos(angle) ** 2
            arrow = Arrow(
                collision + 0.09 * direction,
                collision + (1.30 + 0.28 * centrality) * direction,
                buff=0.0,
                color=RECOIL,
                stroke_width=2.0,
                max_tip_length_to_length_ratio=0.13,
            )
            arrow.set_opacity(0.12 + 0.26 * centrality)
            fan_arrows.add(arrow)

        incoming_axis = DashedLine(
            collision + 0.12 * RIGHT,
            collision + 2.05 * RIGHT,
            color=WIMP,
            stroke_width=1.7,
            stroke_opacity=0.75,
            dash_length=0.08,
        )
        distribution_tag = Text(
            "RECOIL ENSEMBLE",
            font=FONT,
            color=MUTED,
        ).scale(0.27)
        distribution_tag.move_to(collision + 2.60 * RIGHT + 0.62 * UP)
        distribution_caption = VGroup(
            Text(
                "one recoil ≠ exact arrival direction",
                font=FONT,
                color=FOREGROUND,
            ).scale(0.30),
            Text(
                "an ensemble reveals a forward excess",
                font=FONT,
                color=RECOIL,
            ).scale(0.30),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.09)
        distribution_caption.move_to(collision + 3.82 * RIGHT + 0.20 * DOWN)

        self.play(
            Create(incoming_axis),
            LaggedStart(
                *[GrowArrow(arrow) for arrow in fan_arrows],
                lag_ratio=0.035,
            ),
            FadeIn(distribution_tag, shift=UP * 0.05),
            FadeIn(distribution_caption, shift=RIGHT * 0.05),
            run_time=1.60,
        )
        # Hold the full collision and ensemble angular distribution before the
        # microscopic ionization close-up begins.
        self.wait(3.20)

        macro_objects = VGroup(
            incoming_arrow,
            incoming_label,
            p_in_label,
            outgoing_arrow,
            outgoing_label,
            p_out_label,
            recoil_arrow,
            recoil_label,
            q_label,
            candidate,
            incoming_axis,
            fan_arrows,
            distribution_tag,
            distribution_caption,
        )

        recoil_direction = unit(q)
        transverse = np.array([-recoil_direction[1], recoil_direction[0], 0.0])
        closeup_centre = recoil_end + 0.78 * recoil_direction
        self.play(
            self.camera.frame.animate.scale(0.52).move_to(closeup_centre),
            FadeOut(fixed_header),
            FadeOut(fixed_equation),
            FadeOut(macro_objects),
            target.animate.scale(0.47),
            run_time=1.90,
        )

        # A sparse neutral-gas texture establishes that the following marks are
        # microscopic interactions, not camera pixels or a measured event.
        gas_offsets = (
            (-1.12, 0.54),
            (-0.78, -0.41),
            (-0.45, 0.63),
            (-0.18, -0.55),
            (0.22, 0.48),
            (0.55, -0.63),
            (0.86, 0.57),
            (1.18, -0.48),
            (1.48, 0.42),
            (1.78, -0.58),
        )
        gas_atoms = VGroup(
            *[
                Circle(
                    radius=0.045,
                    color=MUTED,
                    stroke_width=1.2,
                    stroke_opacity=0.30,
                    fill_color=MUTED,
                    fill_opacity=0.025,
                ).move_to(
                    recoil_end
                    + (along + 0.18) * recoil_direction
                    + across * transverse
                )
                for along, across in gas_offsets
            ]
        )
        frame_scale = float(self.camera.frame.get_width() / config.frame_width)
        provenance = Text(
            "Illustrative detector response",
            font=FONT,
            color=MUTED,
        ).scale(0.22 * frame_scale)
        provenance.move_to(
            self.camera.frame.get_corner(UP + LEFT)
            + RIGHT * (provenance.width / 2.0 + 0.28 * frame_scale)
            + DOWN * (provenance.height / 2.0 + 0.25 * frame_scale)
        )
        self.play(FadeIn(gas_atoms), FadeIn(provenance), run_time=0.65)

        distances = np.array([0.00, 0.22, 0.43, 0.61, 0.78, 0.94, 1.08, 1.21, 1.33, 1.43, 1.52])
        wiggles = np.array([0.00, 0.025, -0.035, 0.050, -0.025, 0.045, -0.055, 0.020, -0.040, 0.025, 0.00])
        trail_points = [
            recoil_end + distance * recoil_direction + wiggle * transverse
            for distance, wiggle in zip(distances, wiggles)
        ]
        trail = VMobject(color=RECOIL, stroke_width=4.2, stroke_opacity=0.78)
        trail.set_points_as_corners(trail_points)

        # In the low-energy NR regime, the
        # visible ionization is greatest near the beginning of the recoil path
        # and falls toward the stopping end.  Unequal point spacing and a mild
        # size/opacity gradient make that longitudinal asymmetry readable.
        deposit_distances = (
            0.06,
            0.10,
            0.14,
            0.18,
            0.22,
            0.27,
            0.32,
            0.38,
            0.44,
            0.51,
            0.59,
            0.68,
            0.78,
            0.89,
            1.02,
            1.16,
            1.31,
            1.47,
        )
        ion_sites = VGroup()
        electrons = VGroup()
        for index, distance in enumerate(deposit_distances):
            progress = distance / distances[-1]
            path_point = recoil_end + distance * recoil_direction
            side = -1.0 if index % 2 else 1.0
            ion_point = path_point + side * (0.022 + 0.007 * (index % 3)) * transverse
            electron_point = path_point + side * (0.102 + 0.015 * (index % 4)) * transverse
            ion_sites.add(
                Circle(
                    radius=0.030 + 0.012 * (1.0 - progress),
                    color=RECOIL,
                    stroke_width=1.5,
                    fill_color=RECOIL,
                    fill_opacity=0.12 + 0.28 * (1.0 - progress),
                ).move_to(ion_point)
            )
            electron = Dot(
                electron_point,
                radius=0.016 + 0.007 * (1.0 - progress),
                color=ELECTRON,
            )
            electron.set_opacity(0.55 + 0.40 * (1.0 - progress))
            electrons.add(electron)

        self.play(
            Create(trail),
            MoveAlongPath(target, trail, rate_func=linear),
            run_time=2.10,
        )
        self.wait(0.45)
        self.play(
            LaggedStart(
                *[FadeIn(site, scale=0.5) for site in ion_sites],
                lag_ratio=0.045,
            ),
            LaggedStart(
                *[FadeIn(electron, scale=0.3) for electron in electrons],
                lag_ratio=0.045,
            ),
            run_time=1.45,
        )

        electron_key = VGroup(
            Dot(radius=0.026, color=ELECTRON),
            Text("ionization electrons", font=FONT, color=ELECTRON).scale(0.22),
        ).arrange(RIGHT, buff=0.07)
        legend = electron_key
        legend.move_to(closeup_centre + 1.85 * LEFT + 0.28 * DOWN)

        start_label = VGroup(
            Text("START / TAIL", font=FONT, color=RECOIL).scale(0.22),
            Text("more ionization", font=FONT, color=FOREGROUND).scale(0.20),
        ).arrange(DOWN, buff=0.04)
        start_label.move_to(recoil_end + 0.16 * recoil_direction + 0.62 * transverse)
        start_callout = DashedLine(
            start_label.get_bottom(),
            recoil_end + 0.09 * recoil_direction + 0.08 * transverse,
            color=MUTED,
            stroke_width=1.2,
            dash_length=0.035,
        )

        stop_label = VGroup(
            Text("STOP / HEAD", font=FONT, color=RECOIL).scale(0.22),
            Text("less ionization", font=FONT, color=FOREGROUND).scale(0.20),
        ).arrange(DOWN, buff=0.04)
        stop_label.move_to(trail_points[-1] - 0.63 * transverse)
        stop_callout = DashedLine(
            stop_label.get_top(),
            trail_points[-1] - 0.07 * transverse,
            color=MUTED,
            stroke_width=1.2,
            dash_length=0.035,
        )

        sense_arrow = Arrow(
            recoil_end + 0.10 * recoil_direction - 0.28 * transverse,
            trail_points[-1] - 0.08 * recoil_direction - 0.28 * transverse,
            buff=0.0,
            color=RECOIL,
            stroke_width=2.6,
            max_tip_length_to_length_ratio=0.10,
        )
        sense_label_text = Text(
            "recoil sense",
            font=FONT,
            color=RECOIL,
        ).scale(0.22)
        sense_label_panel = RoundedRectangle(
            width=sense_label_text.width + 0.18,
            height=sense_label_text.height + 0.12,
            corner_radius=0.06,
            stroke_color=RECOIL,
            stroke_width=0.9,
            fill_color=BACKGROUND,
            fill_opacity=0.94,
        )
        sense_label = VGroup(sense_label_panel, sense_label_text)
        sense_midpoint = sense_arrow.point_from_proportion(0.52)
        sense_label.move_to(
            sense_midpoint - 0.62 * transverse - 0.12 * recoil_direction
        )
        sense_label.shift(DOWN * 0.20 + LEFT * 0.08)
        sense_callout = DashedLine(
            sense_label.get_corner(UP + RIGHT),
            sense_midpoint - 0.02 * transverse,
            color=MUTED,
            stroke_width=1.1,
            dash_length=0.035,
        )

        self.play(
            FadeIn(legend),
            FadeIn(start_label),
            Create(start_callout),
            FadeIn(stop_label),
            Create(stop_callout),
            GrowArrow(sense_arrow),
            FadeIn(sense_label),
            Create(sense_callout),
            run_time=0.90,
        )

        energy_panel = RoundedRectangle(
            width=10.8,
            height=0.94,
            corner_radius=0.12,
            stroke_color=DIM,
            stroke_width=1.2,
            fill_color=PANEL,
            fill_opacity=0.96,
        ).to_edge(DOWN, buff=0.20)
        energy_line = VGroup(
            Text("NR energy loss", font=FONT, color=RECOIL).scale(0.32),
            Text("→", font=FONT, color=MUTED).scale(0.38),
            Text("asymmetric ionization", font=FONT, color=ELECTRON).scale(0.32),
            Text("→", font=FONT, color=MUTED).scale(0.38),
            Text("head–tail estimate", font=FONT, color=FOREGROUND).scale(0.32),
        ).arrange(RIGHT, buff=0.18)
        energy_line.move_to(energy_panel.get_center() + UP * 0.13)
        energy_note = Text(
            "Only part becomes detectable charge  •  sense recognition is statistical",
            font=FONT,
            color=MUTED,
        ).scale(0.27)
        energy_note.move_to(energy_panel.get_center() + DOWN * 0.25)
        fixed_energy = VGroup(energy_panel, energy_line, energy_note)
        fixed_energy.scale(0.52)
        fixed_energy.move_to(
            self.camera.frame.get_bottom()
            + UP * (fixed_energy.height / 2.0 + 0.10)
        )
        self.play(
            FadeIn(energy_panel),
            LaggedStart(*[FadeIn(item, shift=RIGHT * 0.05) for item in energy_line], lag_ratio=0.10),
            FadeIn(energy_note, shift=UP * 0.04),
            run_time=1.40,
        )
        self.wait(1.80)
        show_brand_outro(self)
