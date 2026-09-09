"""Locate CYGNO at LNGS and assemble the detector, readout and shielding."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    Group,
    ImageMobject,
    DashedLine,
    linear,
    Indicate,
    LaggedStart,
    Line,
    MoveAlongPath,
    MovingCameraScene,
    Polygon,
    Rectangle,
    RoundedRectangle,
    VGroup,
    VMobject,
    Write,
)


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cygno_anim.branding import add_brand_signature, show_brand_outro
from cygno_anim.config import (
    PLACEHOLDER,
    load_science,
    require_nonbottom_shell_layers,
    require_numeric,
    require_positive_integer,
    require_triplet,
)
from cygno_anim.detector import half_tpc, camera_icon, pmt_icon
from cygno_anim.visuals import (
    BACKGROUND,
    COPPER,
    COPPER_HIGHLIGHT,
    CYGNUS,
    FOREGROUND,
    GALLERY,
    HALL,
    MUTED,
    POLYETHYLENE,
    PHOTON,
    ROAD,
    ROADBED,
    ROCK_DARK,
    ROCK_LAMP,
    ROCK_LIGHT,
    ROCK_MID,
    ScientificScene,
    WATER,
    label,
)


ROUTE_SEQUENCE = (
    "A24 → LNGS ENTRANCE → HALL C → HALL B → HALL F"
)


def formatted_value(value: object, unit: str = "") -> str:
    """Format a configured value, suppressing unresolved values on screen."""

    if value == PLACEHOLDER:
        return ""
    if isinstance(value, (int, float)):
        numeric = f"{value:g}"
        return f"{numeric} {unit}".strip()
    if isinstance(value, (list, tuple)):
        joined = " × ".join(f"{item:g}" if isinstance(item, (int, float)) else str(item) for item in value)
        return f"{joined} {unit}".strip()
    return f"{value} {unit}".strip()


class LNGSPositioning(MovingCameraScene):
    """An independently renderable site-to-shielding scene."""

    def setup(self) -> None:
        super().setup()
        self.camera.background_color = BACKGROUND

    def title_block(self, kicker: str, title: str) -> VGroup:
        """Reuse the shared title style with a moving-camera scene."""

        return ScientificScene.title_block(self, kicker, title).set_z_index(20)

    def construct(self) -> None:
        science = load_science(require_local=True)
        site = science["site"]
        shielding = science["shielding"]
        if site.get("location") != "LNGS Hall F":
            raise ValueError("Scene 05 requires the configured LNGS Hall F location")

        add_brand_signature(self)

        default_frame_width = float(self.camera.frame.width)
        default_frame_center = self.camera.frame.get_center().copy()

        title = self.title_block("LNGS", "Inside Gran Sasso")
        self.play(FadeIn(title, shift=DOWN * 0.12), run_time=1.10)

        mountain_layers, highway, laboratory, mountain_labels = self.mountain_context()
        self.play(
            LaggedStart(*[Create(layer) for layer in mountain_layers], lag_ratio=0.16),
            run_time=2.20,
        )
        self.play(Create(highway), run_time=1.60)
        self.play(FadeIn(laboratory, shift=UP * 0.10), Write(mountain_labels), run_time=1.40)
        self.play(Indicate(laboratory, color=CYGNUS, scale_factor=1.04), run_time=0.90)
        self.wait(3.00)

        mountain = VGroup(mountain_layers, highway, laboratory)
        self.play(
            FadeOut(title), FadeOut(mountain_labels), FadeOut(mountain),
            run_time=1.10,
        )
        self.show_underground_route()

        shield_title = self.title_block(
            "CYGNO-04 · SHIELDING",
            "From components to assembly",
        )
        shield_base, stages = self.shielding_assembly(shielding)
        self.camera.frame.set(width=default_frame_width).move_to(default_frame_center)
        self.wait(0.10)
        title = shield_title
        self.play(FadeIn(title), FadeIn(shield_base, shift=UP * 0.06), run_time=1.05)

        preview_centres = (
            np.array([-3.70, -0.72, 0.0]),
            np.array([-4.65, -0.42, 0.0]),
            np.array([3.95, -0.30, 0.0]),
            np.array([-4.45, 0.28, 0.0]),
            np.array([4.15, 0.12, 0.0]),
        )
        preview_scales = (0.55, 0.72, 0.72, 0.88, 0.42)
        stage_names = (
            "CONTAINMENT POOL",
            "POLYETHYLENE",
            "COPPER",
            "DETECTOR",
            "WATER",
        )
        stage_colors = (WATER, POLYETHYLENE, COPPER, HALL, WATER)
        components_by_name = {
            name: component
            for name, (component, _, _) in zip(stage_names, stages)
        }

        for (component, annotations, mass_badge), preview_centre, preview_scale, stage_name, stage_color in zip(
            stages,
            preview_centres,
            preview_scales,
            stage_names,
            stage_colors,
        ):
            component.save_state()
            component.scale(preview_scale).move_to(preview_centre)
            component_name = label(stage_name, color=stage_color, scale=0.245, weight="BOLD")
            component_name.next_to(component, DOWN, buff=0.16)
            self.play(
                FadeIn(component, shift=UP * 0.08),
                FadeIn(component_name, shift=UP * 0.04),
                run_time=0.95,
            )
            self.wait(0.55)
            self.play(
                component.animate.restore(),
                FadeOut(component_name),
                run_time=1.20,
            )
            self.play(FadeIn(annotations, shift=UP * 0.04), run_time=0.90)
            if mass_badge is not None:
                self.play(FadeIn(mass_badge, scale=0.86), run_time=0.65)
                self.play(
                    Indicate(
                        mass_badge[3],
                        color=mass_badge[2].get_color(),
                        scale_factor=1.08,
                    ),
                    run_time=0.75,
                )
            self.wait(2.25)
            stage_annotations = [FadeOut(annotations)]
            if mass_badge is not None:
                stage_annotations.append(FadeOut(mass_badge))
            self.play(*stage_annotations, run_time=0.55)

        self.wait(2.80)

        show_brand_outro(self)

    def mountain_context(self) -> tuple[VGroup, VGroup, VGroup, VGroup]:
        """Draw the route-bearing A24 tunnel and the LNGS entrance."""

        back = Polygon(
            [-6.8, -2.05, 0],
            [-5.55, -0.78, 0],
            [-4.52, -1.08, 0],
            [-3.20, 0.26, 0],
            [-2.15, -0.25, 0],
            [-0.48, 1.56, 0],
            [0.42, 0.52, 0],
            [1.42, 1.14, 0],
            [2.62, 0.02, 0],
            [3.73, 0.62, 0],
            [5.08, -0.44, 0],
            [6.8, -2.05, 0],
            color=ROCK_LIGHT,
            fill_color=ROCK_DARK,
            fill_opacity=0.98,
            stroke_width=2.5,
        )
        middle = Polygon(
            [-6.8, -2.05, 0],
            [-5.20, -1.18, 0],
            [-4.05, -1.47, 0],
            [-2.68, -0.42, 0],
            [-1.42, -1.05, 0],
            [0.08, 0.20, 0],
            [1.35, -0.79, 0],
            [2.86, -0.16, 0],
            [4.32, -1.08, 0],
            [6.8, -2.05, 0],
            color=ROCK_MID,
            fill_color=ROCK_MID,
            fill_opacity=0.82,
            stroke_width=1.7,
        )
        foreground = Polygon(
            [-6.8, -2.05, 0],
            [-5.28, -1.56, 0],
            [-3.68, -1.86, 0],
            [-2.20, -1.18, 0],
            [-0.52, -1.72, 0],
            [1.14, -1.08, 0],
            [2.92, -1.60, 0],
            [4.64, -1.06, 0],
            [6.8, -2.05, 0],
            color=ROCK_LIGHT,
            fill_color=ROCK_LIGHT,
            fill_opacity=0.42,
            stroke_width=1.4,
        )
        ridge_accents = VGroup(
            Line([-5.32, -0.82, 0], [-4.50, -1.08, 0], color=ROCK_LIGHT, stroke_width=1.2),
            Line([-3.18, 0.22, 0], [-2.17, -0.24, 0], color=ROCK_LIGHT, stroke_width=1.2),
            Line([-0.46, 1.50, 0], [0.40, 0.52, 0], color=ROCK_LIGHT, stroke_width=1.2),
            Line([1.43, 1.09, 0], [2.62, 0.02, 0], color=ROCK_LIGHT, stroke_width=1.2),
            Line([3.73, 0.57, 0], [5.05, -0.44, 0], color=ROCK_LIGHT, stroke_width=1.2),
        ).set_opacity(0.58)
        ground = Line([-6.85, -2.06, 0], [6.85, -2.06, 0], color=GALLERY, stroke_width=1.5)

        connected_points = [
            [-6.84, -1.54, 0],
            [-4.82, -1.48, 0],
            [-2.74, -1.40, 0],
            [-0.52, -1.36, 0],
            [1.68, -1.39, 0],
            [3.92, -1.52, 0],
            [6.84, -1.76, 0],
        ]
        motorway_angle = np.arctan2(
            connected_points[-1][1] - connected_points[0][1],
            connected_points[-1][0] - connected_points[0][0],
        )
        def motorway_bore(
            points: list[list[float]],
            shell_color: str,
            shell_opacity: float,
        ) -> VGroup:
            axis = VMobject().set_points_smoothly(
                [np.array(point, dtype=float) for point in points]
            )
            cut = axis.copy().set_stroke(BACKGROUND, width=13.0, opacity=0.94)
            shell = axis.copy().set_stroke(
                shell_color,
                width=8.5,
                opacity=shell_opacity,
            )
            road = axis.copy().set_stroke(ROADBED, width=5.2, opacity=1.0)
            lights = VGroup(
                *[
                    Dot(
                        axis.point_from_proportion(float(proportion)),
                        radius=0.018,
                        color=ROCK_LAMP,
                    )
                    for proportion in np.linspace(0.08, 0.92, 11)
                ]
            )
            portal_normal = UP * 0.13
            portals = VGroup(
                Line(
                    np.array(points[0]) - portal_normal,
                    np.array(points[0]) + portal_normal,
                    color=shell_color,
                    stroke_width=2.0,
                ),
                Line(
                    np.array(points[-1]) - portal_normal,
                    np.array(points[-1]) + portal_normal,
                    color=shell_color,
                    stroke_width=2.0,
                ),
            )
            return VGroup(cut, shell, road, lights, portals)

        motorway_teramo_rome = motorway_bore(connected_points, ROAD, 0.92)

        access_axis = VMobject().set_points_smoothly(
            [
                np.array([0.22, -1.37, 0]),
                np.array([0.30, -1.18, 0]),
                np.array([0.50, -1.02, 0]),
                np.array([0.69, -0.96, 0]),
            ]
        )
        access_cut = access_axis.copy().set_stroke(BACKGROUND, width=11.0, opacity=0.92)
        access_concrete = access_axis.copy().set_stroke(GALLERY, width=7.0, opacity=0.96)
        access_road = access_axis.copy().set_stroke(ROADBED, width=4.0, opacity=1.0)
        access_lights = VGroup(
            *[
                Dot(
                    access_axis.point_from_proportion(float(proportion)),
                    radius=0.019,
                    color=ROCK_LAMP,
                )
                for proportion in (0.30, 0.62, 0.90)
            ]
        )
        dedicated_access = VGroup(
            access_cut,
            access_concrete,
            access_road,
            access_lights,
        )
        highway = VGroup(motorway_teramo_rome, dedicated_access)

        lngs_point = np.array([0.69, -0.96, 0.0])
        lngs_marker = VGroup(
            Circle(radius=0.13, color=CYGNUS, stroke_width=1.8),
            Dot(radius=0.047, color=CYGNUS),
        ).move_to(lngs_point)
        laboratory = VGroup(lngs_marker)

        massif_label = label("GRAN SASSO", color=FOREGROUND, scale=0.38, weight="BOLD")
        massif_label.move_to([3.15, 1.30, 0])
        road_label = label("A24 MOTORWAY TUNNEL", color=ROAD, scale=0.28, weight="BOLD")
        road_label.rotate(motorway_angle).move_to([-2.72, -0.83, 0])
        road_leader = Line([-1.88, -0.98, 0], [-1.30, -1.47, 0], color=ROAD, stroke_width=1.6)
        lngs_label = label("LNGS ENTRANCE", color=CYGNUS, scale=0.30, weight="BOLD")
        lngs_label.move_to([1.31, -0.54, 0])
        lngs_leader = Line([0.96, -0.70, 0], lngs_point + UP * 0.10, color=CYGNUS, stroke_width=1.8)

        laquila = label("L'AQUILA / ROMA", color=MUTED, scale=0.24, weight="BOLD")
        laquila.rotate(motorway_angle).move_to([-5.62, -2.45, 0])
        teramo = label("TERAMO", color=MUTED, scale=0.24, weight="BOLD")
        teramo.rotate(motorway_angle).move_to([5.95, -2.46, 0])

        mountain_layers = VGroup(back, middle, foreground, ridge_accents, ground)
        mountain_labels = VGroup(
            massif_label,
            road_label,
            road_leader,
            lngs_label,
            lngs_leader,
            laquila,
            teramo,
        )
        return mountain_layers, highway, laboratory, mountain_labels

    def show_underground_route(self) -> None:
        """Overlay an illustrative access route on the supplied, unaltered PNG.

        Coordinates below are pixels in View_exp_underground_2.png (1151x1160),
        measured from the top left. The labelled companion reference identifies
        A on the left, B in the middle, and C on the right. Hall F is the narrow
        A-B connector at (638, 786)--(714, 817), above the broad access gallery.
        These image waypoints are presentation geometry, not a surveyed route.
        """
        image_path = ROOT / "assets/LNGS/View_exp_underground_2.png"
        if not image_path.is_file():
            raise FileNotFoundError(f"Scene 05 requires the supplied image: {image_path}")
        illustration = ImageMobject(str(image_path)).set_height(7.1)
        illustration.move_to([0, -0.15, 0])
        self.play(FadeIn(illustration), run_time=1.3)
        self.wait(1.8)

        # Zoom the original image itself; the camera and branding stay fixed.
        enlarged = illustration.copy().set_width(18.0)
        focus = np.array([650.0 / 1151 - .5, .5 - 930.0 / 1160, 0])
        enlarged.move_to(-focus * [enlarged.width, enlarged.height, 1])
        self.play(illustration.animate.become(enlarged), run_time=2.6)

        def pixel(x, y):
            return illustration.get_center() + np.array([
                (x / 1151 - .5) * illustration.width,
                (.5 - y / 1160) * illustration.height, 0,
            ])

        header = self.title_block("LNGS", "Route to Hall F")
        header.add_background_rectangle(color=BACKGROUND, opacity=.90, buff=.12)
        header.set_z_index(20, family=True)
        route_text = label(ROUTE_SEQUENCE, color=FOREGROUND, scale=.25, weight="BOLD")
        route_text.move_to([0, -3.60, 0])
        route_text.add_background_rectangle(color=BACKGROUND, opacity=.92, buff=.14)
        route_text.set_z_index(20, family=True)

        hall_labels = VGroup()
        for name, anchor, centre in (
            ("Hall A", (519, 811), (475, 778)),
            ("Hall B", (841, 788), (903, 812)),
            ("Hall C", (958, 865), (1027, 961)),
        ):
            text = label(name, color=FOREGROUND, scale=.26, weight="BOLD").move_to(pixel(*centre))
            text.add_background_rectangle(color=BACKGROUND, opacity=.88, buff=.08)
            leader = Line(text.get_bottom(), pixel(*anchor), color=FOREGROUND, stroke_width=1.0)
            hall_labels.add(VGroup(leader, text))
        hall_labels.set_z_index(12, family=True)
        self.play(FadeIn(header), FadeIn(route_text), FadeIn(hall_labels), run_time=.9)
        self.wait(1.0)

        # Follow the entry bend and main gallery past C and B, then enter the
        # small A-B connector. Do not mark the large foreground gallery as F.
        route_segments = (
            ([(982, 1104), (982, 1060), (982, 1023),
              (979, 1006), (973, 995), (959, 985), (837, 928)], 4.4),
            ([(837, 928), (777, 900), (716, 871), (679, 852)], 3.1),
            ([(679, 852), (703, 841), (731, 825), (714, 816), (676, 801)], 3.0),
        )
        marker = VGroup(
            Dot(radius=.082, color=BACKGROUND, fill_opacity=.90),
            Dot(radius=.048, color=CYGNUS, stroke_color=FOREGROUND, stroke_width=1),
        ).move_to(pixel(*route_segments[0][0][0])).set_z_index(15, family=True)
        self.play(FadeIn(marker), run_time=.4)
        for points, duration in route_segments:
            path = VMobject().set_points_as_corners([pixel(*point) for point in points])
            self.play(MoveAlongPath(marker, path, rate_func=linear), run_time=duration)
            self.wait(.55)

        destination = pixel(676, 801)
        hall_f_text = label("HallF - CYGNO04", color=CYGNUS, scale=.27, weight="BOLD")
        hall_f_text.move_to([-2.3, 2.55, 0])
        hall_f_text.add_background_rectangle(color=BACKGROUND, opacity=.94, buff=.10)
        hall_f_leader = DashedLine(hall_f_text.get_right(), destination + UP * .13,
                                  color=CYGNUS, stroke_width=1.4, dash_length=.06)
        hall_f_ring = Circle(radius=.13, color=CYGNUS, stroke_width=2).move_to(destination)
        hall_f = VGroup(hall_f_leader, hall_f_ring, hall_f_text).set_z_index(16, family=True)
        self.play(FadeIn(hall_f), FadeOut(hall_labels), run_time=.9)
        self.play(Indicate(hall_f_ring, scale_factor=1.35), run_time=.9)
        self.wait(3.0)
        self.play(FadeOut(Group(illustration, header, route_text, marker, hall_f)), run_time=.95)

    def dimension_line(
        self,
        start: np.ndarray,
        end: np.ndarray,
        text: str,
        color: str,
        label_side: np.ndarray,
        text_scale: float = 0.285,
    ) -> VGroup:
        """Create a capped architectural dimension with a horizontal caption."""

        start = np.asarray(start, dtype=float)
        end = np.asarray(end, dtype=float)
        vector = end - start
        norm = float(np.linalg.norm(vector[:2]))
        if norm == 0:
            raise ValueError("dimension line requires two distinct points")
        tangent = vector / norm
        normal = np.array([-tangent[1], tangent[0], 0.0])
        line = Line(start, end, color=color, stroke_width=2.0)
        cap_a = Line(start - normal * 0.10, start + normal * 0.10, color=color, stroke_width=2.0)
        cap_b = Line(end - normal * 0.10, end + normal * 0.10, color=color, stroke_width=2.0)
        caption = label(text, color=color, scale=text_scale, weight="BOLD")
        caption.next_to(line, label_side, buff=0.12)
        return VGroup(line, cap_a, cap_b, caption)

    def mass_badge(
        self,
        name: str,
        value: str,
        color: str,
        centre: list[float],
    ) -> VGroup:
        """Create a high-contrast physical mass callout shared by all shields."""

        panel = RoundedRectangle(
            width=2.55,
            height=1.08,
            corner_radius=0.11,
            stroke_color=color,
            stroke_width=2.2,
            fill_color=BACKGROUND,
            fill_opacity=0.94,
        ).move_to(centre)
        accent = Line(
            panel.get_corner(UP + LEFT) + DOWN * 0.08,
            panel.get_corner(DOWN + LEFT) + UP * 0.08,
            color=color,
            stroke_width=4.0,
        )
        name_text = label(name, color=color, scale=0.245, weight="BOLD")
        name_text.move_to(panel.get_top() + DOWN * 0.24)
        value_text = label(value, color=FOREGROUND, scale=0.46, weight="BOLD")
        value_text.move_to(panel.get_center() + DOWN * 0.17)
        return VGroup(panel, accent, name_text, value_text)

    def shielding_assembly(
        self,
        shielding: dict,
    ) -> tuple[VGroup, list[tuple[VGroup, VGroup, VGroup | None]]]:
        """Build the separately sourced protection components for assembly."""

        dimensions = shielding["dimensions"]
        thicknesses = shielding["material_thicknesses"]
        masses = shielding["component_masses_tonnes"]
        water_data = shielding["water"]

        outer_length_mm, outer_depth_mm, outer_height_mm = require_triplet(
            dimensions["outer_envelope_mm"],
            "shielding.dimensions.outer_envelope_mm",
        )
        inner_length_mm, inner_depth_mm, inner_height_mm = require_triplet(
            dimensions["inner_occupied_void_mm"],
            "shielding.dimensions.inner_occupied_void_mm",
        )
        pe_length_mm, pe_depth_mm, pe_height_mm = require_triplet(
            dimensions["polyethylene_base_overall_mm"],
            "shielding.dimensions.polyethylene_base_overall_mm",
        )
        copper_length_mm, copper_depth_mm, copper_height_mm = require_triplet(
            dimensions.get("copper_shield_outer_mm", PLACEHOLDER),
            "shielding.dimensions.copper_shield_outer_mm",
        )
        copper_thickness_mm = require_numeric(
            thicknesses["copper_shield_mm"],
            "shielding.material_thicknesses.copper_shield_mm",
            positive=True,
        )
        water_thickness_mm = require_numeric(
            thicknesses["water_shield_approx_mm"],
            "shielding.material_thicknesses.water_shield_approx_mm",
            positive=True,
        )
        pool_footprint = dimensions.get("safety_pool_footprint_mm", PLACEHOLDER)
        if not isinstance(pool_footprint, (list, tuple)) or len(pool_footprint) != 2:
            raise ValueError(
                "shielding.dimensions.safety_pool_footprint_mm must contain two values"
            )
        pool_length_mm = require_numeric(
            pool_footprint[0],
            "shielding.dimensions.safety_pool_footprint_mm[0]",
            positive=True,
        )
        pool_depth_mm = require_numeric(
            pool_footprint[1],
            "shielding.dimensions.safety_pool_footprint_mm[1]",
            positive=True,
        )
        copper_mass = require_numeric(
            masses["copper"],
            "shielding.component_masses_tonnes.copper",
            positive=True,
        )
        pe_mass = require_numeric(
            masses["polyethylene"],
            "shielding.component_masses_tonnes.polyethylene",
            positive=True,
        )
        water_mass = require_numeric(
            water_data["derived_mass_tonnes_approx"],
            "shielding.water.derived_mass_tonnes_approx",
            positive=True,
        )

        centre_x = -0.35
        floor_y = -2.65
        outer_width = 6.15
        display_scale = outer_width / outer_length_mm
        inner_width = outer_width * inner_length_mm / outer_length_mm
        require_nonbottom_shell_layers(
            (outer_length_mm, outer_depth_mm, outer_height_mm),
            (inner_length_mm, inner_depth_mm, inner_height_mm),
            water_thickness_mm,
            "shielding.water",
        )

        # Component envelopes come from independent source views.  Their exact
        # labels are preserved while the final assembly view is normalized into
        # the documented occupied height without asserting an unprovided fit.
        component_scale = min(
            display_scale,
            inner_height_mm * display_scale / (pe_height_mm + copper_height_mm),
        )
        pe_width = pe_length_mm * component_scale
        pe_height = pe_height_mm * component_scale
        pe_bottom = floor_y
        pe_top = pe_bottom + pe_height

        floor = Line([-6.45, floor_y, 0], [6.45, floor_y, 0], color=GALLERY, stroke_width=2.0)
        floor_glow = Line([-5.15, floor_y + 0.04, 0], [4.45, floor_y + 0.04, 0], color=CYGNUS, stroke_width=0.9)
        hall_f_mark = label("HALL F", color=MUTED, scale=0.25, weight="BOLD").move_to([5.45, floor_y + 0.28, 0])
        shield_base = VGroup(floor, floor_glow, hall_f_mark)

        pool_width = pool_length_mm * display_scale
        pool_lip_height = 0.22
        pool_bottom = Line(
            [centre_x - pool_width / 2, floor_y - 0.08, 0],
            [centre_x + pool_width / 2, floor_y - 0.08, 0],
            color=WATER,
            stroke_width=3.0,
        )
        pool_walls = VGroup(
            Line(
                pool_bottom.get_start(),
                pool_bottom.get_start() + UP * pool_lip_height,
                color=WATER,
                stroke_width=3.0,
            ),
            Line(
                pool_bottom.get_end(),
                pool_bottom.get_end() + UP * pool_lip_height,
                color=WATER,
                stroke_width=3.0,
            ),
        )
        pool_fill = Rectangle(
            width=pool_width,
            height=pool_lip_height,
            stroke_width=0,
            fill_color=WATER,
            fill_opacity=0.055,
        ).move_to([centre_x, floor_y + 0.03, 0])
        stage_pool = VGroup(pool_fill, pool_bottom, pool_walls)
        pool_footprint_line = self.dimension_line(
            np.array([centre_x - pool_width / 2, -3.18, 0]),
            np.array([centre_x + pool_width / 2, -3.18, 0]),
            f"{pool_length_mm / 1000:.2f} × {pool_depth_mm / 1000:.2f} m footprint",
            WATER,
            DOWN,
            text_scale=0.255,
        )
        pool_annotations = VGroup(pool_footprint_line)

        pe_base = Rectangle(
            width=pe_width,
            height=pe_height,
            stroke_color=POLYETHYLENE,
            stroke_width=2.6,
            fill_color=POLYETHYLENE,
            fill_opacity=0.48,
        ).move_to([centre_x, pe_bottom + pe_height / 2, 0])
        base_top_glint = Line(
            pe_base.get_corner(UP + LEFT),
            pe_base.get_corner(UP + RIGHT),
            color=FOREGROUND,
            stroke_width=1.0,
        ).set_opacity(0.30)
        stage_pe = VGroup(pe_base, base_top_glint)
        pe_footprint = self.dimension_line(
            np.array([centre_x - pe_width / 2, -3.02, 0]),
            np.array([centre_x + pe_width / 2, -3.02, 0]),
            f"{pe_length_mm / 1000:.2f} × {pe_depth_mm / 1000:.2f} m footprint",
            POLYETHYLENE,
            DOWN,
        )
        pe_thickness_line = self.dimension_line(
            np.array([centre_x + pe_width / 2 + 0.28, pe_bottom, 0]),
            np.array([centre_x + pe_width / 2 + 0.28, pe_top, 0]),
            f"{pe_height_mm / 1000:.2f} m overall height",
            POLYETHYLENE,
            RIGHT,
            text_scale=0.255,
        )
        pe_mass_text = formatted_value(pe_mass, "t")
        pe_badge = self.mass_badge(
            "POLYETHYLENE BASE",
            pe_mass_text,
            POLYETHYLENE,
            [4.68, -1.55, 0],
        )
        pe_leader = Line(
            pe_base.get_right(),
            pe_badge.get_left() + LEFT * 0.10,
            color=POLYETHYLENE,
            stroke_width=1.7,
        )
        pe_annotations = VGroup(pe_footprint, pe_thickness_line, pe_leader)

        copper_width = copper_length_mm * component_scale
        copper_height = copper_height_mm * component_scale
        copper_wall = copper_thickness_mm * component_scale
        copper_inner_width = copper_width - 2 * copper_wall
        copper_inner_height = copper_height - 2 * copper_wall
        if copper_inner_width <= 0 or copper_inner_height <= 0:
            raise ValueError("copper wall thickness leaves no detector cavity")
        copper_bottom_y = pe_top
        copper_top_y = copper_bottom_y + copper_height
        copper_left_x = centre_x - copper_width / 2
        copper_right_x = centre_x + copper_width / 2
        copper_bottom = Rectangle(
            width=copper_width,
            height=copper_wall,
            stroke_color=COPPER,
            stroke_width=2.2,
            fill_color=COPPER,
            fill_opacity=0.72,
        ).move_to([centre_x, copper_bottom_y + copper_wall / 2, 0])
        copper_left = Rectangle(
            width=copper_wall,
            height=copper_height,
            stroke_color=COPPER,
            stroke_width=2.2,
            fill_color=COPPER,
            fill_opacity=0.58,
        ).move_to([copper_left_x + copper_wall / 2, copper_bottom_y + copper_height / 2, 0])
        copper_right = copper_left.copy().move_to(
            [copper_right_x - copper_wall / 2, copper_bottom_y + copper_height / 2, 0]
        )
        copper_top = Rectangle(
            width=copper_width,
            height=copper_wall,
            stroke_color=COPPER,
            stroke_width=2.2,
            fill_color=COPPER,
            fill_opacity=0.58,
        ).move_to([centre_x, copper_top_y - copper_wall / 2, 0])
        copper_inner_glow = RoundedRectangle(
            width=copper_inner_width,
            height=copper_inner_height,
            corner_radius=0.06,
            stroke_color=COPPER_HIGHLIGHT,
            stroke_width=1.0,
            fill_opacity=0.0,
        ).move_to([centre_x, copper_bottom_y + copper_height / 2, 0])
        stage_copper = VGroup(copper_bottom, copper_left, copper_right, copper_top, copper_inner_glow)
        copper_footprint = self.dimension_line(
            np.array([copper_left_x, copper_top_y + 0.27, 0]),
            np.array([copper_right_x, copper_top_y + 0.27, 0]),
            f"{copper_length_mm / 1000:.2f} × {copper_depth_mm / 1000:.2f} m footprint",
            COPPER,
            UP,
        )
        copper_height_line = self.dimension_line(
            np.array([copper_right_x + 0.30, copper_bottom_y, 0]),
            np.array([copper_right_x + 0.30, copper_top_y, 0]),
            f"{copper_height_mm / 1000:.2f} m overall height",
            COPPER,
            RIGHT,
            text_scale=0.255,
        )
        copper_wall_text = label(
            f"{copper_thickness_mm / 10:.0f} cm Cu wall",
            color=COPPER,
            scale=0.275,
            weight="BOLD",
        ).move_to([copper_left_x - 1.05, copper_top_y - 0.15, 0])
        copper_wall_leader = Line(
            copper_wall_text.get_right() + RIGHT * 0.08,
            copper_top.get_left() + RIGHT * 0.32,
            color=COPPER,
            stroke_width=1.8,
        )
        copper_thickness = VGroup(copper_wall_leader, copper_wall_text)
        depth_panel = RoundedRectangle(
            width=2.90,
            height=1.28,
            corner_radius=0.10,
            stroke_color=MUTED,
            stroke_width=1.3,
            fill_color=BACKGROUND,
            fill_opacity=0.92,
        ).move_to([4.72, 1.46, 0])
        depth_heading = label("DEPTH · TOP VIEW", color=FOREGROUND, scale=0.21, weight="BOLD")
        depth_heading.move_to(depth_panel.get_top() + DOWN * 0.20)
        pe_depth_bar = Line(
            [3.62, 1.45, 0],
            [4.98, 1.45, 0],
            color=POLYETHYLENE,
            stroke_width=5.0,
        )
        copper_depth_bar = Line(
            [3.62, 1.08, 0],
            [5.19, 1.08, 0],
            color=COPPER,
            stroke_width=5.0,
        )
        pe_depth_name = label(
            f"PE {pe_depth_mm / 1000:.2f} m",
            color=POLYETHYLENE,
            scale=0.205,
            weight="BOLD",
        ).next_to(pe_depth_bar, RIGHT, buff=0.10)
        copper_depth_name = label(
            f"Cu {copper_depth_mm / 1000:.2f} m",
            color=COPPER,
            scale=0.205,
            weight="BOLD",
        ).next_to(copper_depth_bar, RIGHT, buff=0.10)
        depth_comparison = VGroup(
            depth_panel,
            depth_heading,
            pe_depth_bar,
            copper_depth_bar,
            pe_depth_name,
            copper_depth_name,
        )
        copper_mass_text = formatted_value(copper_mass, "t")
        copper_badge = self.mass_badge(
            "COPPER SHIELD",
            copper_mass_text,
            COPPER,
            [4.68, -1.35, 0],
        )
        copper_leader = Line(
            copper_right.get_right(),
            copper_badge.get_left() + LEFT * 0.10,
            color=COPPER,
            stroke_width=1.7,
        )
        copper_annotations = VGroup(
            copper_footprint,
            copper_height_line,
            copper_thickness,
            depth_comparison,
            copper_leader,
        )

        left_tpc = half_tpc(width=1.22, height=0.92, direction=LEFT)
        right_tpc = half_tpc(width=1.22, height=0.92, direction=RIGHT)
        detector_core = VGroup(left_tpc, right_tpc).arrange(RIGHT, buff=0.0)
        detector_frame = RoundedRectangle(
            width=detector_core.width + 0.20,
            height=detector_core.height + 0.18,
            corner_radius=0.08,
            stroke_color=HALL,
            stroke_width=2.2,
            fill_color=HALL,
            fill_opacity=0.055,
        ).move_to(detector_core)
        detector_body = VGroup(detector_frame, detector_core)
        detector_fit = min(
            0.84 * copper_inner_width / detector_body.width,
            0.84 * copper_inner_height / detector_body.height,
            1.0,
        )
        detector_body.scale(detector_fit)
        copper_interior_centre = np.array(
            [centre_x, copper_bottom_y + copper_height / 2, 0]
        )
        detector_body.move_to(copper_interior_centre)
        if detector_body.width > copper_inner_width or detector_body.height > copper_inner_height:
            raise ValueError("detector drawing does not fit inside the copper cavity")
        detector_name = label("CYGNO-04", color=HALL, scale=0.25, weight="BOLD")
        detector_name.move_to(detector_frame.get_top() + DOWN * 0.13)
        stage_detector = VGroup(detector_body, detector_name)
        detector_card = label("CYGNO-04 DETECTOR", color=HALL, scale=0.245, weight="BOLD")
        detector_card.move_to([4.60, -0.84, 0])
        detector_leader = Line(
            detector_frame.get_right(),
            detector_card.get_left() + LEFT * 0.12,
            color=HALL,
            stroke_width=1.7,
        )
        detector_annotations = VGroup(detector_leader, detector_card)

        outer_height = outer_width * outer_height_mm / outer_length_mm
        side_width = (outer_width - inner_width) / 2
        # The lateral tanks stand directly on the Hall-F floor.  There is no
        # water layer beneath the PE/copper/detector stack.
        outer_bottom_y = floor_y
        outer_top_y = outer_bottom_y + outer_height
        water_top_bottom_y = outer_bottom_y + inner_height_mm * display_scale
        side_height = inner_height_mm * display_scale
        top_height = outer_top_y - water_top_bottom_y
        if top_height <= 0:
            raise ValueError("shielding stack exceeds the documented water envelope")
        outer_left_x = centre_x - outer_width / 2
        outer_right_x = centre_x + outer_width / 2

        water_side_blocks = VGroup()
        side_rows = 4
        side_cell_height = side_height / side_rows
        side_block_height = side_cell_height - 0.035
        for side_sign in (-1, 1):
            side_centre_x = centre_x + side_sign * (inner_width / 2 + side_width / 2)
            for index in range(side_rows):
                block = RoundedRectangle(
                    width=side_width - 0.035,
                    height=side_block_height,
                    corner_radius=0.045,
                    stroke_color=WATER,
                    stroke_width=1.4,
                    fill_color=WATER,
                    fill_opacity=0.22 + 0.025 * (index % 2),
                ).move_to(
                    [
                        side_centre_x,
                        outer_bottom_y + side_block_height / 2 + index * side_cell_height,
                        0,
                    ]
                )
                water_side_blocks.add(block)

        water_top_blocks = VGroup()
        top_columns = 6
        for index in range(top_columns):
            block = RoundedRectangle(
                width=outer_width / top_columns - 0.035,
                height=top_height - 0.035,
                corner_radius=0.045,
                stroke_color=WATER,
                stroke_width=1.4,
                fill_color=WATER,
                fill_opacity=0.25 + 0.02 * (index % 2),
            ).move_to(
                [
                    outer_left_x + (index + 0.5) * outer_width / top_columns,
                    water_top_bottom_y + top_height / 2,
                    0,
                ]
            )
            water_top_blocks.add(block)

        water_straps = VGroup(
            Line([outer_left_x, water_top_bottom_y, 0], [outer_right_x, water_top_bottom_y, 0], color=CYGNUS, stroke_width=2.0),
            Line([outer_left_x, outer_top_y, 0], [outer_right_x, outer_top_y, 0], color=CYGNUS, stroke_width=2.0),
            Line([outer_left_x, outer_bottom_y, 0], [outer_left_x, water_top_bottom_y, 0], color=CYGNUS, stroke_width=2.0),
            Line([outer_right_x, outer_bottom_y, 0], [outer_right_x, water_top_bottom_y, 0], color=CYGNUS, stroke_width=2.0),
        )
        stage_water = VGroup(water_side_blocks, water_top_blocks, water_straps)

        water_width = self.dimension_line(
            np.array([outer_left_x, outer_top_y + 0.23, 0]),
            np.array([outer_right_x, outer_top_y + 0.23, 0]),
            f"{outer_length_mm / 1000:.2f} m outer width",
            WATER,
            UP,
        )
        water_height = self.dimension_line(
            np.array([outer_right_x + 0.30, outer_bottom_y, 0]),
            np.array([outer_right_x + 0.30, outer_top_y, 0]),
            f"{outer_height_mm / 1000:.2f} m height",
            WATER,
            RIGHT,
        )
        depth_text = label(
            f"{outer_depth_mm / 1000:.2f} m depth",
            color=WATER,
            scale=0.285,
            weight="BOLD",
        ).move_to([4.68, 1.55, 0])
        depth_leader = Line(
            [outer_right_x - 0.18, outer_top_y - 0.12, 0],
            depth_text.get_left() + LEFT * 0.10,
            color=WATER,
            stroke_width=1.8,
        )
        water_mass_card = self.mass_badge(
            "WATER SHIELD",
            f"≈{water_mass:.0f} t",
            WATER,
            [4.68, -1.62, 0],
        )
        water_mass_leader = Line(
            [outer_right_x, outer_bottom_y + 0.62, 0],
            water_mass_card.get_left() + LEFT * 0.10,
            color=WATER,
            stroke_width=1.7,
        )
        water_annotations = VGroup(
            water_width,
            water_height,
            depth_leader,
            depth_text,
            water_mass_leader,
        )

        # Use the same optical-end projection as Scenes 03 and 04. Sensors
        # accompany the detector during insertion and stay in the copper/water gap.
        science = load_science(include_local=False)
        camera_count = require_positive_integer(
            science["geometry"]["cameras_per_optical_end"],
            "geometry.cameras_per_optical_end",
        )
        pmt_count = require_positive_integer(
            science["presentation_projection"]["pmts_visible_per_optical_end"],
            "presentation_projection.pmts_visible_per_optical_end",
        )
        gap = (inner_width-copper_width)/2
        cameras, pmts = VGroup(), VGroup()
        for side in (-1, 1):
            camera_x = centre_x + side*(copper_width/2 + gap*.69)
            pmt_x = centre_x + side*(copper_width/2 + gap*.22)
            for y in np.linspace(copper_bottom_y+.25*copper_height,
                                 copper_bottom_y+.75*copper_height, camera_count):
                camera = camera_icon().set_width(min(.32, gap*.42))
                if side == 1:
                    camera.flip(UP)
                cameras.add(camera.move_to([camera_x, y, 0]))
            for y in np.linspace(copper_bottom_y+.16*copper_height,
                                 copper_bottom_y+.84*copper_height, pmt_count):
                pmt = pmt_icon().set_width(min(.22, gap*.30))
                if side == 1:
                    pmt.flip(UP)
                pmts.add(pmt.move_to([pmt_x, y, 0]))
        stage_detector.add(cameras, pmts)
        readout_heading = label("Readout", color=FOREGROUND, scale=.27, weight="BOLD")
        camera_caption = label("qCMOS cameras", color=CYGNUS, scale=.25)
        pmt_caption = label("PMTs", color=PHOTON, scale=.25)
        readout_labels = VGroup(readout_heading, camera_caption, pmt_caption).arrange(DOWN, buff=.12)
        readout_labels.move_to([4.55, .40, 0])
        camera_leader = Line(cameras.get_right(), camera_caption.get_left()+LEFT*.10,
                             color=CYGNUS, stroke_width=1.4)
        pmt_leader = Line(pmts[-1].get_right(), pmt_caption.get_left()+LEFT*.10,
                          color=PHOTON, stroke_width=1.4)
        detector_annotations.add(readout_labels, camera_leader, pmt_leader)

        stages = [
            (stage_pool, pool_annotations, None),
            (stage_pe, pe_annotations, pe_badge),
            (stage_copper, copper_annotations, copper_badge),
            (stage_detector, detector_annotations, None),
            (stage_water, water_annotations, water_mass_card),
        ]
        return shield_base, stages
