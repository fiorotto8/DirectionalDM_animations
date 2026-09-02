"""CAD-informed but parameter-free detector diagram primitives."""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    Line,
    Polygon,
    Rectangle,
    RoundedRectangle,
    VGroup,
)

from .config import load_science, require_positive_integer
from .visuals import (
    BACKGROUND,
    CHAMBER_FILL,
    CYGNUS,
    FIELD,
    FOREGROUND,
    GEM,
    MUTED,
    PHOTON,
)


def gem_foil(height: float = 3.5, thickness: float = 0.10, holes: int = 11) -> VGroup:
    foil = RoundedRectangle(
        width=thickness,
        height=height,
        corner_radius=thickness * 0.3,
        stroke_color=GEM,
        stroke_width=1.4,
        fill_color=GEM,
        fill_opacity=0.72,
    )
    hole_group = VGroup()
    for index in range(holes):
        y = -height * 0.43 + index * (height * 0.86 / max(holes - 1, 1))
        hole = Circle(
            radius=thickness * 0.17,
            stroke_color=BACKGROUND,
            stroke_width=0.8,
            fill_color=BACKGROUND,
            fill_opacity=1.0,
        ).move_to([0, y, 0])
        hole_group.add(hole)
    return VGroup(foil, hole_group)


def gem_stack(
    height: float = 3.5,
    spacing: float = 0.24,
    stages: int | None = None,
) -> VGroup:
    if stages is None:
        stages = require_positive_integer(
            load_science(include_local=False)["geometry"]["gem_stages_per_end"],
            "geometry.gem_stages_per_end",
        )
    foils = VGroup(*[gem_foil(height=height) for _ in range(stages)])
    foils.arrange(RIGHT, buff=spacing)
    return foils


def camera_icon(scale: float = 1.0) -> VGroup:
    body = RoundedRectangle(
        width=0.62,
        height=0.42,
        corner_radius=0.06,
        stroke_color=CYGNUS,
        stroke_width=1.5,
        fill_color=CYGNUS,
        fill_opacity=0.13,
    )
    lens = Polygon(
        [0.31, 0.16, 0],
        [0.56, 0.10, 0],
        [0.56, -0.10, 0],
        [0.31, -0.16, 0],
        stroke_color=CYGNUS,
        stroke_width=1.5,
        fill_color=CYGNUS,
        fill_opacity=0.2,
    )
    return VGroup(body, lens).scale(scale)


def pmt_icon(scale: float = 1.0) -> VGroup:
    bulb = Circle(
        radius=0.13,
        stroke_color=PHOTON,
        stroke_width=1.5,
        fill_color=PHOTON,
        fill_opacity=0.12,
    )
    stem = Rectangle(
        width=0.14,
        height=0.16,
        stroke_color=PHOTON,
        stroke_width=1.2,
        fill_color=PHOTON,
        fill_opacity=0.12,
    ).next_to(bulb, LEFT, buff=-0.01)
    return VGroup(stem, bulb).scale(scale)


def half_tpc(width: float = 4.2, height: float = 3.6, direction=RIGHT) -> VGroup:
    sign = 1 if direction[0] >= 0 else -1
    chamber = Rectangle(
        width=width,
        height=height,
        stroke_color=MUTED,
        stroke_width=1.5,
        fill_color=CHAMBER_FILL,
        fill_opacity=0.34,
    )
    cathode = Line(DOWN * height * 0.45, UP * height * 0.45, color=FOREGROUND, stroke_width=4)
    cathode.move_to(chamber.get_left() if sign > 0 else chamber.get_right())

    stack = gem_stack(height=height * 0.78, spacing=0.16)
    stack.move_to(chamber.get_right() + LEFT * 0.28 if sign > 0 else chamber.get_left() + RIGHT * 0.28)

    cage_lines = VGroup()
    for fraction in (0.2, 0.4, 0.6, 0.8):
        x = chamber.get_left()[0] + width * fraction
        cage_lines.add(Line([x, -height * 0.43, 0], [x, height * 0.43, 0], color=FIELD, stroke_width=0.65).set_opacity(0.28))

    return VGroup(chamber, cage_lines, cathode, stack)
