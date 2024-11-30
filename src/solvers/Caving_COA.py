import random
import sys
from itertools import permutations
import copy

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment

from skopt import gp_minimize
from skopt.space import Real, Integer
import torch.nn as nn
import torch

import numpy as np

torch.device("cuda" if torch.cuda.is_available() else "cpu")


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

    dp = {}

    def A3(
        uld_COAs: dict[int, list[Point]],
        env: Environment,
        pkgs: list[Package],
        heurestic: dict[str, int] = None,
        allowed_ULDs: list[int] = None,
        logging: bool = True,
        prune_COAs: bool = True,
        **kwargs,
    ):
        if heurestic is None:
            heurestic = {
                "included_cost": 7967464,
                "paste_number": 1835,
                "paste_ratio": 780,
                "largest_dim": 2985,
                "middle_dim": 223,
                "smallest_dim": 11,
                "z_gravity": -2704,
                "y_gravity": -666,
                "x_gravity": -214,
            }

        if allowed_ULDs is None:
            allowed_ULDs = list(range(len(env.ULDs)))

        total_pkgs = len(pkgs)

        if logging:
            print(f"Total packages: {total_pkgs}", file=sys.stderr)

        while any(len(uld_COAs[uld_id]) != 0 for uld_id in allowed_ULDs):
            best_coa = None
            best_pkg = None
            best_orientation = None
            best_uld = None

            max_value = float("-inf")

            for uld_id in allowed_ULDs:
                uld = env.ULDs[uld_id]
                COAs = uld_COAs[uld_id]

                if prune_COAs:
                    COAs_to_remove = []

                for coa in COAs:
                    if prune_COAs:
                        found_atleast_one_package = False

                    for pkg in pkgs:
                        for x_inc, y_inc, z_inc in permutations(
                            (pkg.dim.l, pkg.dim.w, pkg.dim.h)
                        ):
                            orientation = Point(
                                coa.x + x_inc, coa.y + y_inc, coa.z + z_inc
                            )

                            if not env.add_package(
                                pkg, uld, corners=(coa, orientation), simulate=True
                            ):
                                continue

                            found_atleast_one_package = True

                            current_values = {
                                "paste_number": COA.paste_number(uld, coa, orientation),
                                "paste_ratio": COA.paste_ratio(uld, coa, orientation),
                                "z_gravity": (coa.z + orientation.z) / 2,
                                "y_gravity": (coa.y + orientation.y) / 2,
                                "x_gravity": (coa.x + orientation.x) / 2,
                                "priority_cost": (
                                    sum(
                                        pkg.cost
                                        for pkg in env.packages
                                        if (not pkg.is_priority and pkg.uld_id == 0)
                                    )
                                    + sum(env.K for uld in env.ULDs if uld.has_priority)
                                    + env.K
                                    if (not uld.has_priority and pkg.is_priority)
                                    else 0
                                ),
                                "included_cost": (pkg.cost**1.5 / pkg.volume() ** 0.8),
                            }
                            (
                                current_values["largest_dim"],
                                current_values["middle_dim"],
                                current_values["smallest_dim"],
                            ) = sorted([x_inc, y_inc, z_inc], reverse=True)

                            current_value = sum(
                                weight * current_values[param]
                                for param, weight in heurestic.items()
                            )

                            if current_value > max_value:
                                max_value = current_value

                                best_coa = coa
                                best_pkg = pkg
                                best_orientation = orientation
                                best_uld = uld

                    if prune_COAs and not found_atleast_one_package:
                        COAs_to_remove.append(coa)

                if prune_COAs:
                    for coa in COAs_to_remove:
                        COAs.remove(coa)

            if best_coa is None:
                break

            env.add_package(
                best_pkg,
                best_uld,
                corners=(best_coa, best_orientation),
                collision_check=False,
                weight_limit_check=False,
            )

            pkgs.remove(best_pkg)
            uld_COAs[best_uld.id - 1].remove(best_coa)
            for corner_idx in (1, 2, 4):
                uld_COAs[best_uld.id - 1].append(best_pkg.get_corners()[corner_idx])

            if logging:
                print(
                    f"Package {total_pkgs - len(pkgs)}/{total_pkgs}",  # TODO: fix the denominator
                    file=sys.stderr,
                )

        return sum(env.cost(priority_check=False))

    def Ai(
        uld_COAs: dict[int, list[Point]],
        env: Environment,
        pkgs: list[Package],
        allowed_ULDs: list[int] = None,
        logging: bool = True,
        optimizer: str = "gp_minimize",
        n_calls: int = 20,
    ):
        def objective(params):
            heurestic = {
                "included_cost": params[0],
                "paste_number": params[1],
                "paste_ratio": params[2],
                "largest_dim": params[3],
                "middle_dim": params[4],
                "smallest_dim": params[5],
                "z_gravity": params[6],
                "y_gravity": params[7],
                "x_gravity": params[8],
            }

            uld_COAs_copy = copy.deepcopy(uld_COAs)
            env_copy = copy.deepcopy(env)
            pkgs_copy = copy.deepcopy(pkgs)

            cost = COA.A3(
                uld_COAs_copy, env_copy, pkgs_copy, heurestic, allowed_ULDs, logging
            )

            if logging:
                print(f"Cost: {cost}", file=sys.stderr)

            return cost

        best_heurestic = None

        if optimizer == "gp_minimize":
            space = [
                Integer(10000, 10000000, name="included_cost"),
                Integer(1, 10000, name="paste_number"),
                Integer(1, 1000, name="paste_ratio"),
                Integer(1, 5000, name="largest_dim"),
                Integer(1, 500, name="middle_dim"),
                Integer(1, 100, name="smallest_dim"),
                Integer(-5000, 0, name="z_gravity"),
                Integer(-1000, 0, name="y_gravity"),
                Integer(-250, 0, name="x_gravity"),
            ]

            res = gp_minimize(objective, space, n_calls=n_calls, random_state=42)

            best_params = res.x
            best_heurestic = {
                "included_cost": best_params[0],
                "paste_number": best_params[1],
                "paste_ratio": best_params[2],
                "largest_dim": best_params[3],
                "middle_dim": best_params[4],
                "smallest_dim": best_params[5],
                "z_gravity": best_params[6],
                "y_gravity": best_params[7],
                "x_gravity": best_params[8],
            }

        elif optimizer == "torch":

            class HeuresticTuner(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.params = nn.Parameter(
                        torch.tensor(
                            [7967464, 1835, 780, 2985, 223, 11, -2704, -666, -214],
                            dtype=torch.float,
                            requires_grad=True,
                        )
                    )

                def forward(self):
                    return self.params

            def torched_objective_function(params):
                heurestic = {
                    "included_cost": params[0],
                    "paste_number": params[1],
                    "paste_ratio": params[2],
                    "largest_dim": params[3],
                    "middle_dim": params[4],
                    "smallest_dim": params[5],
                    "z_gravity": params[6],
                    "y_gravity": params[7],
                    "x_gravity": params[8],
                }

                env_copy = copy.deepcopy(env)
                uld_COAs_copy = copy.deepcopy(uld_COAs)
                pkgs_copy = copy.deepcopy(pkgs)

                cost = COA.A3(
                    uld_COAs_copy, env_copy, pkgs_copy, heurestic, allowed_ULDs, logging
                )

                return torch.tensor(cost, dtype=torch.float, requires_grad=True)

            tuner = HeuresticTuner()
            optimizer = torch.optim.Adam(tuner.parameters(), lr=0.01)

            for epoch in range(n_calls):
                optimizer.zero_grad()
                loss = torched_objective_function(tuner())
                loss.backward()
                optimizer.step()
                if logging:
                    print(f"Epoch {epoch}: Cost: {loss.item()}", file=sys.stderr)

            best_params = tuner().detach().numpy()
            best_heurestic = {
                "included_cost": best_params[0],
                "paste_number": best_params[1],
                "paste_ratio": best_params[2],
                "largest_dim": best_params[3],
                "middle_dim": best_params[4],
                "smallest_dim": best_params[5],
                "z_gravity": best_params[6],
                "y_gravity": best_params[7],
                "x_gravity": best_params[8],
            }

            if logging:
                print(f"Cost: {loss.item()}", file=sys.stderr)

        print(f"Best heurestic:\n{best_heurestic}\n\n", file=open("heuristic.log", "a"))

        COA.A3(uld_COAs, env, pkgs, best_heurestic, allowed_ULDs, logging=logging)

        return best_heurestic

    def solve(self, env: Environment):
        """
        https://www.sciencedirect.com/science/article/pii/S0305054807001785
        """
        random.seed(42)

        sorted_ULDs = sorted(env.ULDs, key=lambda uld: uld.volume(), reverse=True)
        priority_pkgs = [pkg for pkg in env.packages if pkg.is_priority]
        economy_pkgs = [pkg for pkg in env.packages if not pkg.is_priority]

        uld_COAs = {uld.id - 1: [Point(0, 0, 0)] for uld in sorted_ULDs}

        priority_heurestic = {
            "priority_cost": 1000000,
            "paste_number": 100000,
            "paste_ratio": 1000,
            "largest_dim": 1000,
            "middle_dim": 100,
            "smallest_dim": 100,
            "z_gravity": -1000,
            "y_gravity": -100,
            "x_gravity": -100,
        }

        for uld in sorted_ULDs:
            COA.A3(
                uld_COAs,
                env,
                priority_pkgs,
                heurestic=priority_heurestic,
                allowed_ULDs=[uld.id - 1],
                prune_COAs=False,
            )

        print(f"{'='*60}", file=sys.stderr)

        for uld in sorted_ULDs:
            print(f"ULD {uld.id}", file=sys.stderr)
            COA.A3(
                uld_COAs,
                env,
                economy_pkgs,
                allowed_ULDs=[uld.id - 1],
                n_calls=20,
            )
            print(f"{'='*60}", file=sys.stderr)
