"""Deterministic schematic ER/NR generators for outreach comparisons."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TrackSample:
    points: np.ndarray
    weights: np.ndarray
    kind: str

    @property
    def visible_integral(self) -> float:
        return float(np.sum(self.weights))

    @property
    def end_to_end(self) -> float:
        return float(np.linalg.norm(self.points[-1] - self.points[0]))

    @property
    def path_length(self) -> float:
        return float(np.linalg.norm(np.diff(self.points, axis=0), axis=1).sum())


def _normalise_visible(weights: np.ndarray, visible_integral: float) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    return weights * (visible_integral / weights.sum())


def simulate_er_track(seed: int = 31, visible_integral: float = 1.0) -> TrackSample:
    """Longer, sparse and tortuous illustrative electron-recoil topology."""

    rng = np.random.default_rng(seed)
    n_points = 44
    direction = np.array([1.0, 0.08])
    points = [np.zeros(2)]
    for index in range(1, n_points):
        turn = rng.normal(0.0, 0.16)
        c, s = np.cos(turn), np.sin(turn)
        direction = np.array([c * direction[0] - s * direction[1], s * direction[0] + c * direction[1]])
        direction /= np.linalg.norm(direction)
        step = rng.uniform(0.075, 0.14)
        points.append(points[-1] + step * direction)
    points_array = np.asarray(points)
    weights = _normalise_visible(rng.uniform(0.55, 1.15, n_points), visible_integral)
    return TrackSample(points=points_array, weights=weights, kind="ER")


def simulate_nr_track(seed: int = 43, visible_integral: float = 1.0) -> TrackSample:
    """Short, straggled NR with a qualitative longitudinal charge asymmetry.

    For the low-energy schematic used here, the beginning of the recoil path
    carries more visible ionization than the stopping end.  The exact size and
    even the sign of a measured head--tail estimator depend on recoil species,
    energy, gas, diffusion and reconstruction, so only the qualitative gradient
    is encoded.
    """

    rng = np.random.default_rng(seed)
    n_points = 28
    direction = np.array([1.0, 0.0])
    points = [np.zeros(2)]
    for index in range(1, n_points):
        turn = rng.normal(0.0, 0.34)
        c, s = np.cos(turn), np.sin(turn)
        direction = np.array([c * direction[0] - s * direction[1], s * direction[0] + c * direction[1]])
        direction /= np.linalg.norm(direction)
        step = rng.uniform(0.025, 0.055)
        points.append(points[-1] + step * direction)
    points_array = np.asarray(points)
    longitudinal_profile = np.linspace(1.75, 0.52, n_points)
    fluctuations = rng.uniform(0.82, 1.18, n_points)
    weights = _normalise_visible(longitudinal_profile * fluctuations, visible_integral)
    return TrackSample(points=points_array, weights=weights, kind="NR")


def diffuse_track(track: TrackSample, sigma: float = 0.08, seed: int = 59) -> TrackSample:
    """Apply the same schematic diffusion model to a primary track."""

    if sigma < 0:
        raise ValueError("sigma cannot be negative")
    rng = np.random.default_rng(seed)
    points = track.points + rng.normal(0.0, sigma, size=track.points.shape)
    return TrackSample(points=points, weights=track.weights.copy(), kind=track.kind)
