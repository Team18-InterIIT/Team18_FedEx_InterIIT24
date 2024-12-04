import copy
import multiprocessing
import random
import sys
from itertools import permutations

import numpy as np
import skopt
import tqdm
from skopt import Optimizer
from skopt.space import Integer

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment


def objective(
    params,
    uld_COAs,
    env,
    pkgs,
    allowed_ULDs,
    verbose,
    maximize_volume_utilization,
    return_params=True,
):
    heuristic = {
        "included_cost": params[0],
        "caving_degree": params[1],
        "paste_number": params[2],
        "paste_ratio": params[3],
        "largest_dim": params[4],
        "middle_dim": params[5],
        "smallest_dim": params[6],
        "z_gravity": params[7],
        "y_gravity": params[8],
        "x_gravity": params[9],
    }

    uld_COAs_copy: dict[int, list] = copy.deepcopy(uld_COAs)
    env_copy: Environment = copy.deepcopy(env)
    pkgs_copy: list = copy.deepcopy(pkgs)

    cost = COA.A3(
        uld_COAs_copy,
        env_copy,
        pkgs_copy,
        heuristic=heuristic,
        allowed_ULDs=allowed_ULDs,
        verbose=verbose,
    )

    if maximize_volume_utilization is not None:
        volume_utilization = sum(
            uld.volume_utilisation() for uld in env_copy.ULDs
        ) / len(allowed_ULDs)
        cost += 1000 * (
            (1 - volume_utilization)
            if maximize_volume_utilization
            else (volume_utilization)
        )

        if verbose:
            print(f"Volume Utilization: {volume_utilization}")

    if verbose:
        print(f"Cost: {cost}")

    env_copy.global_stability_check()
    num_unstable = sum((1 if env_copy.stable[i] == -1 else 0) for i in env_copy.stable)

    if return_params:
        return params, (cost + 100 * num_unstable)
    else:
        return cost + 100 * num_unstable


