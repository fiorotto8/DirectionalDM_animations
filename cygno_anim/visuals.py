"""Shared Manim visual language for the production scenes."""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circle,
    DashedLine,
    Dot,
    Scene,
    Text,
    VGroup,
)


BACKGROUND = "#07111F"
FOREGROUND = "#F4F7FB"
MUTED = "#8EA8BE"
CYGNUS = "#55DDE0"
SOLAR = "#F5C451"
WIMP = "#B477FF"
NUCLEUS = "#FF8B5C"
ELECTRON = "#70E1C1"
PHOTON = "#FFE173"
FIELD = "#4F8CFF"
GEM = "#D78B4A"
FONT = "DejaVu Sans"

# Galactic-view palette.
HALO = "#315C7C"
GALACTIC_DISK = "#79A9C5"
EARTH = "#4DA3FF"
LAND = "#7DD49A"
STAR = "#C7E7F6"

# Elastic-scatter palette.
SCATTER_BACKGROUND = "#07131B"
SCATTER_FOREGROUND = "#EDF7F4"
SCATTER_MUTED = "#8CA4AA"
SCATTER_WIMP = "#9A88FF"
SCATTER_RECOIL = "#FF9D62"
SCATTER_ELECTRON = "#58D9F0"
SCATTER_PANEL = "#10242E"
SCATTER_DIM = "#3E5660"

# Detector and data-product surfaces.
CHAMBER_FILL = "#10243A"
READOUT_PANEL = "#0B192A"
PIPELINE_PANEL = "#0A1727"
NUCLEON_ALT = "#E85D75"

# LNGS context and service palette.
ROCK_DARK = "#152737"
ROCK_MID = "#29465B"
ROCK_LIGHT = "#42687D"
GALLERY = "#82A7BF"
HALL = "#55C6B3"
WATER = "#4F8CFF"
POLYETHYLENE = "#B9D9E8"
COPPER = "#C87945"
ROAD = "#D9E5ED"
DATA = "#79E6FF"
GAS = "#72D7A0"
HIGH_VOLTAGE = "#F5C15A"
ROCK_LAMP = "#FFD28A"
ROADBED = "#1B2C3B"
TUNNEL_WALL = "#202F3A"
GALLERY_INNER = "#263742"
PORTAL_EDGE = "#9CB7C7"
PORTAL_INNER = "#22343F"
ROUTE = "#F2C46D"
SERVICE_PANEL = "#314653"
COPPER_HIGHLIGHT = "#F1B17A"


class ScientificScene(Scene):
    """Base scene with stable styling and compact title helpers."""

    def setup(self):
        self.camera.background_color = BACKGROUND

    def title_block(self, kicker: str, title: str) -> VGroup:
        kicker_text = Text(kicker.upper(), font=FONT, color=CYGNUS, weight="BOLD").scale(0.25)
        title_text = Text(title, font=FONT, color=FOREGROUND, weight="BOLD").scale(0.58)
        group = VGroup(kicker_text, title_text).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        group.to_corner(UP + LEFT, buff=0.42)
        return group

def label(text: str, color: str = FOREGROUND, scale: float = 0.28, weight: str = "NORMAL") -> Text:
    return Text(text, font=FONT, color=color, weight=weight).scale(scale)


def semantic_arrow(
    start: np.ndarray,
    end: np.ndarray,
    text: str,
    color: str,
    label_direction: np.ndarray = UP,
    dashed: bool = False,
    stroke_width: float = 4.5,
) -> VGroup:
    if dashed:
        shaft = DashedLine(start, end, color=color, stroke_width=stroke_width, dash_length=0.14)
        tip = Arrow(start, end, color=color, stroke_width=0, buff=0, tip_length=0.2).get_tip()
        arrow = VGroup(shaft, tip)
    else:
        arrow = Arrow(start, end, color=color, stroke_width=stroke_width, buff=0, tip_length=0.2)
    caption = label(text, color=color, scale=0.25, weight="BOLD")
    caption.next_to(arrow, label_direction, buff=0.12)
    return VGroup(arrow, caption)


def nucleus_marker(radius: float = 0.22) -> VGroup:
    offsets = [LEFT * 0.09, RIGHT * 0.09, UP * 0.08, DOWN * 0.08]
    nucleons = VGroup(
        *[
            Circle(
                radius=radius * 0.44,
                stroke_width=1.1,
                stroke_color=NUCLEUS,
                fill_color=NUCLEUS if i % 2 == 0 else NUCLEON_ALT,
                fill_opacity=0.88,
            ).shift(offset)
            for i, offset in enumerate(offsets)
        ]
    )
    return nucleons


def electron_marker(radius: float = 0.035) -> Dot:
    return Dot(radius=radius, color=ELECTRON)
