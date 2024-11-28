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

    def caving_degree(uld: ULD, point_min: Point, point_max: Point) -> float:
        x_min, y_min, z_min = point_min.x, point_min.y, point_min.z
        x_max, y_max, z_max = point_max.x, point_max.y, point_max.z
        volume = (x_max - x_min) * (y_max - y_min) * (z_max - z_min)
        return 1.0 - COA.distance_coa(uld, point_min, point_max) / ((volume) ** (1 / 3))

    dp = {}

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
        for uld in env.ULDs:
            COA.dp[uld.id] = {}

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
                "cost": float("-inf"),
                "priority_cost": float("-inf"),
            }

            coa = init_coa
            uld = init_uld

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

                    if (coa, orientation) in COA.dp[uld.id]:
                        current_values = COA.dp[uld.id][(coa, orientation)]
                    else:
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

                        COA.dp[uld.id][(coa, orientation)] = current_values

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

            env.add_package(best_pkg, uld, corners=(coa, best_orientation))
            pkgs.remove(best_pkg)
            uld_COAs[uld.id - 1].remove(coa)
            for corner_idx in (1, 2, 4):
                uld_COAs[uld.id - 1].append(best_pkg.get_corners()[corner_idx])

            first_pkg = copy.deepcopy(best_pkg)

        while any(len(COAs) != 0 for COAs in uld_COAs.values()):
            best_coa = None
            best_pkg = None
            best_orientation = None
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
                            orientation = Point(
                                coa.x + x_inc, coa.y + y_inc, coa.z + z_inc
                            )

                            if not env.add_package(
                                pkg, uld, corners=(point1, orientation), simulate=True
                            ):
                                continue

                            if (coa, orientation) in COA.dp[uld.id]:
                                current_values = COA.dp[uld.id][(coa, orientation)]
                            else:
                                current_values = {
                                    "priority_cost": -(
                                        env.running_cost + env.K
                                        if (not uld.has_priority and pkg.is_priority)
                                        else 0
                                    ),
                                    "paste_number": COA.paste_number(
                                        uld, point1, orientation
                                    ),
                                    "caving_degree": COA.caving_degree(
                                        uld, point1, orientation
                                    ),
                                    "paste_ratio": COA.paste_ratio(
                                        uld, point1, orientation
                                    ),
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

                                COA.dp[uld.id][(coa, orientation)] = current_values

                            for param in heurestic:
                                if current_values[param] < max_values[param]:
                                    break
                                if current_values[param] > max_values[param]:
                                    max_values = current_values

                                    best_coa = coa
                                    best_pkg = pkg
                                    best_orientation = orientation
                                    best_uld = uld
                                    break

            if best_coa is None:
                break

            env.add_package(best_pkg, best_uld, corners=(best_coa, best_orientation))
            pkgs.remove(best_pkg)
            uld_COAs[best_uld.id - 1].remove(best_coa)
            for corner_idx in (1, 2, 4):
                uld_COAs[best_uld.id - 1].append(best_pkg.get_corners()[corner_idx])

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

        pkg_no = 1
        total_pkgs = len(pkgs)

        while any(len(COAs) != 0 for COAs in uld_COAs.values()):
            min_cost = float("inf")
            min_uld, min_coa, best_pkg = None, None, None
            for uld_id, COAs in uld_COAs.items():
                if uld_id not in allowed_ULDs:
                    continue

                init_uld = copy.deepcopy(env.ULDs[uld_id])

                for coa in COAs:
                    init_coa = copy.deepcopy(coa)
                    new_uld_COAs = copy.deepcopy(uld_COAs)
                    new_env = env.copy()
                    new_pkgs = copy.deepcopy(pkgs)
                    cost, pkg = COA.A0(
                        new_uld_COAs,
                        new_env,
                        new_pkgs,
                        heurestic,
                        allowed_ULDs=[uld_id],
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
            env.packages[best_pkg.id - 1].copy_from(best_pkg)
            best_pkg = env.packages[best_pkg.id - 1]

            env.add_package(best_pkg, min_uld, corners=best_pkg.corners)
            pkgs.remove(best_pkg)
            uld_COAs[min_uld.id - 1].remove(min_coa)
            for corner_idx in (1, 2, 4):
                uld_COAs[min_uld.id - 1].append(best_pkg.get_corners()[corner_idx])

            if logging:
                print(
                    f"Package {pkg_no}/{total_pkgs}",
                    file=sys.stderr,
                )
            pkg_no += 1

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

        priority_heurestic = [
            # "priority_cost",
            "paste_number",
            "largest_dim",
            "z_gravity",
            "paste_ratio",
            "caving_degree",
            "y_gravity",
            "x_gravity",
            "middle_dim",
            "smallest_dim",
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
            "largest_dim",
            "z_gravity",
            "caving_degree",
            "paste_ratio",
            "middle_dim",
            "smallest_dim",
            "y_gravity",
            "x_gravity",
        ]

        for uld in sorted_ULDs:
            COA.A1(
                uld_COAs,
                env,
                economy_pkgs,
                economy_heurestic,
                allowed_ULDs=[uld.id - 1],
            )
