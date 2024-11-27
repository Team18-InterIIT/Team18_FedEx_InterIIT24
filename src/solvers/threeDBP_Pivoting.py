import random
import sys
from itertools import permutations

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment
import numpy as np
import copy

class ThreeDBP_Pivoting_Simul_Annealing(PackingAlgorithm):
    def solve(self, env: Environment):
        """
        https://github.com/enzoruiz/3dbinpacking/blob/master/erick_dube_507-034.pdf
        https://scholar.uwindsor.ca/cgi/viewcontent.cgi?article=5986&context=etd
        """
        random.seed(42)

        def pivot_package(
            pkg: Package, uld: ULD, pivot: Point, signs: tuple[int, int, int]
        ) -> bool:
            for l_inc, w_inc, h_inc in permutations((pkg.dim.l, pkg.dim.w, pkg.dim.h)):
                l_inc = signs[0] * l_inc
                w_inc = signs[1] * w_inc
                h_inc = signs[2] * h_inc
                corners = (
                    Point(
                        *map(
                            min,
                            zip(
                                (pivot.x, pivot.y, pivot.z),
                                (pivot.x + l_inc, pivot.y + w_inc, pivot.z + h_inc),
                            ),
                        )
                    ),
                    Point(
                        *map(
                            max,
                            zip(
                                (pivot.x, pivot.y, pivot.z),
                                (pivot.x + l_inc, pivot.y + w_inc, pivot.z + h_inc),
                            ),
                        )
                    ),
                )
                return env.add_package(pkg, uld, corners=corners)

        def generate_pivots(existing_pkg):
            x, y, z = (
                existing_pkg.corners[0].x,
                existing_pkg.corners[0].y,
                existing_pkg.corners[0].z,
            )
            l, w, h = existing_pkg.dim.l, existing_pkg.dim.w, existing_pkg.dim.h
            return [
                (Point(x + l, y, z), (1, 1, 1)),
                (Point(x, y + w, z), (1, 1, 1)),
                (Point(x, y, z + h), (1, 1, 1)),
            ]

        def pack_to_ULD(pkg: Package, uld: ULD) -> bool:
            """
            Pack the package to the ULD
            """
            if pkg.uld_id != 0:
                return False

            if not uld.packages:
                return pivot_package(pkg, uld, Point(0, 0, 0), (1, 1, 1))

            for existing_pkg in uld.packages:
                for pivot, signs in generate_pivots(existing_pkg):
                    if pivot_package(pkg, uld, pivot, signs):
                        return True

            return False

        sorted_ULDs = sorted(env.ULDs, key=lambda uld: uld.volume(), reverse=True)

        # Simulated Annealing to change the order of packages and see if it improves the solution
        def simulated_annealing(
            pkgs,
            neighbor_mode="swap",
            bounds=None,
            num_iterations=1000,
        ):
            if bounds is None:
                bounds = [0, len(pkgs)]

            env.reset()
            uld_list = sorted_ULDs
            best_state = pkgs[:]
            for uld in uld_list:
                for pkg in best_state:
                    pack_to_ULD(pkg, uld)
            best_cost = sum(env.cost(priority_check=False))
            i = 0
            while i < num_iterations:
                env.reset()
                new_state = best_state[:]

                idx1, idx2 = random.sample(range(*bounds), 2)
                if neighbor_mode == "swap":
                    new_state[idx1], new_state[idx2] = (
                        new_state[idx2],
                        new_state[idx1],
                    )
                elif neighbor_mode == "reverse":
                    new_state[idx1:idx2] = new_state[idx1:idx2][::-1]

                for uld in uld_list:
                    for pkg in new_state:
                        pack_to_ULD(pkg, uld)
                new_cost = sum(env.cost(priority_check=False))
                if new_cost == float("inf"):
                    continue

                if new_cost < best_cost:
                    best_state = new_state[:]
                    best_cost = new_cost

                print(
                    f"Iteration: {i}/{num_iterations}   \t Cost: {best_cost}",
                    file=sys.stderr,
                )

                i += 1

            return best_state


        def simulated_annealing2(
            pkgs,
            neighbor_mode="swap",
            bounds=None,
            num_iterations=1000,
        ):
            if bounds is None:
                bounds = [0, len(pkgs)]

            env.reset()
            uld_list = sorted_ULDs
            best_state = pkgs[:]
            current_state = best_state[:]
            for uld in uld_list:
                for pkg in current_state:
                    pack_to_ULD(pkg, uld)
            best_cost = sum(env.cost(priority_check=False))
            current_cost = best_cost
            i = 0
            T = 8000
            alpha = 0.95
            while i < num_iterations:
                env.reset()
                new_state = current_state[:]
                idx1, idx2 = random.sample(range(*bounds), 2)
                bounds = [0, len(pkgs)]
                idx3, idx4 = random.sample(range(*bounds), 2) 

                if neighbor_mode == "swap":
                    new_state[idx1], new_state[idx2] = (
                        new_state[idx2],
                        new_state[idx1],
                    )
                    new_state[idx3], new_state[idx4] = (
                        new_state[idx4],
                        new_state[idx3],
                    )
                elif neighbor_mode == "reverse":
                    new_state[idx1:idx2] = new_state[idx1:idx2][::-1]

                for uld in uld_list:
                    for pkg in new_state:
                        pack_to_ULD(pkg, uld)
                new_cost = sum(env.cost(priority_check=False))
                if new_cost == float("inf"):
                    continue

                arg = (current_cost-new_cost)/T
                T*=alpha
             
                p = np.exp(arg)
                y = random.random()
                print(p,y)
                
                if new_cost <= best_cost:
                    best_state = new_state[:]
                    best_cost = new_cost
                    current_cost = new_cost
                    current_state = new_state[:]
                if new_cost <= current_cost or y<p:
                    current_cost = new_cost
                    current_state = new_state[:]


                print(
                    f"Iteration: {i}/{num_iterations}   \t Cost: {current_cost} \t Best Cost: {best_cost}",
                    file=sys.stderr,
                )

                i += 1

            return best_state
        priority_pkgs = sorted(
            [pkg for pkg in env.packages if pkg.is_priority],
            key=lambda pkg: pkg.volume(),
            reverse=True,
        )
        economy_pkgs = sorted(
            [pkg for pkg in env.packages if not pkg.is_priority],
            key=lambda pkg: pkg.cost**2 / pkg.volume(),
            reverse=True,
        )


        print(f"{"="*20}\nAnnealing for Priority Packages\n{"="*20}", file=sys.stderr)
        priority_pkgs = simulated_annealing(priority_pkgs, num_iterations=10)
        pkgs = priority_pkgs + economy_pkgs
        print(f"{"="*20}\nAnnealing for Economy Packages\n{"="*20}", file=sys.stderr)
        pkgs = simulated_annealing2(
            pkgs, bounds=[len(priority_pkgs), len(pkgs)]  ,num_iterations=1000
        )
        print(f"{"="*60}\n", file=sys.stderr)

        env.reset()
        for uld in sorted_ULDs:
            for pkg in pkgs:
                pack_to_ULD(pkg, uld)
