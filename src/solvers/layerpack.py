import copy
import multiprocessing
import random
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import skopt
from skopt import Optimizer
from skopt.space import Integer, Real
from tqdm import tqdm

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment
from family_cost import centroidFamilyCost, graphFamilyCost
from layering import add_layer, make_layers


def objective(
    params,
    uld_heights,
    env,
    pkgs,
    allowed_ULDs,
    verbose,
    maximize_volume_utilization,
    minimize_unstable,
    family_cost,
) -> tuple[list[int], float]:
    heuristic = {
        "no_of_layers": params[0],
        "layer_cost": params[1],
        "layer_height": params[2],
        "layer_efficiency": params[3],
        "efficiency_threshold": params[4],
        "weight_threshold": params[5],
    }

    uld_heights_copy = copy.deepcopy(uld_heights)
    env_copy: Environment = copy.deepcopy(env)
    pkgs_copy: list = copy.deepcopy(pkgs)

    LayerPack.A3_L(
        uld_heights_copy,
        env_copy,
        pkgs_copy,
        heuristic=heuristic,
        allowed_ULDs=allowed_ULDs,
        verbose=False,
    )
    cost = sum(env_copy.cost(priority_check=False))

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

    if minimize_unstable:
        env_copy.global_stability_check()
        num_unstable = sum((1 if val == -1 else 0) for val in env_copy.stable.values())
        stability_cost = num_unstable * 100
        cost += stability_cost

    if family_cost:
        fam_cost = 0
        for uld_id in allowed_ULDs:
            uld = env_copy.ULDs[uld_id]
            fam_cost += graphFamilyCost(uld, env_copy.family_dict)
        fam_cost *= 50
        cost += fam_cost

    if verbose:
        print(f"Cost: {cost}")

    return params, cost


