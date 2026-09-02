"""Reusable scientific primitives for the CYGNO animations."""

from .physics import (
    N_CYG,
    SCATTER_DIAGRAM_INCOMING,
    ScatterState,
    direction_from_convention,
    elastic_scatter_lab,
    electron_drift_velocity,
    observer_frame_velocities,
    paired_halo_velocities,
)

__all__ = [
    "N_CYG",
    "SCATTER_DIAGRAM_INCOMING",
    "ScatterState",
    "direction_from_convention",
    "elastic_scatter_lab",
    "electron_drift_velocity",
    "observer_frame_velocities",
    "paired_halo_velocities",
]
