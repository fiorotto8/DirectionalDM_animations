"""Load the small public configuration and one optional private override."""

from __future__ import annotations

import copy
import math
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
PLACEHOLDER = "PLACEHOLDER"
LOCAL_CONFIG_ENV = "CYGNO_LOCAL_CONFIG"


class ConfigurationError(ValueError):
    """Raised when public or private configuration is incomplete or invalid."""


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ConfigurationError(f"Expected a mapping in {path}")
    if data.get("schema_version") != 1:
        raise ConfigurationError(f"{path} must declare schema_version: 1")
    return data


def _local_path() -> Path:
    override = os.environ.get(LOCAL_CONFIG_ENV)
    return Path(override).expanduser().resolve() if override else CONFIG_DIR / "local.yaml"


_PROTECTED_SCIENCE_SECTIONS = {
    "conventions",
    "presentation_projection",
    "scale_up",
    "scope",
}


def _merge_science_overlay(
    public: Mapping[str, Any],
    private: Mapping[str, Any],
    *,
    path: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Fill public placeholders without allowing local convention changes."""

    merged = copy.deepcopy(dict(public))
    for key, private_value in private.items():
        key_path = (*path, str(key))
        dotted = ".".join(key_path)
        if key not in public:
            if not path or path[0] in _PROTECTED_SCIENCE_SECTIONS:
                raise ConfigurationError(
                    f"config/local.yaml cannot add public science field {dotted}"
                )
            merged[key] = copy.deepcopy(private_value)
            continue

        public_value = public[key]
        if public_value == PLACEHOLDER:
            merged[key] = copy.deepcopy(private_value)
        elif isinstance(public_value, Mapping) and isinstance(private_value, Mapping):
            merged[key] = _merge_science_overlay(
                public_value,
                private_value,
                path=key_path,
            )
        elif private_value != public_value:
            raise ConfigurationError(
                f"config/local.yaml cannot override public science invariant {dotted}"
            )
    return merged


def load_local(*, required: bool = False) -> dict[str, Any]:
    """Load the single ignored local override, if present."""

    path = _local_path()
    if not path.is_file():
        if required:
            raise ConfigurationError(
                f"Private configuration is required: create {path} as described in "
                "README.md#private-inputs"
            )
        return {}
    return _read_yaml(path)


def load_science(
    *, require_local: bool = False, include_local: bool = True
) -> dict[str, Any]:
    """Load public scientific conventions and overlay private collaboration data."""

    public = _read_yaml(CONFIG_DIR / "science.yaml")
    public.pop("schema_version", None)
    if require_local and not include_local:
        raise ConfigurationError("require_local and include_local=False are incompatible")
    local = load_local(required=require_local) if include_local else {}
    private_science = local.get("science", {})
    if not isinstance(private_science, Mapping):
        raise ConfigurationError("config/local.yaml: science must be a mapping")
    return _merge_science_overlay(public, private_science)


def load_branding() -> dict[str, Any]:
    """Load the public brand layout and official social destination."""

    data = _read_yaml(CONFIG_DIR / "branding.yaml")
    data.pop("schema_version", None)
    required = {"handle", "page_url", "logo_path", "signature", "outro",
                "website_url", "website_qr_path", "instagram_qr_path", "watermark"}
    missing = sorted(required.difference(data))
    if missing:
        raise ConfigurationError(f"branding.yaml is missing: {', '.join(missing)}")
    return data


def load_scene_manifest() -> list[dict[str, Any]]:
    """Return the ordered production-scene manifest."""

    data = _read_yaml(CONFIG_DIR / "scenes.yaml")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ConfigurationError("scenes.yaml must contain a non-empty scenes list")

    required = {"id", "file", "class_name", "output_name", "requires_local_science"}
    identifiers: set[str] = set()
    result: list[dict[str, Any]] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ConfigurationError("Each scene-manifest entry must be a mapping")
        missing = sorted(required.difference(scene))
        if missing:
            raise ConfigurationError(f"Scene entry is missing: {', '.join(missing)}")
        identifier = scene["id"]
        if not isinstance(identifier, str) or identifier in identifiers:
            raise ConfigurationError(f"Invalid or duplicate scene id: {identifier!r}")
        identifiers.add(identifier)
        source = ROOT / str(scene["file"])
        if not source.is_file():
            raise ConfigurationError(f"Scene source does not exist: {source}")
        result.append(copy.deepcopy(scene))
    return result


def is_placeholder(value: Any) -> bool:
    return value == PLACEHOLDER


def require_numeric(value: Any, field_name: str, *, positive: bool = False) -> float:
    """Return a finite number or fail before a placeholder enters geometry."""

    if is_placeholder(value):
        raise ConfigurationError(f"{field_name} is PLACEHOLDER")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{field_name} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0.0):
        qualifier = "positive and " if positive else ""
        raise ConfigurationError(f"{field_name} must be {qualifier}finite")
    return result


def require_triplet(value: Any, field_name: str) -> tuple[float, float, float]:
    """Return a positive numeric length/depth/height triplet."""

    if is_placeholder(value):
        raise ConfigurationError(f"{field_name} is PLACEHOLDER")
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) != 3:
        raise ConfigurationError(f"{field_name} must be a three-value sequence")
    return tuple(require_numeric(item, field_name, positive=True) for item in value)  # type: ignore[return-value]


def require_positive_integer(value: Any, field_name: str) -> int:
    """Return a strictly positive integer for discrete detector structure."""

    numeric = require_numeric(value, field_name, positive=True)
    if not numeric.is_integer():
        raise ConfigurationError(f"{field_name} must be an integer")
    return int(numeric)


def require_nonbottom_shell_layers(
    outer_envelope: Any,
    inner_void: Any,
    approximate_thickness: Any,
    field_name: str,
) -> tuple[float, float, float]:
    """Validate left/right, front/back, and top layers around a floor-level void."""

    outer_length, outer_depth, outer_height = require_triplet(
        outer_envelope, f"{field_name}.outer_envelope"
    )
    inner_length, inner_depth, inner_height = require_triplet(
        inner_void, f"{field_name}.inner_void"
    )
    target = require_numeric(
        approximate_thickness,
        f"{field_name}.approximate_thickness",
        positive=True,
    )
    layers = (
        (outer_length - inner_length) / 2,
        (outer_depth - inner_depth) / 2,
        outer_height - inner_height,
    )
    if any(layer <= 0 for layer in layers):
        raise ConfigurationError(
            f"{field_name}: inner void must be smaller than the outer envelope"
        )
    tolerance = max(50.0, 0.10 * target)
    if any(abs(layer - target) > tolerance for layer in layers):
        raise ConfigurationError(
            f"{field_name}: envelope-derived layers disagree with the approximate thickness"
        )
    return layers


def assert_publication_clearance() -> None:
    """Refuse release packaging until all written approvals are recorded locally."""

    local = load_local(required=True)
    publication = local.get("publication")
    if not isinstance(publication, Mapping):
        raise ConfigurationError("config/local.yaml must contain publication approvals")

    failures: list[str] = []
    for name in ("branding", "technical_data", "scene_05"):
        record = publication.get(name)
        if not isinstance(record, Mapping) or record.get("approved") is not True:
            failures.append(name)
            continue
        for field in ("approved_by", "approved_on", "evidence"):
            value = record.get(field)
            if not isinstance(value, str) or not value.strip() or value == PLACEHOLDER:
                failures.append(f"{name}.{field}")
    if failures:
        raise ConfigurationError(
            "Publication clearance is incomplete: " + ", ".join(failures)
        )
