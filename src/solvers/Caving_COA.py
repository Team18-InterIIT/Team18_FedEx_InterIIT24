import random
import sys
from itertools import permutations
import copy

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment


class COA(PackingAlgorithm):
    def paste_number(uld: ULD, point_min: Point, point_max: Point) -> int:
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
                    and (y0_min <= y1_min < y0_max or y0_min < y1_max <= y0_max)
                    and (z0_min <= z1_min < z0_max or z0_min < z1_max <= z0_max)
                )
                + (
                    x1_max == x0_min
                    and (y0_min <= y1_min < y0_max or y0_min < y1_max <= y0_max)
                    and (z0_min <= z1_min < z0_max or z0_min < z1_max <= z0_max)
                )
                + (
                    y1_min == y0_max
                    and (x0_min <= x1_min < x0_max or x0_min < x1_max <= x0_max)
                    and (z0_min <= z1_min < z0_max or z0_min < z1_max <= z0_max)
                )
                + (
                    y1_max == y0_min
                    and (x0_min <= x1_min < x0_max or x0_min < x1_max <= x0_max)
                    and (z0_min <= z1_min < z0_max or z0_min < z1_max <= z0_max)
                )
                + (
                    z1_min == z0_max
                    and (x0_min <= x1_min < x0_max or x0_min < x1_max <= x0_max)
                    and (y0_min <= y1_min < y0_max or y0_min < y1_max <= y0_max)
                )
                + (
                    z1_max == z0_min
                    and (x0_min <= x1_min < x0_max or x0_min < x1_max <= x0_max)
                    and (y0_min <= y1_min < y0_max or y0_min < y1_max <= y0_max)
                )
            )

        return paste_number_value

    def paste_ratio(uld: ULD, point_min: Point, point_max: Point) -> float:
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
                and (y0_min <= y1_min < y0_max or y0_min < y1_max <= y0_max)
                and (z0_min <= z1_min < z0_max or z0_min < z1_max <= z0_max)
            ):
                paste_area += (min(y0_max, y1_max) - max(y0_min, y1_min)) * (
                    min(z0_max, z1_max) - max(z0_min, z1_min)
                )

            if (
                x1_max == x0_min
                and (y0_min <= y1_min < y0_max or y0_min < y1_max <= y0_max)
                and (z0_min <= z1_min < z0_max or z0_min < z1_max <= z0_max)
            ):
                paste_area += (min(y0_max, y1_max) - max(y0_min, y1_min)) * (
                    min(z0_max, z1_max) - max(z0_min, z1_min)
                )

            if (
                y1_min == y0_max
                and (x0_min <= x1_min < x0_max or x0_min < x1_max <= x0_max)
                and (z0_min <= z1_min < z0_max or z0_min < z1_max <= z0_max)
            ):
                paste_area += (min(x0_max, x1_max) - max(x0_min, x1_min)) * (
                    min(z0_max, z1_max) - max(z0_min, z1_min)
                )

            if (
                y1_max == y0_min
                and (x0_min <= x1_min < x0_max or x0_min < x1_max <= x0_max)
                and (z0_min <= z1_min < z0_max or z0_min < z1_max <= z0_max)
            ):
                paste_area += (min(x0_max, x1_max) - max(x0_min, x1_min)) * (
                    min(z0_max, z1_max) - max(z0_min, z1_min)
                )

            if (
                z1_min == z0_max
                and (x0_min <= x1_min < x0_max or x0_min < x1_max <= x0_max)
                and (y0_min <= y1_min < y0_max or y0_min < y1_max <= y0_max)
            ):
                paste_area += (min(x0_max, x1_max) - max(x0_min, x1_min)) * (
                    min(y0_max, y1_max) - max(y0_min, y1_min)
                )

            if (
                z1_max == z0_min
                and (x0_min <= x1_min < x0_max or x0_min < x1_max <= x0_max)
                and (y0_min <= y1_min < y0_max or y0_min < y1_max <= y0_max)
            ):
                paste_area += (min(x0_max, x1_max) - max(x0_min, x1_min)) * (
                    min(y0_max, y1_max) - max(y0_min, y1_min)
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

    def distance(
        pt1: Point, pt2: Point, pt3: Point, pt4: Point
    ) -> tuple[int, int, int]:
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

    def caving_degree(uld: ULD, point_min: Point, point_max: Point) -> float:
        x_min, y_min, z_min = point_min.x, point_min.y, point_min.z
        x_max, y_max, z_max = point_max.x, point_max.y, point_max.z
        volume = (x_max - x_min) * (y_max - y_min) * (z_max - z_min)
        return 1.0 - (
            COA.distance_coa(uld, point_min, point_max) / ((volume) ** (1 / 3))
        )

    def generate_COAs(point_min: Point, point_max: Point) -> list[tuple[Point, tuple]]:
        x, y, z = point_min.x, point_min.y, point_min.z
        l, w, h = point_max.x - x, point_max.y - y, point_max.z - z
        return [
            (Point(x + l, y, z), (1, 1, 1)),
            (Point(x, y + w, z), (1, 1, 1)),
            (Point(x, y, z + h), (1, 1, 1)),
            # (Point(x, y, z), (1, -1, -1)),
            # (Point(x, y, z), (-1, 1, -1)),
            # (Point(x + l, y, z), (-1, -1, 1)),
            # (Point(x, y + w, z), (-1, -1, 1)),
            # (Point(x + l, y + w, z), (1, -1, -1)),
            # (Point(x + l, y + w, z), (-1, 1, -1)),
            # (Point(x + l, y, z + h), (-1, 1, -1)),
            # (Point(x, y + w, z + h), (1, -1, -1)),
            # (Point(x + l, y + w, z + h), (-1, -1, 1)),
        ]

    def A0(
        uld_COAs: dict[int, list[Point]],
        env: Environment,
        pkgs: list[Package],
        heurestic: list[str] = None,
        allowed_ULDs: list[int] = None,
        init_coa: Point = None,
        init_uld: ULD = None,
        logging: bool = True,
    ):
        if heurestic is None:
            heurestic = [
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

        total_pkgs = len(pkgs)
        first_pkg = None

        if init_coa is not None and init_uld is not None:
            best_pkg = None
            best_orientation = None

            max_values = {
                "paste_number": -1,
                "z_gravity": float("-inf"),
                "caving_degree": -1,
                "paste_ratio": -1,
                "largest_dim": -1,
                "middle_dim": -1,
                "smallest_dim": -1,
                "y_gravity": float("-inf"),
                "x_gravity": float("-inf"),
                "cost": -1,
                "priority_cost": float("-inf"),
            }

            coa = init_coa
            uld = init_uld

            for pkg in pkgs:
                for x_inc, y_inc, z_inc in permutations(
                    (pkg.dim.l, pkg.dim.w, pkg.dim.h)
                ):
                    orientation = Point(coa.x + x_inc, coa.y + y_inc, coa.z + z_inc)

                    if not env.add_package(
                        pkg, uld, corners=(coa, orientation), simulate=True
                    ):
                        continue

                    current_values = {
                        "paste_number": COA.paste_number(uld, coa, orientation),
                        "caving_degree": COA.caving_degree(uld, coa, orientation),
                        "paste_ratio": COA.paste_ratio(uld, coa, orientation),
                        "z_gravity": -(coa.z + orientation.z) / 2,
                        "y_gravity": -(coa.y + orientation.y) / 2,
                        "x_gravity": -(coa.x + orientation.x) / 2,
                    }
                    (
                        current_values["largest_dim"],
                        current_values["middle_dim"],
                        current_values["smallest_dim"],
                    ) = sorted([x_inc, y_inc, z_inc], reverse=True)

                    current_values["priority_cost"] = -(
                        env.running_cost + env.K
                        if (not uld.has_priority and pkg.is_priority)
                        else 0
                    )

                    current_values["cost"] = pkg.cost**1.5 / pkg.volume() ** 0.8

                    for param in heurestic:
                        if current_values[param] < max_values[param]:
                            break
                        if current_values[param] > max_values[param]:
                            max_values = current_values

                            best_pkg = pkg
                            best_orientation = orientation
                            break

            if best_pkg is None:
                return float("inf"), None

            env.add_package(best_pkg.id, uld.id, corners=(coa, best_orientation))
            pkgs.remove(best_pkg)
            uld_COAs[uld.id - 1].remove(coa)
            for corner_idx in (1, 2, 4):
                uld_COAs[uld.id - 1].append(best_pkg.get_corners()[corner_idx])

            best_pkg.copy_from(env.packages[best_pkg.id - 1])
            first_pkg = copy.deepcopy(best_pkg)

        while any(len(uld_COAs[uld_id]) != 0 for uld_id in allowed_ULDs):
            best_coa = None
            best_quadrant = None
            best_pkg = None
            best_point_min = None
            best_point_max = None
            best_uld = None

            max_values = {
                "paste_number": -1,
                "z_gravity": float("-inf"),
                "caving_degree": -1,
                "paste_ratio": -1,
                "largest_dim": -1,
                "middle_dim": -1,
                "smallest_dim": -1,
                "y_gravity": float("-inf"),
                "x_gravity": float("-inf"),
                "cost": -1,
                "priority_cost": float("-inf"),
            }

            for uld_id, COAs in uld_COAs.items():
                if uld_id not in allowed_ULDs:
                    continue

                uld = env.ULDs[uld_id]
                for coa, quadrant in COAs:
                    for pkg in pkgs:
                        for x_inc, y_inc, z_inc in permutations(
                            (pkg.dim.l, pkg.dim.w, pkg.dim.h)
                        ):
                            x_inc *= quadrant[0]
                            y_inc *= quadrant[1]
                            z_inc *= quadrant[2]

                            x_min = min(coa.x, coa.x + x_inc)
                            y_min = min(coa.y, coa.y + y_inc)
                            z_min = min(coa.z, coa.z + z_inc)

                            x_max = max(coa.x, coa.x + x_inc)
                            y_max = max(coa.y, coa.y + y_inc)
                            z_max = max(coa.z, coa.z + z_inc)

                            point_min = Point(x_min, y_min, z_min)
                            point_max = Point(x_max, y_max, z_max)

                            if not env.add_package(
                                pkg, uld, corners=(point_min, point_max), simulate=True
                            ):
                                continue

                            current_values = {
                                "paste_number": COA.paste_number(
                                    uld, point_min, point_max
                                ),
                                "caving_degree": COA.caving_degree(
                                    uld, point_min, point_max
                                ),
                                "paste_ratio": COA.paste_ratio(
                                    uld, point_min, point_max
                                ),
                                "z_gravity": -(point_min.z + point_max.z) / 2,
                                "y_gravity": -(point_min.y + point_max.y) / 2,
                                "x_gravity": -(point_min.x + point_max.x) / 2,
                            }
                            (
                                current_values["largest_dim"],
                                current_values["middle_dim"],
                                current_values["smallest_dim"],
                            ) = sorted(
                                [abs(x_inc), abs(y_inc), abs(z_inc)], reverse=True
                            )

                            current_values["priority_cost"] = -(
                                env.running_cost + env.K
                                if (not uld.has_priority and pkg.is_priority)
                                else 0
                            )

                            current_values["cost"] = pkg.cost**1.5 / pkg.volume() ** 0.8

                            for param in heurestic:
                                if current_values[param] < max_values[param]:
                                    break
                                if current_values[param] > max_values[param]:
                                    max_values = current_values

                                    best_coa = coa
                                    best_quadrant = quadrant
                                    best_pkg = pkg
                                    best_point_min = point_min
                                    best_point_max = point_max
                                    best_uld = uld
                                    break

            if best_coa is None:
                break

            env.add_package(
                best_pkg, best_uld, corners=(best_point_min, best_point_max)
            )
            pkgs.remove(best_pkg)
            uld_COAs[best_uld.id - 1].remove((best_coa, best_quadrant))
            for new_coa, new_quadrant in COA.generate_COAs(
                best_point_min, best_point_max
            ):
                uld_COAs[best_uld.id - 1].append((new_coa, new_quadrant))

            if logging:
                print(
                    f"Package {total_pkgs - len(pkgs)}/{total_pkgs}",  # TODO: fix the denominator
                    file=sys.stderr,
                )

        return (env.running_cost, first_pkg)

    def A1(
        uld_COAs: dict[int, list[Point]],
        env: Environment,
        pkgs: list[Package],
        heurestic: list[str] = None,
        allowed_ULDs: list[int] = None,
        logging: bool = True,
    ):
        if heurestic is None:
            heurestic = [
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

        total_pkgs = len(pkgs)

        while any(len(uld_COAs[uld_id]) != 0 for uld_id in allowed_ULDs):
            min_cost = float("inf")
            min_uld, min_coa, best_pkg = None, None, None
            for uld_id, COAs in uld_COAs.items():
                if uld_id not in allowed_ULDs:
                    continue

                for coa in COAs:
                    init_coa = copy.deepcopy(coa)
                    init_uld = copy.deepcopy(env.ULDs[uld_id])
                    new_uld_COAs = copy.deepcopy(uld_COAs)
                    new_env = env.copy()
                    new_pkgs = copy.deepcopy(pkgs)
                    cost, pkg = COA.A0(
                        new_uld_COAs,
                        new_env,
                        new_pkgs,
                        heurestic,
                        allowed_ULDs=None,
                        init_coa=init_coa,
                        init_uld=init_uld,
                        logging=False,
                    )

                    if cost < min_cost:
                        min_cost = cost
                        min_uld = init_uld.copy()
                        min_coa = copy.deepcopy(init_coa)
                        best_pkg = copy.deepcopy(pkg)

            if best_pkg is None:
                break

            pkg_id = best_pkg.id
            uld_id = min_uld.id
            env.add_package(pkg_id, uld_id, corners=(min_coa, best_pkg.corners[1]))

            pkg = env.packages[pkg_id - 1]
            pkgs.remove(pkg)
            uld_COAs[uld_id - 1].remove(min_coa)
            for corner_idx in (1, 2, 4):
                uld_COAs[min_uld.id - 1].append(best_pkg.get_corners()[corner_idx])

            if logging:
                print(
                    f"Package {total_pkgs - len(pkgs)}/{total_pkgs}",  # TODO: fix the denominator
                    file=sys.stderr,
                )

    def solve(self, env: Environment):
        """
        https://www.sciencedirect.com/science/article/pii/S0305054807001785
        """
        random.seed(42)

        sorted_ULDs = sorted(
            env.ULDs, key=lambda uld: (uld.volume(), uld.id), reverse=True
        )
        priority_pkgs = [pkg for pkg in env.packages if pkg.is_priority]
        economy_pkgs = [pkg for pkg in env.packages if not pkg.is_priority]

        uld_COAs = {
            uld.id - 1: [
                (Point(0, 0, 0), (1, 1, 1)),
                # (Point(uld.dim.l, 0, 0), (-1, 1, 1)),
                # (Point(0, uld.dim.w, 0), (1, -1, 1)),
                # (Point(uld.dim.l, uld.dim.w, 0), (-1, -1, 1)),
            ]
            for uld in sorted_ULDs
        }

        priority_heurestic = [
            "priority_cost",
            "paste_number",
            "z_gravity",
            "largest_dim",
            "y_gravity",
            "x_gravity",
            "middle_dim",
            "smallest_dim",
            "paste_ratio",
            "caving_degree",
        ]

        for uld in sorted_ULDs:
            COA.A0(
                uld_COAs,
                env,
                priority_pkgs,
                priority_heurestic,
                allowed_ULDs=[uld.id - 1],
            )

        print(f"{'='*60}", file=sys.stderr)

        economy_heurestic = [
            "cost",
            "paste_number",
            "z_gravity",
            "largest_dim",
            "y_gravity",
            "paste_ratio",
            "caving_degree",
            "x_gravity",
            "middle_dim",
            "smallest_dim",
        ]

        for uld in sorted_ULDs:
            print(f"ULD {uld.id}", file=sys.stderr)
            COA.A0(
                uld_COAs,
                env,
                economy_pkgs,
                heurestic=economy_heurestic,
                allowed_ULDs=[uld.id - 1],
            )
        print(f"{'='*60}", file=sys.stderr)
