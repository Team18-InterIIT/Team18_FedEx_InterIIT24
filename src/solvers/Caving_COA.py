import random
import sys
from itertools import permutations

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment


class COA(PackingAlgorithm):
    def paste_number(uld: ULD, point_min: Point, point_max: Point):
        paste_number_value = 0

        x1_min, y1_min, z1_min = point_min.x, point_min.y, point_min.z
        x1_max, y1_max, z1_max = point_max.x, point_max.y, point_max.z

        paste_number_value += (
            (x1_min == 0 or x1_max == uld.dim.l)
            + (y1_min == 0 or y1_max == uld.dim.w)
            + (z1_min == 0 or z1_max == uld.dim.h)
        )

        for existing_pkg in uld.packages:
            x0_min, y0_min, z0_min = (
                existing_pkg.corners[0].x,
                existing_pkg.corners[0].y,
                existing_pkg.corners[0].z,
            )
            x0_max, y0_max, z0_max = (
                existing_pkg.corners[1].x,
                existing_pkg.corners[1].y,
                existing_pkg.corners[1].z,
            )
            paste_number_value += (
                (
                    x1_min == x0_max
                    and y0_min <= y1_min < y0_max
                    and z0_min <= z1_min < z0_max
                    # and y0_min < y1_max <= y0_max
                    # and z0_min < z1_max <= z0_max
                )
                + (
                    x1_max == x0_min
                    and y0_min <= y1_min < y0_max
                    and z0_min <= z1_min < z0_max
                    # and y0_min < y1_max <= y0_max
                    # and z0_min < z1_max <= z0_max
                )
                + (
                    y1_min == y0_max
                    and x0_min <= x1_min < x0_max
                    and z0_min <= z1_min < z0_max
                    # and x0_min < x1_max <= x0_max
                    # and z0_min < z1_max <= z0_max
                )
                + (
                    y1_max == y0_min
                    and x0_min <= x1_min < x0_max
                    and z0_min <= z1_min < z0_max
                    # and x0_min < x1_max <= x0_max
                    # and z0_min < z1_max <= z0_max
                )
                + (
                    z1_min == z0_max
                    and x0_min <= x1_min < x0_max
                    and y0_min <= y1_min < y0_max
                    # and x0_min < x1_max <= x0_max
                    # and y0_min < y1_max <= y0_max
                )
                + (
                    z1_max == z0_min
                    and x0_min <= x1_min < x0_max
                    and y0_min <= y1_min < y0_max
                    # and x0_min < x1_max <= x0_max
                    # and y0_min < y1_max <= y0_max
                )
            )

        return paste_number_value

    def paste_ratio(uld: ULD, point_min: Point, point_max: Point):
        """
        It is the packing item's total pasted area, divided by the packing item's total surface area.
        """
        x1_min, y1_min, z1_min = point_min.x, point_min.y, point_min.z
        x1_max, y1_max, z1_max = point_max.x, point_max.y, point_max.z

        paste_area = 0

        if x1_min == 0:
            paste_area += (y1_max - y1_min) * (z1_max - z1_min)

        if x1_max == uld.dim.l:
            paste_area += (y1_max - y1_min) * (z1_max - z1_min)

        if y1_min == 0:
            paste_area += (x1_max - x1_min) * (z1_max - z1_min)

        if y1_max == uld.dim.w:
            paste_area += (x1_max - x1_min) * (z1_max - z1_min)

        if z1_min == 0:
            paste_area += (x1_max - x1_min) * (y1_max - y1_min)

        if z1_max == uld.dim.h:
            paste_area += (x1_max - x1_min) * (y1_max - y1_min)

        for existing_pkg in uld.packages:
            x0_min, y0_min, z0_min = (
                existing_pkg.corners[0].x,
                existing_pkg.corners[0].y,
                existing_pkg.corners[0].z,
            )
            x0_max, y0_max, z0_max = (
                existing_pkg.corners[1].x,
                existing_pkg.corners[1].y,
                existing_pkg.corners[1].z,
            )

            paste_area = 0

            if (
                x1_min == x0_max
                and y0_min <= y1_min < y0_max
                and z0_min <= z1_min < z0_max
            ):
                paste_area += (min(y0_max, y1_max) - y1_min) * (
                    min(z0_max, z1_max) - z1_min
                )

            if (
                x1_max == x0_min
                and y0_min <= y1_min < y0_max
                and z0_min <= z1_min < z0_max
            ):
                paste_area += (min(y0_max, y1_max) - y1_min) * (
                    min(z0_max, z1_max) - z1_min
                )

            if (
                y1_min == y0_max
                and x0_min <= x1_min < x0_max
                and z0_min <= z1_min < z0_max
            ):
                paste_area += (min(x0_max, x1_max) - x1_min) * (
                    min(z0_max, z1_max) - z1_min
                )

            if (
                y1_max == y0_min
                and x0_min <= x1_min < x0_max
                and z0_min <= z1_min < z0_max
            ):
                paste_area += (min(x0_max, x1_max) - x1_min) * (
                    min(z0_max, z1_max) - z1_min
                )

            if (
                z1_min == z0_max
                and x0_min <= x1_min < x0_max
                and y0_min <= y1_min < y0_max
            ):
                paste_area += (min(x0_max, x1_max) - x1_min) * (
                    min(y0_max, y1_max) - y1_min
                )

            if (
                z1_max == z0_min
                and x0_min <= x1_min < x0_max
                and y0_min <= y1_min < y0_max
            ):
                paste_area += (min(x0_max, x1_max) - x1_min) * (
                    min(y0_max, y1_max) - y1_min
                )

        return (
            0.5
            * paste_area
            / (
                (x1_max - x1_min) * (y1_max - y1_min)
                + (y1_max - y1_min) * (z1_max - z1_min)
                + (z1_max - z1_min) * (x1_max - x1_min)
            )
        )

    def distance(pt1: Point, pt2: Point, pt3: Point, pt4: Point) -> int:
        x1_min, y1_min, z1_min = (pt1.x, pt1.y, pt1.z)
        x1_max, y1_max, z1_max = (pt2.x, pt2.y, pt2.z)

        x2_min, y2_min, z2_min = (pt3.x, pt3.y, pt3.z)
        x2_max, y2_max, z2_max = (pt4.x, pt4.y, pt4.z)

        x_distance = max(0, max(x1_min, x2_min) - min(x1_max, x2_max))
        y_distance = max(0, max(y1_min, y2_min) - min(y1_max, y2_max))
        z_distance = max(0, max(z1_min, z2_min) - min(z1_max, z2_max))

        return (x_distance, y_distance, z_distance)

    def distance_coa(uld: ULD, point_min: Point, point_max: Point) -> int:
        paste_number_value = COA.paste_number(uld, point_min, point_max)
        if paste_number_value == 6:
            return 0

        if paste_number_value < 3:
            return -1

        Dx, Dy, Dz = [float("inf")] * 3

        for existing_pkg in uld.packages:
            dx, dy, dz = COA.distance(
                existing_pkg.corners[0],
                existing_pkg.corners[1],
                point_min,
                point_max,
            )
            if dx == 0 or dy == 0 or dz == 0:
                continue

            Dx = min(Dx, dx)
            Dy = min(Dy, dy)
            Dz = min(Dz, dz)

        return min(Dx, Dy, Dz)

    def caving_degree(uld: ULD, point_min: Point, point_max: Point):
        x_min, y_min, z_min = point_min.x, point_min.y, point_min.z
        x_max, y_max, z_max = point_max.x, point_max.y, point_max.z
        volume = (x_max - x_min) * (y_max - y_min) * (z_max - z_min)
        return 1 - COA.distance_coa(uld, point_min, point_max) / ((volume) ** (1 / 3))

    def get_best_state(
        uld_COAs: dict[int, list[Point]],
        pkgs: list[Package],
        env: Environment,
        priority_list: list[str] = None,
        allowed_ULDs: list[int] = None,
    ) -> tuple[Point, Package, Point]:
        best_coa = None
        best_pkg = None
        best_orientation = None
        best_uld = None

        if priority_list is None:
            priority_list = [
                "cost",
                "paste_number",
                "largest_dim",
                "z_gravity",
                "caving_degree",
                "paste_ratio",
                "middle_dim",
                "smallest_dim",
                "y_gravity",
                "x_gravity",
            ]

        if allowed_ULDs is None:
            allowed_ULDs = list(range(len(env.ULDs)))

        values = {
            "paste_number": -1,
            "z_gravity": float("-inf"),
            "caving_degree": -1,
            "paste_ratio": -1,
            "largest_dim": -1,
            "middle_dim": -1,
            "smallest_dim": -1,
            "y_gravity": float("-inf"),
            "x_gravity": float("-inf"),
            "cost": float("-inf"),
            "priority_cost": float("-inf"),
        }

        for uld_id, COAs in uld_COAs.items():
            if uld_id not in allowed_ULDs:
                continue

            uld = env.ULDs[uld_id]
            for coa in COAs:
                for pkg in pkgs:
                    for x_inc, y_inc, z_inc in permutations(
                        (pkg.dim.l, pkg.dim.w, pkg.dim.h)
                    ):
                        point1 = Point(coa.x, coa.y, coa.z)
                        orientation = Point(coa.x + x_inc, coa.y + y_inc, coa.z + z_inc)

                        if not env.add_package(
                            pkg, uld, corners=(point1, orientation), simulate=True
                        ):
                            continue

                        current_values = {
                            "priority_cost": -(
                                env.running_cost + env.K
                                if (not uld.has_priority and pkg.is_priority)
                                else 0
                            ),
                            "paste_number": COA.paste_number(uld, point1, orientation),
                            "caving_degree": COA.caving_degree(
                                uld, point1, orientation
                            ),
                            "paste_ratio": COA.paste_ratio(uld, point1, orientation),
                            "z_gravity": -(point1.z + orientation.z) / 2,
                            "y_gravity": -(point1.y + orientation.y) / 2,
                            "x_gravity": -(point1.x + orientation.x) / 2,
                            "cost": pkg.cost**2 / pkg.volume(),
                        }
                        (
                            current_values["largest_dim"],
                            current_values["middle_dim"],
                            current_values["smallest_dim"],
                        ) = sorted([x_inc, y_inc, z_inc], reverse=True)

                        for param in priority_list:
                            if current_values[param] < values[param]:
                                break
                            if current_values[param] > values[param]:
                                values = current_values

                                best_coa = coa
                                best_pkg = pkg
                                best_orientation = orientation
                                best_uld = uld
                                break

        return best_coa, best_pkg, best_orientation, best_uld

    def solve(self, env: Environment):
        """
        https://www.sciencedirect.com/science/article/pii/S0305054807001785
        """
        random.seed(42)

        sorted_ULDs = sorted(env.ULDs, key=lambda uld: uld.volume(), reverse=True)
        priority_pkgs = [pkg for pkg in env.packages if pkg.is_priority]
        economy_pkgs = [pkg for pkg in env.packages if not pkg.is_priority]

        uld_COAs = {
            uld.id - 1: [
                Point(0, 0, 0),
                Point(uld.dim.l, 0, 0),
                Point(0, uld.dim.w, 0),
                Point(uld.dim.l, uld.dim.w, 0),
            ]
            for uld in sorted_ULDs
        }

        package_no = 0
        total_pkgs = len(priority_pkgs)

        priority_heurestic = [
            "priority_cost",
            "paste_number",
            "largest_dim",
            "middle_dim",
            "smallest_dim",
            "paste_ratio",
            "caving_degree",
            "z_gravity",
            "y_gravity",
            "x_gravity",
        ]

        while any(len(COA_freq) != 0 for COA_freq in uld_COAs.values()):
            best_coa, best_pkg, best_orientation, best_uld = COA.get_best_state(
                uld_COAs,
                priority_pkgs,
                env,
                allowed_ULDs=[2, 3, 4, 5],
                priority_list=priority_heurestic,
            )
            if best_coa is None:
                break

            if env.add_package(
                best_pkg, best_uld, corners=(best_coa, best_orientation)
            ):
                package_no += 1
                print(
                    f"Priority Package   ==>\t {package_no}/{total_pkgs}",
                    file=sys.stderr,
                )

            priority_pkgs.remove(best_pkg)
            uld_COAs[best_uld.id - 1].remove(best_coa)
            for corner_idx in (1, 2, 4):
                uld_COAs[best_uld.id - 1].append(best_pkg.get_corners()[corner_idx])

        print(f"{'='*60}", file=sys.stderr)
        package_no = 0
        total_pkgs = len(economy_pkgs)

        while any(len(COA_freq) != 0 for COA_freq in uld_COAs.values()):
            best_coa, best_pkg, best_orientation, best_uld = COA.get_best_state(
                uld_COAs, economy_pkgs, env, allowed_ULDs=None, priority_list=None
            )
            if best_coa is None:
                break

            if env.add_package(
                best_pkg, best_uld, corners=(best_coa, best_orientation)
            ):
                package_no += 1
                print(
                    f"Economy Package   ==>\t {package_no}/{total_pkgs}",
                    file=sys.stderr,
                )

            economy_pkgs.remove(best_pkg)
            uld_COAs[best_uld.id - 1].remove(best_coa)
            for corner_idx in (1, 2, 4):
                uld_COAs[best_uld.id - 1].append(best_pkg.get_corners()[corner_idx])
