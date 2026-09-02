"""Galactic motion and the apparent dark-matter wind from Cygnus.

The cyan sightline points from the observer toward Cygnus, while the purple
cold-dark-matter velocities point from the Cygnus side back toward the observer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    AnimationGroup,
    Arrow,
    Circle,
    Create,
    DashedVMobject,
    Dot,
    DOWN,
    Ellipse,
    FadeIn,
    FadeOut,
    GrowArrow,
    LaggedStart,
    LEFT,
    Line,
    linear,
    MoveAlongPath,
    ParametricFunction,
    PI,
    Polygon,
    RIGHT,
    RoundedRectangle,
    Scene,
    Succession,
    Text,
    UP,
    VGroup,
    WHITE,
    Write,
    always_redraw,
)


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cygno_anim.branding import add_brand_signature, show_brand_outro
from cygno_anim.config import load_science
from cygno_anim.physics import (
    direction_from_convention,
    observer_frame_velocities,
    paired_halo_velocities,
)
from cygno_anim.visuals import (
    BACKGROUND,
    CYGNUS,
    EARTH,
    FONT,
    FOREGROUND,
    GALACTIC_DISK as DISK,
    HALO,
    LAND,
    MUTED,
    SOLAR,
    STAR,
    WIMP as DM,
)


def label(text: str, size: int, color: str = FOREGROUND, weight: str = "NORMAL") -> Text:
    """Create a consistently styled text label."""

    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


def view_badge(text: str) -> VGroup:
    caption = label(text, 20, CYGNUS, "BOLD")
    frame = RoundedRectangle(
        width=caption.width + 0.40,
        height=caption.height + 0.22,
        corner_radius=0.10,
        stroke_color=CYGNUS,
        stroke_width=1.2,
        fill_color=BACKGROUND,
        fill_opacity=0.84,
    )
    return VGroup(frame, caption)


def cygnus_marker(center: np.ndarray, compact: bool = False) -> VGroup:
    """A small schematic constellation marker (not a sky chart)."""

    scale = 0.74 if compact else 1.0
    offsets = (
        np.array([-0.54, -0.17, 0.0]),
        np.array([-0.23, 0.08, 0.0]),
        np.array([0.06, 0.02, 0.0]),
        np.array([0.34, 0.31, 0.0]),
        np.array([0.19, -0.34, 0.0]),
    )
    points = [center + scale * offset for offset in offsets]
    links = VGroup(
        Line(points[0], points[1]),
        Line(points[1], points[2]),
        Line(points[2], points[3]),
        Line(points[2], points[4]),
    ).set_stroke(CYGNUS, width=1.4, opacity=0.62)
    stars = VGroup(*(Dot(point, radius=0.042 * scale, color=CYGNUS) for point in points))
    name = label("CYGNUS", 20 if compact else 23, CYGNUS, "BOLD")
    name.next_to(stars, UP, buff=0.10)
    return VGroup(links, stars, name)


def sun_marker(center: np.ndarray, scale: float = 1.0) -> VGroup:
    glow = Circle(
        radius=0.24 * scale,
        stroke_color=SOLAR,
        stroke_width=1.4,
        stroke_opacity=0.38,
        fill_color=SOLAR,
        fill_opacity=0.05,
    ).move_to(center)
    ring = Circle(
        radius=0.14 * scale,
        stroke_color=SOLAR,
        stroke_width=2.0,
        fill_color=SOLAR,
        fill_opacity=0.18,
    ).move_to(center)
    core = Dot(center, radius=0.065 * scale, color=SOLAR)
    return VGroup(glow, ring, core)


def earth_marker(center: np.ndarray, scale: float = 1.0) -> VGroup:
    """A compact blue-green Earth symbol for the Solar-System inset."""

    globe = Circle(
        radius=0.050 * scale,
        stroke_color=EARTH,
        stroke_width=1.2,
        fill_color=EARTH,
        fill_opacity=0.78,
    ).move_to(center)
    land = Dot(
        center + np.array([-0.014, 0.010, 0.0]) * scale,
        radius=0.014 * scale,
        color=LAND,
    )
    return VGroup(globe, land)


class GalacticWind(Scene):
    """Move from the Galactic frame to the local Solar-frame wind."""

    def construct(self) -> None:
        self.camera.background_color = BACKGROUND
        rng = np.random.default_rng(260831)

        conventions = load_science(include_local=False)["conventions"]
        n_cyg = direction_from_convention(conventions["cygnus_sightline"])
        solar_direction = direction_from_convention(conventions["solar_velocity"])
        incoming_direction = direction_from_convention(
            conventions["incoming_wimp_velocity"]
        )
        assert np.allclose(n_cyg, solar_direction)
        assert np.allclose(incoming_direction, -n_cyg)

        halo_velocities = paired_halo_velocities(seed=260832, n_pairs=18, sigma=0.32)
        solar_velocity = 0.88 * solar_direction
        observed_velocities = observer_frame_velocities(halo_velocities, solar_velocity)
        assert np.allclose(halo_velocities.mean(axis=0), np.zeros(2), atol=1e-14)
        assert np.dot(observed_velocities.mean(axis=0), incoming_direction) > 0.0

        stars = VGroup()
        for _ in range(84):
            point = np.array([rng.uniform(-7.0, 7.0), rng.uniform(-3.8, 3.8), 0.0])
            stars.add(
                Dot(
                    point,
                    radius=rng.uniform(0.006, 0.018),
                    color=WHITE,
                    fill_opacity=rng.uniform(0.12, 0.35),
                    stroke_width=0,
                )
            )
        self.add(stars)
        add_brand_signature(self)

        kicker = label("DIRECTIONAL DARK MATTER", 20, CYGNUS, "BOLD")
        title = label("Why the wind appears from Cygnus", 40, FOREGROUND, "BOLD")
        heading = VGroup(kicker, title).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        heading.to_corner(UP + LEFT, buff=0.38)
        phase = view_badge("GALACTIC FRAME")
        phase.to_edge(RIGHT, buff=0.42)
        phase.set_y(2.62)
        statement = label(
            "The Solar System orbits within the dark-matter halo",
            24,
            MUTED,
        )
        statement.next_to(heading, DOWN, aligned_edge=LEFT, buff=0.18)

        galaxy_center = np.array([0.0, -0.15, 0.0])
        halo_shells = VGroup(
            Ellipse(width=12.2, height=6.15),
            Ellipse(width=10.9, height=5.45),
            Ellipse(width=9.8, height=4.82),
        )
        for index, shell in enumerate(halo_shells):
            shell.move_to(galaxy_center)
            shell.set_stroke(HALO, width=1.3, opacity=0.48 - 0.10 * index)
            shell.set_fill(HALO, opacity=0.025 + 0.010 * index)

        halo_particles = VGroup()
        while len(halo_particles) < 72:
            x = rng.uniform(-5.65, 5.65)
            y = rng.uniform(-2.78, 2.78)
            if (x / 5.65) ** 2 + (y / 2.78) ** 2 > 1.0:
                continue
            halo_particles.add(
                Dot(
                    galaxy_center + np.array([x, y, 0.0]),
                    radius=rng.uniform(0.014, 0.032),
                    color=DM,
                    fill_opacity=rng.uniform(0.18, 0.46),
                    stroke_width=0,
                )
            )

        disk = Ellipse(
            width=9.15,
            height=3.82,
            stroke_color=DISK,
            stroke_width=1.1,
            stroke_opacity=0.33,
            fill_color=DISK,
            fill_opacity=0.035,
        ).move_to(galaxy_center)

        spiral_arms = VGroup()
        for arm_index in range(4):
            arm_phase = arm_index * PI / 2.0

            def arm_curve(t: float, phase_offset: float = arm_phase) -> np.ndarray:
                radius = 0.28 + 0.35 * t
                return galaxy_center + np.array(
                    [radius * np.cos(t + phase_offset), 0.44 * radius * np.sin(t + phase_offset), 0.0]
                )

            curve = ParametricFunction(
                arm_curve,
                t_range=[0.20, 3.08 * PI],
                color=DISK,
                stroke_width=1.6,
            ).set_stroke(opacity=0.68)
            glow = curve.copy().set_stroke(color=DISK, width=11.0, opacity=0.075)
            spiral_arms.add(glow, curve)

        arm_stars = VGroup()
        for arm_index in range(4):
            arm_phase = arm_index * PI / 2.0
            for _ in range(24):
                t = rng.uniform(0.45, 3.02 * PI)
                radius = 0.28 + 0.35 * t
                point = galaxy_center + np.array(
                    [
                        radius * np.cos(t + arm_phase) + rng.normal(0.0, 0.085),
                        0.44 * radius * np.sin(t + arm_phase) + rng.normal(0.0, 0.050),
                        0.0,
                    ]
                )
                arm_stars.add(
                    Dot(
                        point,
                        radius=rng.uniform(0.008, 0.022),
                        color=STAR if rng.random() > 0.20 else SOLAR,
                        fill_opacity=rng.uniform(0.35, 0.82),
                        stroke_width=0,
                    )
                )

        bulge = VGroup(
            Ellipse(width=1.15, height=0.60, stroke_width=0, fill_color=SOLAR, fill_opacity=0.09),
            Ellipse(width=0.68, height=0.34, stroke_width=0, fill_color=SOLAR, fill_opacity=0.22),
            Dot(radius=0.075, color=SOLAR),
        ).move_to(galaxy_center)
        center_name = label("GALACTIC CENTER", 18, SOLAR, "BOLD")
        center_name.next_to(bulge, UP, buff=0.08)
        halo_name = label("DARK-MATTER HALO", 18, DM, "BOLD")
        halo_name.move_to(np.array([5.00, 2.18, 0.0]))

        orbit = DashedVMobject(
            Ellipse(width=6.30, height=3.08).move_to(galaxy_center),
            num_dashes=72,
            dashed_ratio=0.56,
        ).set_stroke(SOLAR, width=1.4, opacity=0.48)
        orbit_name = label("SOLAR ORBIT", 18, SOLAR, "BOLD")
        orbit_name.move_to(galaxy_center + np.array([-4.45, -1.85, 0.0]))

        orbit_a = 3.15
        orbit_b = 1.54

        def orbit_position(theta: float) -> np.ndarray:
            return galaxy_center + np.array([orbit_a * np.cos(theta), orbit_b * np.sin(theta), 0.0])

        def solar_group(theta: float, earth_theta: float) -> VGroup:
            position = orbit_position(theta)
            tangent = np.array([-orbit_a * np.sin(theta), orbit_b * np.cos(theta), 0.0])
            tangent /= np.linalg.norm(tangent)
            marker = sun_marker(position)
            earth_orbit = Ellipse(
                width=0.78,
                height=0.30,
                stroke_color=EARTH,
                stroke_width=1.0,
                stroke_opacity=0.58,
            ).move_to(position)
            earth_position = position + np.array(
                [0.39 * np.cos(earth_theta), 0.15 * np.sin(earth_theta), 0.0]
            )
            earth = earth_marker(earth_position)
            motion = Arrow(
                position + 0.44 * tangent,
                position + 1.35 * tangent,
                buff=0,
                color=SOLAR,
                stroke_width=4.2,
                max_tip_length_to_length_ratio=0.17,
            )
            name = label("SOLAR SYSTEM", 18, SOLAR, "BOLD")
            name.next_to(earth_orbit, LEFT, buff=0.16).shift(DOWN * 0.16)
            motion_name = label("Solar motion", 17, SOLAR)
            motion_name.next_to(motion.get_end(), RIGHT, buff=0.10)
            return VGroup(earth_orbit, marker, earth, motion, name, motion_name)

        # The short arc establishes orbital motion without suggesting that a
        # complete Galactic orbit occurs on this animation timescale.
        from manim import ValueTracker

        orbital_angle = ValueTracker(-2.62)
        earth_angle = ValueTracker(0.35)
        moving_solar_system = always_redraw(
            lambda: solar_group(orbital_angle.get_value(), earth_angle.get_value())
        )

        self.play(FadeIn(heading, shift=DOWN * 0.08), FadeIn(phase), run_time=0.85)
        self.play(
            AnimationGroup(
                FadeIn(statement), FadeIn(halo_shells), FadeIn(halo_particles), FadeIn(disk),
                Create(spiral_arms), FadeIn(arm_stars), FadeIn(bulge), FadeIn(center_name),
                FadeIn(halo_name), lag_ratio=0.06,
            ),
            run_time=2.20,
        )
        self.wait(0.80)
        self.play(Create(orbit), FadeIn(orbit_name), FadeIn(moving_solar_system), run_time=1.15)
        self.wait(0.65)
        self.play(
            orbital_angle.animate.set_value(-PI / 2.0),
            earth_angle.animate.set_value(0.35 + 2.0 * PI),
            rate_func=linear,
            run_time=4.00,
        )

        final_solar_system = solar_group(-PI / 2.0, 0.35 + 2.0 * PI)
        self.remove(moving_solar_system)
        self.add(final_solar_system)
        final_sun = orbit_position(-PI / 2.0)

        global_cygnus = cygnus_marker(np.array([4.70, final_sun[1] + 0.28, 0.0]), compact=True)
        cygnus_sightline = Line(
            final_sun + np.array([0.28, 0.06, 0.0]),
            np.array([4.08, final_sun[1] + 0.23, 0.0]),
            color=CYGNUS,
            stroke_width=1.8,
            stroke_opacity=0.62,
        )
        toward_cygnus = label("Solar motion points toward Cygnus", 23, CYGNUS, "BOLD")
        toward_cygnus.to_edge(DOWN, buff=0.34)
        self.play(
            Create(cygnus_sightline), FadeIn(global_cygnus),
            FadeIn(toward_cygnus, shift=UP * 0.06), run_time=1.25,
        )
        # Hold on the completed Galactic-scale explanation before moving into
        # the local frame.  This gives the orbit, Solar motion, and Cygnus
        # relationship time to register.
        self.wait(3.00)

        galactic_visuals = VGroup(
            halo_shells, halo_particles, disk, spiral_arms, arm_stars, bulge, center_name,
            halo_name, orbit, orbit_name, final_solar_system, global_cygnus,
            cygnus_sightline, toward_cygnus,
        )
        local_phase = view_badge("SOLAR REST FRAME").move_to(phase)
        local_statement = label(
            "Solar-frame arrivals favor Cygnus", 24, MUTED,
        ).move_to(statement)

        observer_position = np.array([-4.72, -0.05, 0.0])
        observer = sun_marker(observer_position, scale=1.20)
        local_earth_orbit = Ellipse(
            width=0.98,
            height=0.42,
            stroke_color=EARTH,
            stroke_width=1.2,
            stroke_opacity=0.62,
        ).move_to(observer_position)

        # The projected orbit is diagrammatic: its deliberately accelerated
        # rate makes Earth's motion legible throughout the apparent-wind hold.
        # Increasing phase preserves the counter-clockwise orbital sense in
        # this chosen view; no direction convention is changed for layout.
        local_earth_phase = [0.45]
        local_earth_a = 0.49
        local_earth_b = 0.21

        def local_earth_position() -> np.ndarray:
            return observer_position + np.array(
                [
                    local_earth_a * np.cos(local_earth_phase[0]),
                    local_earth_b * np.sin(local_earth_phase[0]),
                    0.0,
                ]
            )

        local_earth = earth_marker(local_earth_position(), scale=1.70)

        def revolve_local_earth(mobject: VGroup, dt: float) -> None:
            local_earth_phase[0] += 0.92 * dt
            mobject.move_to(local_earth_position())

        local_earth.add_updater(revolve_local_earth)
        observer_name = label("SOLAR SYSTEM", 20, SOLAR, "BOLD")
        observer_name.next_to(local_earth_orbit, DOWN, buff=0.15).shift(LEFT * 0.35)
        local_cygnus = cygnus_marker(np.array([4.72, 1.48, 0.0]), compact=True)

        local_sightline_y = 1.52
        sightline = Arrow(
            np.array([-4.02, local_sightline_y, 0.0]),
            np.array([4.04, local_sightline_y, 0.0]),
            buff=0,
            color=CYGNUS,
            stroke_width=3.0,
            max_tip_length_to_length_ratio=0.055,
        )
        assert np.dot((sightline.get_end() - sightline.get_start())[:2], n_cyg) > 0.0
        sightline_lower_edge = sightline.get_bottom()[1]

        sightline_text = label("line of sight  →  Cygnus", 21, CYGNUS, "BOLD")
        sightline_panel = RoundedRectangle(
            width=sightline_text.width + 0.42,
            height=sightline_text.height + 0.24,
            corner_radius=0.10,
            stroke_color=CYGNUS,
            stroke_width=1.0,
            fill_color=BACKGROUND,
            fill_opacity=0.94,
        )
        sightline_name = VGroup(sightline_panel, sightline_text)
        sightline_name.move_to(np.array([-0.25, 1.88, 0.0]))

        self.play(
            FadeOut(galactic_visuals),
            FadeOut(phase),
            FadeOut(statement),
            run_time=0.90,
        )
        phase = local_phase
        statement = local_statement
        self.play(
            FadeIn(phase),
            FadeIn(statement),
            FadeIn(local_earth_orbit),
            FadeIn(observer, scale=0.75),
            FadeIn(local_earth),
            FadeIn(observer_name),
            FadeIn(local_cygnus),
            run_time=1.10,
        )
        self.play(GrowArrow(sightline), FadeIn(sightline_name), run_time=1.05)
        self.wait(1.25)

        selected_indices = (6, 8, 12, 16, 21, 34, 35)
        # The upper limit leaves a true empty band for the cyan sightline,
        # including the finite radius of each moving particle.
        mid_heights = np.linspace(-1.48, 0.90, len(selected_indices))
        trajectory_start_x = 3.95
        trajectory_end_x = -3.72
        visible_paths: list[Line] = []
        trajectory_guides = VGroup()
        direction_arrows = VGroup()
        for index, mid_height in zip(selected_indices, mid_heights, strict=True):
            velocity = observed_velocities[index]
            assert velocity[0] < 0.0
            slope = velocity[1] / velocity[0]
            delta_x = trajectory_end_x - trajectory_start_x
            delta_y = slope * delta_x
            start = np.array([trajectory_start_x, mid_height - 0.5 * delta_y, 0.0])
            end = np.array([trajectory_end_x, mid_height + 0.5 * delta_y, 0.0])
            path = Line(start, end)
            visible_paths.append(path)
            trajectory_guides.add(path.copy().set_stroke(DM, width=1.15, opacity=0.23))
            direction = (end - start) / np.linalg.norm(end - start)
            midpoint = 0.54 * start + 0.46 * end
            direction_arrows.add(
                Arrow(
                    midpoint - 0.42 * direction,
                    midpoint + 0.42 * direction,
                    buff=0,
                    color=DM,
                    stroke_width=3.0,
                    max_tip_length_to_length_ratio=0.22,
                ).set_opacity(0.82)
            )

        particle_outer_radius = 0.105
        purple_trajectory_top = max(
            max(path.get_start()[1], path.get_end()[1]) for path in visible_paths
        ) + particle_outer_radius
        assert purple_trajectory_top < sightline_lower_edge - 0.20

        wind_cone = Polygon(
            np.array([4.25, 1.16, 0.0]), np.array([-3.87, 0.18, 0.0]),
            np.array([4.25, -2.05, 0.0]), stroke_width=0,
            fill_color=DM, fill_opacity=0.035,
        )
        assert wind_cone.get_top()[1] < sightline_lower_edge - 0.15
        physical_motion = label("dark matter travels toward the observer", 22, DM, "BOLD")
        physical_motion.move_to(np.array([-1.12, -2.16, 0.0]))
        wind_label = label("APPARENT WIND FROM CYGNUS", 29, DM, "BOLD")
        wind_label.to_edge(DOWN, buff=0.32)

        self.play(
            FadeIn(wind_cone),
            LaggedStart(*(Create(path) for path in trajectory_guides), lag_ratio=0.06),
            LaggedStart(*(GrowArrow(arrow) for arrow in direction_arrows), lag_ratio=0.06),
            FadeIn(physical_motion), run_time=1.40,
        )

        def particle_wave() -> LaggedStart:
            animations = []
            for path in visible_paths:
                particle = VGroup(
                    Circle(
                        radius=particle_outer_radius,
                        color=DM, stroke_width=1.3, stroke_opacity=0.65,
                        fill_color=DM, fill_opacity=0.06,
                    ),
                    Dot(radius=0.035, color=DM),
                ).move_to(path.get_start())
                animations.append(
                    Succession(
                        FadeIn(particle, run_time=0.12),
                        MoveAlongPath(particle, path, run_time=2.80, rate_func=linear),
                        FadeOut(particle, run_time=0.16),
                    )
                )
            return LaggedStart(*animations, lag_ratio=0.09)

        self.play(particle_wave(), run_time=3.65)
        self.play(Write(wind_label), run_time=0.90)
        self.wait(0.70)
        self.play(particle_wave(), run_time=3.50)
        self.wait(1.40)
        show_brand_outro(self)
