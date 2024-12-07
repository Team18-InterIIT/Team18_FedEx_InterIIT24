import random

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment
from layering import make_layers
from solvers.Caving_NAC import NAC
from solvers.layerpack import LayerPack


class Hybrid(PackingAlgorithm):
    def solve(
        self, env: Environment, n_calls=100, search="normal", layering: bool = True
    ):
        random.seed(42)

        if search in ("normal", "fast"):
            solver = NAC.A3
        elif search in ("hyper", "slow"):
            solver = NAC.A4
            layering = False

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

        if layering:
            print("Checking if layering is feasible...")
            # If it is not possible to make good layers, then the layering is turned off
            uld = env.ULDs[sorted_ULD_ids[-1]]
            priority_layers = make_layers(priority_pkgs, uld, rejection_threshold=0.95)
            economy_layers = make_layers(economy_pkgs, uld, rejection_threshold=0.95)
            if len(priority_layers) == 0 and len(economy_layers) == 0:
                print("Layering is not feasible. Turning off layering.")
                layering = False

        if layering:
            uld_heights = {uld_id: 0 for uld_id in range(len(env.ULDs))}

        uld_corners = {uld_id: [] for uld_id in range(len(env.ULDs))}
        for uld in env.ULDs:
            for pkg in uld.packages:
                for corner in NAC.generate_corners(pkg.corners[0], pkg.corners[1]):
                    if uld.id - 1 not in uld_corners:
                        uld_corners[uld.id - 1] = []
                    uld_corners[uld.id - 1].append(corner)

        for uld_id in range(len(env.ULDs)):
            if len(uld_corners[uld_id]) == 0:
                uld_corners[uld_id] = [Point(0, 0, 0)]

        print("Priority Packages:")
        for uld_id in sorted_ULD_ids:
            print(f"ULD: {uld_id + 1}")
            if layering:
                best_layer_heuristic = LayerPack.Ai_L(
                    uld_heights,
                    env,
                    priority_pkgs,
                    allowed_ULDs=[uld_id],
                    n_calls=n_calls,
                    n_jobs=-1,
                    verbose=False,
                    multiprocessing=True,
                    maximize_volume_utilization=True,
                    minimize_unstable=True,
                    family_cost=False,
                    simulate=True,
                )

                no_of_layers_added = LayerPack.A3_L(
                    uld_heights,
                    env,
                    priority_pkgs,
                    allowed_ULDs=[uld_id],
                    heuristic=best_layer_heuristic,
                    verbose=True,
                )

                if no_of_layers_added != 0:
                    for uld in env.ULDs:
                        for pkg in uld.packages:
                            for corner in NAC.generate_corners(
                                pkg.corners[0], pkg.corners[1]
                            ):
                                if uld.id - 1 not in uld_corners:
                                    uld_corners[uld.id - 1] = []
                                uld_corners[uld.id - 1].append(corner)

            best_heuristic = NAC.Ai(
                uld_corners,
                env,
                priority_pkgs,
                allowed_ULDs=[uld_id],
                prune_corners=False,
                n_calls=n_calls,
                multiprocessing=True,
                simulate=True,
                maximize_volume_utilization=True,
                minimize_unstable=True,
                family_cost=False,
            )
            solver(
                uld_corners,
                env,
                priority_pkgs,
                allowed_ULDs=[uld_id],
                prune_corners=False,
                heuristic=best_heuristic,
                maximize_volume_utilization=True,
                minimize_unstable=True,
                family_cost=False,
            )

            print(f"{'='*60}")

        print("\nEconomy Packages:")

        for uld_id in sorted_ULD_ids:
            print(f"ULD: {uld_id + 1}")
            if layering:
                best_layer_heuristic = LayerPack.Ai_L(
                    uld_heights,
                    env,
                    economy_pkgs,
                    allowed_ULDs=[uld_id],
                    n_calls=n_calls,
                    n_jobs=-1,
                    verbose=False,
                    multiprocessing=True,
                    maximize_volume_utilization=True,
                    minimize_unstable=True,
                    family_cost=False,
                    simulate=True,
                )

                no_of_layers_added = LayerPack.A3_L(
                    uld_heights,
                    env,
                    economy_pkgs,
                    allowed_ULDs=[uld_id],
                    heuristic=best_layer_heuristic,
                    verbose=True,
                )

                if no_of_layers_added != 0:
                    for uld in env.ULDs:
                        for pkg in uld.packages:
                            for corner in NAC.generate_corners(
                                pkg.corners[0], pkg.corners[1]
                            ):
                                if uld.id - 1 not in uld_corners:
                                    uld_corners[uld.id - 1] = []
                                uld_corners[uld.id - 1].append(corner)

            best_heuristic = NAC.Ai(
                uld_corners,
                env,
                economy_pkgs,
                allowed_ULDs=[uld_id],
                prune_corners=True,
                n_calls=n_calls,
                multiprocessing=True,
                simulate=True,
                maximize_volume_utilization=True,
                minimize_unstable=True,
                family_cost=False,
            )
            solver(
                uld_corners,
                env,
                economy_pkgs,
                allowed_ULDs=[uld_id],
                prune_corners=True,
                heuristic=best_heuristic,
                maximize_volume_utilization=True,
                minimize_unstable=True,
                family_cost=False,
            )
            print(f"{'='*60}")
