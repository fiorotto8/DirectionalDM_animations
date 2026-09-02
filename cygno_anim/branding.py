"""Shared CYGNO signature and Instagram outro for every production scene."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
import qrcode
from manim import (
    DOWN,
    RIGHT,
    Circle,
    FadeIn,
    FadeOut,
    Group,
    ImageMobject,
    Rectangle,
    RoundedRectangle,
    Scene,
    Text,
    WHITE,
    config,
)
from PIL import Image, ImageDraw

from cygno_anim.config import load_branding
from cygno_anim.visuals import BACKGROUND, CYGNUS, FONT, FOREGROUND, MUTED


ROOT = Path(__file__).resolve().parents[1]
_SIGNATURE_ATTRIBUTE = "_cygno_brand_signature"
_TRANSITION_DURATION = 0.60


@dataclass(frozen=True)
class BrandingSettings:
    """Validated values from the public branding configuration."""

    handle: str
    page_url: str
    logo_path: Path
    signature_width: float
    signature_height: float
    signature_margin: float
    signature_background_opacity: float
    outro_duration: float
    qr_width: float


def _positive_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a positive number")
    number = float(value)
    if not np.isfinite(number) or number <= 0.0:
        raise ValueError(f"{field} must be a positive finite number")
    return number


@lru_cache(maxsize=1)
def load_branding_settings() -> BrandingSettings:
    """Load branding settings and resolve the private logo asset path."""

    data = load_branding()

    handle = data.get("handle")
    page_url = data.get("page_url")
    raw_logo_path = data.get("logo_path")
    signature = data.get("signature")
    outro = data.get("outro")
    if not isinstance(handle, str) or not handle.startswith("@"):
        raise ValueError("branding.handle must be an @-prefixed account name")
    if not isinstance(page_url, str):
        raise TypeError("branding.page_url must be a URL string")
    parsed_url = urlsplit(page_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("branding.page_url must be an absolute HTTPS URL")
    if not isinstance(raw_logo_path, str) or not raw_logo_path.strip():
        raise TypeError("branding.logo_path must be a non-empty path string")
    if not isinstance(signature, dict) or not isinstance(outro, dict):
        raise TypeError("branding.signature and branding.outro must be mappings")

    logo_path = Path(raw_logo_path)
    if not logo_path.is_absolute():
        logo_path = ROOT / logo_path
    logo_path = logo_path.resolve()
    if not logo_path.is_file():
        raise FileNotFoundError(
            f"Missing private CYGNO logo: {logo_path}. "
            "See README.md#private-inputs before rendering."
        )

    background_opacity = signature.get("background_opacity")
    if isinstance(background_opacity, bool) or not isinstance(
        background_opacity, (int, float)
    ):
        raise TypeError("branding.signature.background_opacity must be numeric")
    background_opacity = float(background_opacity)
    if not 0.0 <= background_opacity <= 1.0:
        raise ValueError("branding.signature.background_opacity must be in [0, 1]")

    settings = BrandingSettings(
        handle=handle,
        page_url=page_url,
        logo_path=logo_path,
        signature_width=_positive_number(signature.get("width"), "branding.signature.width"),
        signature_height=_positive_number(signature.get("height"), "branding.signature.height"),
        signature_margin=_positive_number(signature.get("margin"), "branding.signature.margin"),
        signature_background_opacity=background_opacity,
        outro_duration=_positive_number(outro.get("duration"), "branding.outro.duration"),
        qr_width=_positive_number(outro.get("qr_width"), "branding.outro.qr_width"),
    )
    if settings.outro_duration < _TRANSITION_DURATION:
        raise ValueError(
            f"branding.outro.duration must be at least {_TRANSITION_DURATION:.1f} seconds"
        )
    return settings


@lru_cache(maxsize=4)
def _circular_logo_pixels(path: Path, size: int = 768) -> np.ndarray:
    """Load the official raster and apply a circular alpha mask in memory."""

    with Image.open(path) as source:
        logo = source.convert("RGBA")
        side = min(logo.size)
        left = (logo.width - side) // 2
        top = (logo.height - side) // 2
        logo = logo.crop((left, top, left + side, top + side))
        logo = logo.resize((size, size), Image.Resampling.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((1, 1, size - 2, size - 2), fill=255)
    logo.putalpha(mask)
    return np.asarray(logo)


def _logo_mobject(settings: BrandingSettings) -> ImageMobject:
    return ImageMobject(_circular_logo_pixels(settings.logo_path))


def _frame(scene: Scene):
    """Return the animated camera frame when the scene exposes one."""

    return getattr(scene.camera, "frame", None)


def _screen_scale(scene: Scene) -> float:
    frame = _frame(scene)
    return float(frame.get_width() / config.frame_width) if frame is not None else 1.0


def _screen_center(scene: Scene) -> np.ndarray:
    frame = _frame(scene)
    return frame.get_center() if frame is not None else np.zeros(3)


def _place_signature(signature: Group, scene: Scene, settings: BrandingSettings) -> None:
    """Place a signature in the visible frame using screen-space dimensions."""

    frame = _frame(scene)
    scale = _screen_scale(scene)
    target_width = settings.signature_width * scale
    if signature.width > 0.0:
        signature.scale(target_width / signature.width)

    if frame is None:
        right_edge = config.frame_width / 2.0
        top_edge = config.frame_height / 2.0
    else:
        right_edge = frame.get_right()[0]
        top_edge = frame.get_top()[1]
    signature.move_to(
        np.array(
            [
                right_edge - settings.signature_margin * scale - signature.width / 2.0,
                top_edge - settings.signature_margin * scale - signature.height / 2.0,
                0.0,
            ]
        )
    )


def _build_signature(settings: BrandingSettings) -> Group:
    panel = RoundedRectangle(
        width=settings.signature_width,
        height=settings.signature_height,
        corner_radius=0.13,
        stroke_color=CYGNUS,
        stroke_width=1.0,
        stroke_opacity=0.58,
        fill_color=BACKGROUND,
        fill_opacity=settings.signature_background_opacity,
    )
    logo = _logo_mobject(settings)
    logo.set_height(settings.signature_height * 0.72)
    logo.move_to(panel.get_left() + RIGHT * (settings.signature_height * 0.52))
    logo_ring = Circle(
        radius=logo.height / 2.0,
        stroke_color=CYGNUS,
        stroke_width=1.1,
        stroke_opacity=0.72,
    ).move_to(logo)

    handle = Text(settings.handle, font=FONT, color=FOREGROUND, weight="BOLD")
    handle.scale_to_fit_height(settings.signature_height * 0.32)
    maximum_handle_width = settings.signature_width - settings.signature_height - 0.24
    if handle.width > maximum_handle_width:
        handle.scale_to_fit_width(maximum_handle_width)
    handle.next_to(logo, RIGHT, buff=0.13)
    handle.set_y(panel.get_y())
    return Group(panel, logo, logo_ring, handle)


def add_brand_signature(scene: Scene) -> Group:
    """Add the persistent CYGNO/Instagram lockup to a scene.

    Moving-camera scenes receive a lightweight updater that keeps the lockup
    fixed in the same screen-space corner through pans and zooms.
    """

    existing = getattr(scene, _SIGNATURE_ATTRIBUTE, None)
    if existing is not None:
        return existing

    settings = load_branding_settings()
    signature = _build_signature(settings)
    _place_signature(signature, scene, settings)
    signature.set_z_index(1000, family=True)

    if _frame(scene) is not None:
        signature.add_updater(
            lambda mobject: _place_signature(mobject, scene, settings)
        )

    setattr(scene, _SIGNATURE_ATTRIBUTE, signature)
    scene.add(signature)
    return signature


def _display_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.netloc}{parsed.path}".rstrip("/")


def _qr_mobject(settings: BrandingSettings) -> ImageMobject:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(settings.page_url)
    qr.make(fit=True)
    pixels = np.asarray(qr.make_image(fill_color="black", back_color="white").convert("RGB"))
    image = ImageMobject(pixels)
    image.set_width(settings.qr_width)
    return image


def _build_outro(scene: Scene, settings: BrandingSettings) -> Group:
    backdrop = Rectangle(
        width=config.frame_width,
        height=config.frame_height,
        stroke_width=0,
        fill_color=BACKGROUND,
        fill_opacity=1.0,
    )

    logo = _logo_mobject(settings)
    logo.set_height(1.78)
    logo_ring = Circle(
        radius=logo.height / 2.0,
        stroke_color=CYGNUS,
        stroke_width=2.0,
    ).move_to(logo)
    logo_mark = Group(logo, logo_ring)
    invitation = Text("Follow CYGNO", font=FONT, color=FOREGROUND, weight="BOLD").scale(0.63)
    handle = Text(settings.handle, font=FONT, color=CYGNUS, weight="BOLD").scale(0.52)
    page = Text(_display_url(settings.page_url), font=FONT, color=MUTED).scale(0.25)
    identity = Group(logo_mark, invitation, handle, page).arrange(
        DOWN, buff=0.20
    )

    qr_image = _qr_mobject(settings)
    qr_frame = RoundedRectangle(
        width=qr_image.width + 0.26,
        height=qr_image.height + 0.26,
        corner_radius=0.12,
        stroke_color=CYGNUS,
        stroke_width=1.8,
        fill_color=WHITE,
        fill_opacity=1.0,
    ).move_to(qr_image)
    qr_caption = Text("Instagram", font=FONT, color=FOREGROUND, weight="BOLD").scale(0.27)
    qr_caption.next_to(qr_frame, DOWN, buff=0.16)
    qr_group = Group(qr_frame, qr_image, qr_caption)

    content = Group(identity, qr_group).arrange(RIGHT, buff=1.18)
    content.move_to(np.zeros(3))
    outro = Group(backdrop, content)

    scale = _screen_scale(scene)
    outro.scale(scale)
    outro.move_to(_screen_center(scene))
    outro.set_z_index(1100, family=True)
    return outro


def show_brand_outro(scene: Scene) -> None:
    """Replace the scene with the standard four-second Instagram end card."""

    settings = load_branding_settings()
    signature = getattr(scene, _SIGNATURE_ATTRIBUTE, None)
    if signature is not None:
        signature.clear_updaters()

    outro = _build_outro(scene, settings)
    current = list(scene.mobjects)
    scene.play(
        *(FadeOut(mobject) for mobject in current),
        FadeIn(outro),
        run_time=_TRANSITION_DURATION,
    )
    scene.wait(settings.outro_duration - _TRANSITION_DURATION)