class LayerPack(PackingAlgorithm):
    def A3_L(
        uld_heights: dict[int, int],
        env: Environment,
        pkgs: list[Package],
        heuristic: dict[str, int] = None,
        allowed_ULDs: list[int] = None,
        verbose: bool = True,
        **kwargs,
    ):
        if heuristic is None:
            heuristic = {
                "no_of_layers": 0,
                "layer_cost": 10000,
                "layer_height": -10000,
                "layer_efficiency": 10000,
                "efficiency_threshold": 0.95,
                "weight_threshold": 0.3,
            }

        no_of_layers = heuristic.pop("no_of_layers")
        efficiency_threshold = heuristic.pop("efficiency_threshold")
        weight_threshold = heuristic.pop("weight_threshold")

        if allowed_ULDs is None:
            allowed_ULDs = list(range(len(env.ULDs)))

        total_pkgs = len(pkgs)

        if verbose:
            print(
                f"A3_L on {total_pkgs} packages, allowed ULDs: {[uld_id + 1 for uld_id in allowed_ULDs]}"
            )

        no_of_layers_added = 0

        for _ in range(no_of_layers):
            best_layer = None
            best_uld = None

            max_value = float("-inf")
            for uld_id in allowed_ULDs:
                uld = env.ULDs[uld_id]

                layers = make_layers(
                    pkgs,
                    uld,
                    rejection_threshold=efficiency_threshold,
                    weight_ratio_threshold=weight_threshold,
                )

                if verbose:
                    print(f"Found {len(layers)} layers for ULD {uld_id + 1}")

                for layer in layers:
                    if not add_layer(env, layer, z_coordinate=0, simulate=True):
                        continue

                    current_values = {
                        "layer_cost": layer.cost,
                        "layer_height": layer.dim.h,
                        "layer_efficiency": layer.packing_eff,
                    }

                    current_value = sum(
                        weight * current_values[param]
                        for param, weight in heuristic.items()
                        if param in current_values
                    )

                    if current_value > max_value:
                        max_value = current_value
                        best_layer = layer
                        best_uld = uld

            if best_layer is None:
                break

            if add_layer(env, best_layer, z_coordinate=uld_heights[best_uld.id - 1]):
                uld_heights[best_uld.id - 1] += best_layer.dim.h
                no_of_layers_added += 1

            rect_ids = [rect.id for rect in best_layer.rects]
            pkgs[:] = [pkg for pkg in pkgs if pkg.id not in rect_ids]

            if verbose:
                print(
                    f"\r Layer added to ULD {best_uld.id} with height {best_layer.dim.h}   \t",
                    end="",
                )
                sys.stdout.flush()

        if verbose:
            print("")

        cost = sum(env.cost(priority_check=False))

        return cost, no_of_layers_added

    def gp_minimize(
        objective,
        space,
        env,
        pkgs,
        allowed_ULDs,
        verbose,
        maximize_volume_utilization,
        minimize_unstable,
        family_cost,
        n_jobs=1,
        n_calls=10,
        random_state=42,
    ):
        optimizer = Optimizer(
            space, base_estimator="ET", random_state=random_state, n_initial_points=15
        )
        if n_jobs == -1:
            n_jobs = multiprocessing.cpu_count()
        n_completed_calls = 0
        args = (
            env,
            pkgs,
            allowed_ULDs,
            verbose,
            maximize_volume_utilization,
            minimize_unstable,
            family_cost,
        )

        # scaling n_calls to the next multiple of n_jobs
        n_calls = ((n_jobs + n_calls - 1) // n_jobs) * n_jobs

        progress_bar = tqdm(total=n_calls, desc="Tuning", postfix="Best Cost: inf")
        best_cost = float("inf")

        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            while n_completed_calls < n_calls:
                sampled_points = optimizer.ask(n_jobs)
                futures = [
                    executor.submit(objective, point, *args) for point in sampled_points
                ]
                for future in as_completed(futures):
                    result = future.result()
                    optimizer.tell(*result)
                    progress_bar.update(1)

                    current_cost = result[1]
                    if current_cost < best_cost:
                        best_cost = current_cost
                        progress_bar.set_postfix_str(f"Best Cost: {best_cost:.4f}")

                n_completed_calls += n_jobs

        best_params = optimizer.Xi[np.argmin(optimizer.yi)]
        return best_params

    def Ai_L(
        uld_heights: dict[int, int],
        env: Environment,
        pkgs: list[Package],
        allowed_ULDs: list[int] = None,
        verbose: bool = True,
        n_calls: int = 20,
        n_jobs: int = -1,
        multiprocessing: bool = True,
        maximize_volume_utilization: bool = True,
        minimize_unstable: bool = True,
        family_cost: bool = False,
        simulate: bool = False,
        **kwargs,
    ):
        if allowed_ULDs is None:
            allowed_ULDs = list(range(len(env.ULDs)))

        if not env.families:
            family_cost = False

        print(f"Allowed ULDs: {[uld_id + 1 for uld_id in allowed_ULDs]}")

        space = [
            Integer(0, 1, name="no_of_layers"),
            Integer(1000, 10000, name="layer_cost"),
            Integer(-10000, -1000, name="layer_height"),
            Integer(10000, 100000, name="layer_efficiency"),
            Real(0.95, 1, name="efficiency_threshold"),
            Real(0, 0.3, name="weight_threshold"),
        ]

        if not multiprocessing:

            def objective_wrapper(params):
                return objective(
                    params,
                    uld_heights,
                    env,
                    pkgs,
                    allowed_ULDs,
                    False,
                    maximize_volume_utilization,
                    minimize_unstable,
                    family_cost,
                )[1]

            res = skopt.gp_minimize(
                objective_wrapper,
                space,
                n_calls=n_calls,
                n_jobs=n_jobs,
                random_state=42,
            )

            best_params = res.x
        else:
            best_params = LayerPack.gp_minimize(
                objective,
                space,
                uld_heights,
                env,
                pkgs,
                allowed_ULDs,
                False,
                maximize_volume_utilization,
                minimize_unstable,
                family_cost,
                n_calls=n_calls,
                random_state=42,
                n_jobs=n_jobs,
            )

        best_heuristic = {
            "no_of_layers": best_params[0],
            "layer_cost": best_params[1],
            "layer_height": best_params[2],
            "layer_efficiency": best_params[3],
            "efficiency_threshold": best_params[4],
            "weight_threshold": best_params[5],
        }

        print(f"Best heuristic:\n{best_heuristic}\n\n", file=open("heuristic.log", "a"))

        if not simulate:
            LayerPack.A3_L(
                uld_heights,
                env,
                pkgs,
                heuristic=best_heuristic,
                allowed_ULDs=allowed_ULDs,
                verbose=verbose,
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

        uld_heights = {uld_id: 0 for uld_id in range(len(env.ULDs))}

        for uld_id in sorted_ULD_ids:
            print(f"ULD: {uld_id + 1}")
            best_params = LayerPack.Ai_L(
                env,
                priority_pkgs,
                allowed_ULDs=[uld_id],
                n_calls=10,
                multiprocessing=True,
                simulate=True,
            )

            LayerPack.A3_L(
                uld_heights,
                env,
                priority_pkgs,
                allowed_ULDs=[uld_id],
                heuristic=best_params,
            )
            print(f"{'='*60}")

        print("")

        for uld_id in sorted_ULD_ids:
            print(f"ULD: {uld_id + 1}")
            best_params = LayerPack.Ai_L(
                env,
                economy_pkgs,
                allowed_ULDs=[uld_id],
                n_calls=10,
                multiprocessing=True,
                simulate=True,
            )

            LayerPack.A3_L(
                uld_heights,
                env,
                economy_pkgs,
                allowed_ULDs=[uld_id],
                heuristic=best_params,
            )
            print(f"{'='*60}")
