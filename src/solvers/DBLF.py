import parser
import itertools
import random
import sys
from entity import Package, ULD, Dim
from itertools import permutations

# # Initialize data
# K = parser.get_K()
# uld_list = parser.get_uld_list()
# pkg_list = parser.get_pkg_list()

# # Create ULD and Package objects
# containers_all = [ULD(row) for row in uld_list]
# packages_all_okay = [Package(row) for row in pkg_list]
# packages_priority_all = [Package(pkg) for pkg in pkg_list if pkg[5] == "Priority"]
# packages_economy_all = [Package(pkg) for pkg in pkg_list if pkg[5] != "Priority"]
from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment
import numpy as np

class dblf_solver(PackingAlgorithm):
    def solve(self, env: Environment):
        """
        https://github.com/enzoruiz/3dbinpacking/blob/master/erick_dube_507-034.pdf
        https://scholar.uwindsor.ca/cgi/viewcontent.cgi?article=5986&context=etd
        """
        random.seed(42)

        # def pivot_package(
        #     pkg: Package, uld: ULD, pivot: Point, signs: tuple[int, int, int]
        # ) -> bool:
        #     for l_inc, w_inc, h_inc in permutations((pkg.dim.l, pkg.dim.w, pkg.dim.h)):
        #         l_inc = signs[0] * l_inc
        #         w_inc = signs[1] * w_inc
        #         h_inc = signs[2] * h_inc
        #         corners = (
        #             Point(
        #                 *map(
        #                     min,
        #                     zip(
        #                         (pivot.x, pivot.y, pivot.z),
        #                         (pivot.x + l_inc, pivot.y + w_inc, pivot.z + h_inc),
        #                     ),
        #                 )
        #             ),
        #             Point(
        #                 *map(
        #                     max,
        #                     zip(
        #                         (pivot.x, pivot.y, pivot.z),
        #                         (pivot.x + l_inc, pivot.y + w_inc, pivot.z + h_inc),
        #                     ),
        #                 )
        #             ),
        #         )
        #         return env.add_package(pkg, uld, corners=corners)

        def pack_to_ULD(packages, ULDs):
            self.dblf_packing_algorithm(env, packages, ULDs)


        sorted_ULDs = sorted(env.ULDs, key=lambda uld: uld.volume(), reverse=True)

        # Simulated Annealing to change the order of packages and see if it improves the solution
        def simulated_annealing(
            pkgs,
            neighbor_mode="swap",
            bounds=None,
            num_iterations=1000,
            temp=10000,
            decay=0.9,
        ):
            if bounds is None:
                bounds = [0, len(pkgs)]

            env.reset()
            uld_list = sorted_ULDs
            best_state = pkgs[:]
            current_state = best_state[:]
            # for uld in uld_list:
            #     for pkg in current_state:
            pack_to_ULD(current_state, uld_list)
            best_cost = sum(env.cost(priority_check=True))
            current_cost = best_cost
            i = 0
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

                # for uld in uld_list:
                #     for pkg in new_state:
                pack_to_ULD(new_state, uld_list)
                new_cost = sum(env.cost(priority_check=True))
                if new_cost == float("inf"):
                    continue

                if new_cost <= best_cost:
                    best_cost = new_cost
                    best_state = new_state[:]
                    current_cost = new_cost
                    current_state = new_state[:]

                    if temp != 0:
                        delta = (current_cost - new_cost) / temp
                        p = np.exp(delta)
                        y = random.random()
                        if y < p:
                            current_cost = new_cost
                            current_state = new_state[:]

                print(
                    f"Iteration: {i}/{num_iterations}   \t Cost: {current_cost} \t Best Cost: {best_cost}",
                    file=sys.stderr,
                )

                temp *= decay
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
        priority_pkgs = simulated_annealing(priority_pkgs, num_iterations=10, temp=0)
        pkgs = priority_pkgs + economy_pkgs
        print(f"{"="*20}\nAnnealing for Economy Packages\n{"="*20}", file=sys.stderr)
        pkgs = simulated_annealing(
            pkgs,
            bounds=[len(priority_pkgs), len(pkgs)],
            num_iterations=1000,
        )
        print(f"{"="*60}\n", file=sys.stderr)

        env.reset()
        # for uld in sorted_ULDs:
        #     for pkg in pkgs:
        pack_to_ULD(pkgs, sorted_ULDs)
    
    def wrapper(self, env):
        self.dblf_packing_algorithm(env, env.packages,env.ULDs)
            

    def dblf_packing_algorithm(self, env, packages, ulds):
        # Initialize position sets for each ULD
        position_sets = {uld.id: [(0, 0, 0)] for uld in ulds}
        
        for package in packages:
            packed = False
            for uld in ulds:
                for position in position_sets[uld.id]:
                    # if can_place(package, position, uld):
                        # Pack the package
                    x, y, z = position
                    corners = (
                        Point(x, y, z),
                        Point(
                            x + package.dim.l,
                            y + package.dim.w,
                            z + package.dim.h,
                        ),
                    )
                    
                    if env.add_package(package, uld, corners=corners):
                        # Update the position set
                        position_sets[uld.id] = self.update_positions(
                            position_sets[uld.id], package, position, uld
                        )
                        packed = True
                        break
                if packed:
                    break
        # return ulds, packages


    def update_positions(position_set, package, position, uld):
        """Update the position set after placing a package."""
        x, y, z = position
        l, w, h = package.dim.l, package.dim.w, package.dim.h

        new_positions = [
            (x + l, y, z),  # Right
            (x, y + w, z),  # Forward
            (x, y, z + h),  # Upward
        ]

        # Keep positions inside the ULD boundaries
        return [
            pos
            for pos in position_set + new_positions
            if pos[0] < uld.dim.l and pos[1] < uld.dim.w and pos[2] < uld.dim.h
        ]
    
    # def can_place(package, position, uld):
    #     """Check if the package can be placed at the given position in the ULD."""
    #     x, y, z = position
    #     if (
    #         x + package.dim.l > uld.dim.l
    #         or y + package.dim.w > uld.dim.w
    #         or z + package.dim.h > uld.dim.h
    #     ):
    #         return False

    #     if uld.weight + package.weight > uld.weight_limit:
    #         return False

    #     for placed_pkg in uld.packages:
    #         if is_overlapping(
    #             package,
    #             (x, y, z, x + package.dim.l, y + package.dim.w, z + package.dim.h),
    #             placed_pkg.corners,
    #         ):
    #             return False

    #     return True


    # def is_overlapping(package, new_coords, existing_coords):
    #     """Check if the new package placement overlaps with an existing package."""
    #     nx1, ny1, nz1, nx2, ny2, nz2 = new_coords
    #     ex1, ey1, ez1, ex2, ey2, ez2 = existing_coords[0] + existing_coords[1]

    #     return not (
    #         nx2 <= ex1 or nx1 >= ex2 or ny2 <= ey1 or ny1 >= ey2 or nz2 <= ez1 or nz1 >= ez2
    #     )