class COA(PackingAlgorithm):
    """
    https://www.sciencedirect.com/science/article/pii/S0305054807001785
    """

    def paste_number(uld: ULD, point_min: Point, point_max: Point) -> int:
        """
        Paste number is the number of faces of the packing item that are pasted to the ULD.
        """
        paste_number_value = 0

        x1_min, y1_min, z1_min = point_min.x, point_min.y, point_min.z
        x1_max, y1_max, z1_max = point_max.x, point_max.y, point_max.z

        paste_number_value += (
            (x1_min == 0 or x1_max == uld.dim.l)
            + (y1_min == 0 or y1_max == uld.dim.w)
            + (z1_min == 0)
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
                    and min(y0_max, y1_max) - max(y0_min, y1_min) > 0
                    and min(z0_max, z1_max) - max(z0_min, z1_min) > 0
                )
                + (
                    x1_max == x0_min
                    and min(y0_max, y1_max) - max(y0_min, y1_min) > 0
                    and min(z0_max, z1_max) - max(z0_min, z1_min) > 0
                )
                + (
                    y1_min == y0_max
                    and min(x0_max, x1_max) - max(x0_min, x1_min) > 0
                    and min(z0_max, z1_max) - max(z0_min, z1_min) > 0
                )
                + (
                    y1_max == y0_min
                    and min(x0_max, x1_max) - max(x0_min, x1_min) > 0
                    and min(z0_max, z1_max) - max(z0_min, z1_min) > 0
                )
                + (
                    z1_min == z0_max
                    and min(x0_max, x1_max) - max(x0_min, x1_min) > 0
                    and min(y0_max, y1_max) - max(y0_min, y1_min) > 0
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
                and min(y0_max, y1_max) - max(y0_min, y1_min) > 0
                and min(z0_max, z1_max) - max(z0_min, z1_min) > 0
            ):
                paste_area += (min(y0_max, y1_max) - max(y0_min, y1_min)) * (
                    min(z0_max, z1_max) - max(z0_min, z1_min)
                )

            if (
                x1_max == x0_min
                and min(y0_max, y1_max) - max(y0_min, y1_min) > 0
                and min(z0_max, z1_max) - max(z0_min, z1_min) > 0
            ):
                paste_area += (min(y0_max, y1_max) - max(y0_min, y1_min)) * (
                    min(z0_max, z1_max) - max(z0_min, z1_min)
                )

            if (
                y1_min == y0_max
                and min(x0_max, x1_max) - max(x0_min, x1_min) > 0
                and min(z0_max, z1_max) - max(z0_min, z1_min) > 0
            ):
                paste_area += (min(x0_max, x1_max) - max(x0_min, x1_min)) * (
                    min(z0_max, z1_max) - max(z0_min, z1_min)
                )

            if (
                y1_max == y0_min
                and min(x0_max, x1_max) - max(x0_min, x1_min) > 0
                and min(z0_max, z1_max) - max(z0_min, z1_min) > 0
            ):
                paste_area += (min(x0_max, x1_max) - max(x0_min, x1_min)) * (
                    min(z0_max, z1_max) - max(z0_min, z1_min)
                )

            if (
                z1_min == z0_max
                and min(x0_max, x1_max) - max(x0_min, x1_min) > 0
                and min(y0_max, y1_max) - max(y0_min, y1_min) > 0
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
        pt1_min: Point, pt1_max: Point, pt2_min: Point, pt2_max: Point
    ) -> tuple[int, int, int]:
        x1_min, y1_min, z1_min = (pt1_min.x, pt1_min.y, pt1_min.z)
        x1_max, y1_max, z1_max = (pt1_max.x, pt1_max.y, pt1_max.z)

        x2_min, y2_min, z2_min = (pt2_min.x, pt2_min.y, pt2_min.z)
        x2_max, y2_max, z2_max = (pt2_max.x, pt2_max.y, pt2_max.z)

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

        x_min, y_min, z_min = point_min.x, point_min.y, point_min.z
        x_max, y_max, z_max = point_max.x, point_max.y, point_max.z

        neg_x, pos_x = x_min, uld.dim.l - x_max
        neg_y, pos_y = y_min, uld.dim.w - y_max
        neg_z, pos_z = z_min, uld.dim.h - z_max

        Dx = neg_x if pos_x == 0 else pos_x if neg_x == 0 else min(neg_x, pos_x)
        Dy = neg_y if pos_y == 0 else pos_y if neg_y == 0 else min(neg_y, pos_y)
        Dz = neg_z if pos_z == 0 else pos_z if neg_z == 0 else min(neg_z, pos_z)

        for existing_pkg in uld.packages:
            dx, dy, dz = COA.distance(
                existing_pkg.corners[0],
                existing_pkg.corners[1],
                point_min,
                point_max,
            )
            if dx != 0:
                Dx = min(Dx, dx)
            if dy != 0:
                Dy = min(Dy, dy)
            if dz != 0:
                Dz = min(Dz, dz)

        return min(Dx, Dy, Dz)

    def caving_degree(uld: ULD, point_min: Point, point_max: Point) -> float:
        x_min, y_min, z_min = point_min.x, point_min.y, point_min.z
        x_max, y_max, z_max = point_max.x, point_max.y, point_max.z
        volume = (x_max - x_min) * (y_max - y_min) * (z_max - z_min)

        return 1.0 - (
            COA.distance_coa(uld, point_min, point_max) / ((volume) ** (1 / 3))
        )

    def generate_COAs(point_min: Point, point_max: Point) -> list[Point]:
        x, y, z = point_min.x, point_min.y, point_min.z
        l, w, h = point_max.x - x, point_max.y - y, point_max.z - z

        return [
            Point(x + l, y, z),
            Point(x, y + w, z),
            Point(x, y, z + h),
        ]

    def A3(
        uld_COAs: dict[int, list[Point]],
        env: Environment,
        pkgs: list[Package],
        heuristic: dict[str, int] = None,
        allowed_ULDs: list[int] = None,
        verbose: bool = True,
        prune_COAs: bool = True,
        **kwargs,
    ):
        if heuristic is None:
            heuristic = {
                "included_cost": 5012633,
                "caving_degree": 10000,
                "paste_number": 4533,
                "paste_ratio": 5896,
                "largest_dim": 1000,
                "middle_dim": 529,
                "smallest_dim": 284,
                "z_gravity": -5000,
                "y_gravity": -335,
                "x_gravity": -100,
            }

        if allowed_ULDs is None:
            allowed_ULDs = list(range(len(env.ULDs)))

        total_pkgs = len(pkgs)

        if verbose:
            print(
                f"A3 on {total_pkgs} packages, allowed ULDs: {[uld_id + 1 for uld_id in allowed_ULDs]}"
            )

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
                                pkg.id,
                                uld.id,
                                corners=(coa, orientation),
                                simulate=True,
                                stability_check=False,
                            ):
                                continue

                            found_atleast_one_package = True

                            current_values = {
                                "included_cost": (
                                    (pkg.cost**1.5 / pkg.volume() ** 0.8)
                                    if not pkg.is_priority
                                    else -(
                                        sum(
                                            pkg.cost
                                            for pkg in env.packages
                                            if (not pkg.is_priority and pkg.uld_id == 0)
                                        )
                                        + sum(
                                            env.K
                                            for uld in env.ULDs
                                            if uld.has_priority
                                        )
                                        + env.K
                                        if (not uld.has_priority and pkg.is_priority)
                                        else 0
                                    )
                                ),
                                "caving_degree": COA.caving_degree(
                                    uld, coa, orientation
                                ),
                                "paste_number": COA.paste_number(uld, coa, orientation),
                                "paste_ratio": COA.paste_ratio(uld, coa, orientation),
                                "z_gravity": (coa.z + orientation.z) / 2,
                                "y_gravity": (coa.y + orientation.y) / 2,
                                "x_gravity": (coa.x + orientation.x) / 2,
                            }
                            (
                                current_values["largest_dim"],
                                current_values["middle_dim"],
                                current_values["smallest_dim"],
                            ) = sorted([x_inc, y_inc, z_inc], reverse=True)

                            current_value = sum(
                                weight * current_values[param]
                                for param, weight in heuristic.items()
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
                best_pkg.id,
                best_uld.id,
                corners=(best_coa, best_orientation),
                collision_check=False,
                weight_limit_check=False,
                stability_check=False,
                gravity=True,
            )

            pkgs.remove(best_pkg)
            uld_COAs[best_uld.id - 1].remove(best_coa)
            for new_coa in COA.generate_COAs(best_coa, best_orientation):
                uld_COAs[best_uld.id - 1].append(new_coa)

            if verbose:
                print(
                    f"\r {total_pkgs - len(pkgs)}/{total_pkgs} : Package added to ULD {best_uld.id}",
                    end="",
                )
                sys.stdout.flush()

        if verbose:
            print("")

        cost = sum(env.cost(priority_check=False))

        return cost

    def gp_minimize(
        objective,
        space,
        uld_COAs,
        env,
        pkgs,
        allowed_ULDs,
        verbose,
        maximize_volume_utilization,
        n_jobs=1,
        n_calls=10,
        random_state=42,
    ):
        optimizer = Optimizer(
            space, base_estimator="ET", random_state=random_state, n_initial_points=15
        )
        if n_jobs == -1:
            n_jobs = multiprocessing.cpu_count()
        cpu_state = {}
        n_completed_calls = 0
        with multiprocessing.Pool(processes=n_jobs) as pool:
            ready_ids = list(range(n_jobs))

            with tqdm.tqdm(total=n_calls, desc="Optimization Progress") as pbar:
                while n_completed_calls < n_calls:
                    if len(ready_ids) > 0:
                        n_updated = 0
                        for cpu_id in ready_ids:
                            if cpu_state.get(cpu_id) is not None:
                                # update optimzier with completed results
                                optimizer.tell(*cpu_state[cpu_id].get())
                                n_updated += 1
                                if pbar.n < n_calls:
                                    pbar.update(1)
                                cpu_state[cpu_id] = None
                        n_completed_calls += n_updated

                        # sample points for all idle CPUs
                        sampled_points = optimizer.ask(len(ready_ids))

                        # distribute tasks to idel CPUs
                        for point, cpu_id in zip(sampled_points, ready_ids):
                            cpu_state[cpu_id] = pool.apply_async(
                                objective,
                                args=(
                                    point,
                                    uld_COAs,
                                    env,
                                    pkgs,
                                    allowed_ULDs,
                                    verbose,
                                    maximize_volume_utilization,
                                    True,
                                ),
                            )

                        ready_ids = [
                            cpu_id
                            for cpu_id in cpu_state
                            if cpu_state[cpu_id] is not None
                            and cpu_state[cpu_id].ready()
                        ]
                    else:
                        ready_ids = [
                            cpu_id
                            for cpu_id in cpu_state
                            if cpu_state[cpu_id] is not None
                            and cpu_state[cpu_id].ready()
                        ]
        best_params = optimizer.Xi[np.argmin(optimizer.yi)]
        return best_params

    def Ai(
        uld_COAs: dict[int, list[Point]],
        env: Environment,
        pkgs: list[Package],
        allowed_ULDs: list[int] = None,
        prune_COAs: bool = True,
        verbose: bool = False,
        n_calls: int = 20,
        n_jobs: int = -1,
        multiprocessing: bool = True,
        maximize_volume_utilization: bool = True,
        **kwargs,
    ):
        if allowed_ULDs is None:
            allowed_ULDs = list(range(len(env.ULDs)))

        print(f"Allowed ULDs: {[uld_id + 1 for uld_id in allowed_ULDs]}")

        space = [
            Integer(100000, 10000000, name="included_cost"),
            Integer(1000, 10000, name="caving_degree"),
            Integer(500, 5000, name="paste_number"),
            Integer(1000, 10000, name="paste_ratio"),
            Integer(1000, 10000, name="largest_dim"),
            Integer(250, 2500, name="middle_dim"),
            Integer(100, 1000, name="smallest_dim"),
            Integer(-5000, -500, name="z_gravity"),
            Integer(-1000, -100, name="y_gravity"),
            Integer(-1000, -100, name="x_gravity"),
        ]

        if not multiprocessing:

            def objective_wrapper(params):
                return objective(
                    params,
                    uld_COAs,
                    env,
                    pkgs,
                    allowed_ULDs,
                    True,
                    maximize_volume_utilization,
                    return_params=False,
                )

            res = skopt.gp_minimize(
                objective_wrapper,
                space,
                n_calls=n_calls,
                n_jobs=n_jobs,
                random_state=42,
            )

            best_params = res.x
        else:
            best_params = COA.gp_minimize(
                objective,
                space,
                uld_COAs,
                env,
                pkgs,
                allowed_ULDs,
                verbose,
                maximize_volume_utilization,
                n_calls=n_calls,
                random_state=42,
                n_jobs=n_jobs,
            )

        best_heuristic = {
            "included_cost": best_params[0],
            "caving_degree": best_params[1],
            "paste_number": best_params[2],
            "paste_ratio": best_params[3],
            "largest_dim": best_params[4],
            "middle_dim": best_params[5],
            "smallest_dim": best_params[6],
            "z_gravity": best_params[7],
            "y_gravity": best_params[8],
            "x_gravity": best_params[9],
        }

        print(f"Best heuristic:\n{best_heuristic}\n\n", file=open("heuristic.log", "a"))

        COA.A3(
            uld_COAs,
            env,
            pkgs,
            heuristic=best_heuristic,
            prune_COAs=prune_COAs,
            allowed_ULDs=allowed_ULDs,
            verbose=verbose,
            maximize_volume_utilization=None,
        )

        return best_heuristic

    def solve(self, env: Environment):
        random.seed(42)

        sorted_ULD_ids = sorted(
            range(len(env.ULDs)),
            key=lambda uld_id: (
                env.ULDs[uld_id].volume(),
                env.ULDs[uld_id].weight_limit,
                uld_id,
            ),
            reverse=True,
        )
        priority_pkgs = [
            pkg for pkg in env.packages if pkg.is_priority and pkg.uld_id == 0
        ]
        economy_pkgs = [
            pkg for pkg in env.packages if not pkg.is_priority and pkg.uld_id == 0
        ]

        uld_COAs = {uld_id: [] for uld_id in range(len(env.ULDs))}
        for uld in env.ULDs:
            for pkg in uld.packages:
                for coa in COA.generate_COAs(pkg.corners[0], pkg.corners[1]):
                    if uld.id - 1 not in uld_COAs:
                        uld_COAs[uld.id - 1] = []
                    uld_COAs[uld.id - 1].append(coa)

        for uld_id in range(len(env.ULDs)):
            if len(uld_COAs[uld_id]) == 0:
                uld_COAs[uld_id] = [Point(0, 0, 0)]

        priority_heuristic = {
            "included_cost": 6019543,
            "caving_degree": 8533,
            "paste_number": 4706,
            "paste_ratio": 1852,
            "largest_dim": 3838,
            "middle_dim": 1350,
            "smallest_dim": 410,
            "z_gravity": -3607,
            "y_gravity": -178,
            "x_gravity": -649,
        }

        for uld_id in sorted_ULD_ids:
            print(f"ULD: {uld_id + 1}")
            COA.Ai(
                uld_COAs,
                env,
                priority_pkgs,
                allowed_ULDs=[uld_id],
                heuristic=priority_heuristic,
                prune_COAs=False,
                n_calls=10,
                multiprocessing=True,
                maximize_volume_utilization=True,
            )
            print(f"{'='*60}")

        print("")

        for uld_id in sorted_ULD_ids:
            print(f"ULD: {uld_id + 1}")
            COA.Ai(
                uld_COAs,
                env,
                economy_pkgs,
                allowed_ULDs=[uld_id],
                n_calls=10,
                multiprocessing=True,
                maximize_volume_utilization=True,
            )
            print(f"{'='*60}")
