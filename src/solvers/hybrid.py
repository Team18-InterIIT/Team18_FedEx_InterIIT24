import random

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment
from solvers.Caving_COA import COA
from solvers.layerpack import LayerPack


class Hybrid(PackingAlgorithm):
    def solve(self, env: Environment, search="normal", layering: bool = False):
        random.seed(42)

        if search in ("normal", "fast"):
            solver = COA.A3
        elif search in ("hyper", "slow"):
            solver = COA.A4

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

        print("Priority Packages:")
        for uld_id in sorted_ULD_ids:
            print(f"ULD: {uld_id + 1}")
            if layering:
                best_layer_heuristic = LayerPack.Ai_L(
                    env,
                    priority_pkgs,
                    allowed_ULDs=[uld_id],
                    n_calls=10,
                    n_jobs=-1,
                    verbose=True,
                    multiprocessing=True,
                    maximize_volume_utilization=True,
                    minimize_untable=True,
                    family_cost=False,
                    simulate=True,
                )

                LayerPack.A3_L(
                    env,
                    priority_pkgs,
                    allowed_ULDs=[uld_id],
                    heuristic=best_layer_heuristic,
                    verbose=True,
                )

                for uld in env.ULDs:
                    for pkg in uld.packages:
                        for coa in COA.generate_COAs(pkg.corners[0], pkg.corners[1]):
                            if uld.id - 1 not in uld_COAs:
                                uld_COAs[uld.id - 1] = []
                            uld_COAs[uld.id - 1].append(coa)

            best_heuristic = COA.Ai(
                uld_COAs,
                env,
                priority_pkgs,
                allowed_ULDs=[uld_id],
                prune_COAs=False,
                n_calls=10,
                multiprocessing=True,
                simulate=True,
            )
            solver(
                uld_COAs,
                env,
                priority_pkgs,
                allowed_ULDs=[uld_id],
                prune_COAs=False,
                heuristic=best_heuristic,
            )

            print(f"{'='*60}")

        print("\nEconomy Packages:")

        for uld_id in sorted_ULD_ids:
            print(f"ULD: {uld_id + 1}")
            if layering:
                best_layer_heuristic = LayerPack.Ai_L(
                    env,
                    economy_pkgs,
                    allowed_ULDs=[uld_id],
                    n_calls=10,
                    n_jobs=-1,
                    verbose=False,
                    multiprocessing=True,
                    maximize_volume_utilization=True,
                    minimize_untable=True,
                    family_cost=False,
                    simulate=True,
                )

                LayerPack.A3_L(
                    env,
                    priority_pkgs,
                    allowed_ULDs=[uld_id],
                    heuristic=best_layer_heuristic,
                    verbose=True,
                )

                for uld in env.ULDs:
                    for pkg in uld.packages:
                        for coa in COA.generate_COAs(pkg.corners[0], pkg.corners[1]):
                            if uld.id - 1 not in uld_COAs:
                                uld_COAs[uld.id - 1] = []
                            uld_COAs[uld.id - 1].append(coa)

            best_heuristic = COA.Ai(
                uld_COAs,
                env,
                economy_pkgs,
                allowed_ULDs=[uld_id],
                prune_COAs=True,
                n_calls=10,
                multiprocessing=True,
                simulate=True,
            )
            solver(
                uld_COAs,
                env,
                economy_pkgs,
                allowed_ULDs=[uld_id],
                prune_COAs=True,
                heuristic=best_heuristic,
            )
            print(f"{'='*60}")
