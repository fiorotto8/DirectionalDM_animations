"""Pure numerical helpers for direction and two-body kinematics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


N_CYG = np.array([1.0, 0.0])
SCATTER_DIAGRAM_INCOMING = np.array([1.0, 0.0])


@dataclass(frozen=True)
class ScatterState:
    p_in: np.ndarray
    p_out: np.ndarray
    p_recoil: np.ndarray
    v_projectile_out: np.ndarray
    v_target_out: np.ndarray
    kinetic_energy_in: float
    kinetic_energy_out: float

    @property
    def q(self) -> np.ndarray:
        return self.p_in - self.p_out


def _unit(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=float)
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Direction vector cannot be zero")
    return vector / norm


def direction_from_convention(value: str) -> np.ndarray:
    """Translate one configured Cygnus-direction token into a unit vector."""

    directions = {
        "+n_cyg": N_CYG,
        "-n_cyg": -N_CYG,
    }
    try:
        return directions[value].copy()
    except KeyError as exc:
        raise ValueError(f"Unsupported direction convention: {value!r}") from exc


def paired_halo_velocities(
    seed: int = 17,
    n_pairs: int = 18,
    sigma: float = 0.58,
) -> np.ndarray:
    """Return deterministic paired samples with an exactly zero halo-frame mean."""

    if n_pairs < 1:
        raise ValueError("n_pairs must be positive")
    rng = np.random.default_rng(seed)
    base = rng.normal(0.0, sigma, size=(n_pairs, 2))
    velocities = np.vstack((base, -base))
    rng.shuffle(velocities)
    return velocities


def observer_frame_velocities(
    halo_velocities: np.ndarray,
    observer_velocity: np.ndarray,
) -> np.ndarray:
    """Galilean transform from halo frame into the selected observer frame."""

    halo_velocities = np.asarray(halo_velocities, dtype=float)
    observer_velocity = np.asarray(observer_velocity, dtype=float)
    if halo_velocities.ndim != 2 or halo_velocities.shape[1] != 2:
        raise ValueError("halo_velocities must have shape (N, 2)")
    if observer_velocity.shape != (2,):
        raise ValueError("observer_velocity must have shape (2,)")
    return halo_velocities - observer_velocity


def elastic_scatter_lab(
    mass_projectile: float = 0.60,
    mass_target: float = 1.00,
    speed: float = 1.0,
    theta_cm: float = np.deg2rad(80.0),
    incoming_direction: np.ndarray | None = None,
) -> ScatterState:
    """Compute an elastic two-body scatter for a target initially at rest.

    ``theta_cm`` rotates the projectile velocity in the centre-of-mass frame.
    Values are dimensionless and illustrative; conservation laws are exact.
    The default rightward direction is local to the scatter diagram and is not
    the Galactic ``+n_cyg`` convention.
    """

    if mass_projectile <= 0 or mass_target <= 0 or speed <= 0:
        raise ValueError("Masses and speed must be positive")

    if incoming_direction is None:
        incoming_direction = SCATTER_DIAGRAM_INCOMING
    direction = _unit(np.asarray(incoming_direction, dtype=float))
    v_in = speed * direction
    v_cm = (mass_projectile / (mass_projectile + mass_target)) * v_in
    u_projectile = v_in - v_cm

    rotation = np.array(
        [
            [np.cos(theta_cm), -np.sin(theta_cm)],
            [np.sin(theta_cm), np.cos(theta_cm)],
        ]
    )
    u_projectile_out = rotation @ u_projectile
    u_target_out = -(mass_projectile / mass_target) * u_projectile_out

    v_projectile_out = v_cm + u_projectile_out
    v_target_out = v_cm + u_target_out

    p_in = mass_projectile * v_in
    p_out = mass_projectile * v_projectile_out
    p_recoil = mass_target * v_target_out

    kinetic_energy_in = 0.5 * mass_projectile * np.dot(v_in, v_in)
    kinetic_energy_out = (
        0.5 * mass_projectile * np.dot(v_projectile_out, v_projectile_out)
        + 0.5 * mass_target * np.dot(v_target_out, v_target_out)
    )

    return ScatterState(
        p_in=p_in,
        p_out=p_out,
        p_recoil=p_recoil,
        v_projectile_out=v_projectile_out,
        v_target_out=v_target_out,
        kinetic_energy_in=kinetic_energy_in,
        kinetic_energy_out=kinetic_energy_out,
    )


def electron_drift_velocity(electric_field: np.ndarray, mobility: float = 1.0) -> np.ndarray:
    """Electron drift is opposite the conventional electric-field vector."""

    if mobility <= 0:
        raise ValueError("mobility must be positive")
    return -mobility * np.asarray(electric_field, dtype=float)
