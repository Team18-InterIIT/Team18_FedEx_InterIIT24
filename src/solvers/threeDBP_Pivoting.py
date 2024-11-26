import math
import random
from itertools import permutations
import copy

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment

random.seed(42)

class ThreeDBP_Pivoting(PackingAlgorithm):
    def solve(self, env: Environment):
        """
        https://github.com/enzoruiz/3dbinpacking/blob/master/erick_dube_507-034.pdf
        """
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
        sorted_pkgs = sorted(
            env.packages, key=lambda pkg: pkg.cost**1.5 / pkg.volume(), reverse=True
        )

        for uld in sorted_ULDs:
            for pkg in sorted_pkgs:
                pack_to_ULD(pkg, uld)


class ThreeDBP_Pivoting_Simul_Annealing(PackingAlgorithm):
    def solve(self, env: Environment):
        """
        https://github.com/enzoruiz/3dbinpacking/blob/master/erick_dube_507-034.pdf
        https://scholar.uwindsor.ca/cgi/viewcontent.cgi?article=5986&context=etd
        """

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
            num_iterations=1000,
        ):
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

                idx1, idx2 = random.sample(range(len(new_state)), 2)
                new_state[idx1], new_state[idx2] = (
                    new_state[idx2],
                    new_state[idx1],
                )
                for uld in uld_list:
                    for pkg in new_state:
                        pack_to_ULD(pkg, uld)
                new_cost = sum(env.cost(priority_check=False))
                if new_cost == float("inf"):
                    continue

                if new_cost < best_cost:
                    best_state = new_state[:]
                    best_cost = new_cost

                print(f"Iteration: {i + 1}, Best Cost: {best_cost}")
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

        priority_pkgs = simulated_annealing(priority_pkgs, num_iterations=100)
        economy_pkgs = simulated_annealing(economy_pkgs, num_iterations=100)

        env.reset()
        pkgs = priority_pkgs + economy_pkgs

        for uld in sorted_ULDs:
            for pkg in pkgs:
                pack_to_ULD(pkg, uld)
