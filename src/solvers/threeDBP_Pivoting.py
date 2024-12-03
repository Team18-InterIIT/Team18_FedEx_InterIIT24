import random
import sys
from itertools import permutations

import mlrose_ky as mlrose
import numpy as np

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment


class ThreeDBP_Pivoting_Simul_Annealing(PackingAlgorithm):
    def solve(self, env: Environment):
        """
        https://github.com/enzoruiz/3dbinpacking/blob/master/erick_dube_507-034.pdf
        https://scholar.uwindsor.ca/cgi/viewcontent.cgi?article=5986&context=etd
        """
        random.seed(42)

        def pivot_package(pkg: Package, uld: ULD, pivot: Point) -> bool:
            for l_inc, b_inc, h_inc in itertools.permutations(
                [pkg.dim.l, pkg.dim.w, pkg.dim.h]
            ):
                if env.add_package(
                    pkg,
                    uld,
                    corners=(
                        pivot,
                        Point(
                            pivot.x + l_inc,
                            pivot.y + b_inc,
                            pivot.z + h_inc,
                        ),
                    ),
                    stability_check=False,
                ):
                    return True

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

        priority_pkgs = sorted(
            [pkg for pkg in env.packages if pkg.is_priority],
            key=lambda pkg: pkg.volume(),
            reverse=True,
        )
        i = 1

        def priority_cost(state):
            nonlocal i
            env.reset()
            pkgs = [priority_pkgs[i] for i in state]

            for uld in sorted_ULDs:
                for pkg in pkgs:
                    pack_to_ULD(pkg, uld)

            cost = sum(env.cost(priority_check=False))
            print(f"Iteration {i}:    \t Cost: {cost}")
            i += 1
            return cost

        priority_fitness = mlrose.CustomFitness(priority_cost)

        # Inheriting the Problem object to overload functions
        class Priority_DiscreteOpt(mlrose.DiscreteOpt):
            def __init__(
                self,
                length,
                fitness_fn,
                maximize=True,
                max_val=2,
                crossover=None,
                mutator=None,
            ):
                super().__init__(
                    length, fitness_fn, maximize, max_val, crossover, mutator
                )

            def random_neighbor(self):
                idx1, idx2 = random.sample(range(self.length), 2)
                new_state = np.copy(self.state)
                new_state[idx1], new_state[idx2] = new_state[idx2], new_state[idx1]
                return new_state

        priority_problem = Priority_DiscreteOpt(
            length=len(priority_pkgs),
            fitness_fn=priority_fitness,
            maximize=False,
            max_val=len(priority_pkgs),
        )
        priority_schedule = mlrose.GeomDecay()
        init_state = np.array(list(range(len(priority_pkgs))))

        # Simulated Annealing

        # priority_state = mlrose.simulated_annealing(
        #     priority_problem,
        #     schedule=priority_schedule,
        #     max_attempts=20,
        #     max_iters=1000,
        #     init_state=init_state,
        #     random_state=None,
        # )

        #Hill climbing
        priority_state = mlrose.random_hill_climb(
            priority_problem,
            max_iters=20,
            init_state=init_state,
            random_state=None,
        )

        priority_pkgs = [priority_pkgs[i] for i in priority_state[0]]
        env.summary()
        economy_pkgs = sorted(
            [pkg for pkg in env.packages if not pkg.is_priority],
            key=lambda pkg: pkg.cost**2 / pkg.volume(),
            reverse=True,
        )
        i = 1

        def economy_cost(state):
            nonlocal i
            env.reset()
            pkgs = priority_pkgs + [economy_pkgs[i] for i in state]

            for uld in sorted_ULDs:
                for pkg in pkgs:
                    pack_to_ULD(pkg, uld)

            cost = sum(env.cost(priority_check=False))
            print(f"Iteration {i}:    \t Cost: {cost}")
            i += 1
            return cost

        economy_fitness = mlrose.CustomFitness(economy_cost)

        # Inheriting the Problem object to overload functions
        class Economy_DiscreteOpt(mlrose.DiscreteOpt):
            def __init__(
                self,
                length,
                fitness_fn,
                maximize=True,
                max_val=2,
                crossover=None,
                mutator=None,
                priority_bounds=None,
                economy_bounds=None,
            ):
                super().__init__(
                    length, fitness_fn, maximize, max_val, crossover, mutator
                )
                if priority_bounds is None:
                    priority_bounds = [0, length]
                if economy_bounds is None:
                    economy_bounds = [0, length]

                self.priority_bounds = priority_bounds
                self.economy_bounds = economy_bounds
                self.swap_state = False

            def random_neighbor(self):
                new_state = np.copy(self.state)
                if(self.swap_state):
                    self.swap_state = False
                    idx1, idx2 = random.sample(range(*self.priority_bounds), 2)
                    new_state[idx1], new_state[idx2] = new_state[idx2], new_state[idx1]
                    return new_state
                else:
                    idx1, idx2 = random.sample(range(*self.economy_bounds), 2)
                    new_state[idx1], new_state[idx2] = new_state[idx2], new_state[idx1]
                    self.swap_state = True
                    return new_state

        economy_problem = Economy_DiscreteOpt(
            length=len(economy_pkgs),
            fitness_fn=economy_fitness,
            maximize=False,
            max_val=len(economy_pkgs),
            priority_bounds=[0, len(priority_pkgs)],
            economy_bounds=[0, len(economy_pkgs)],
        )
        economy_schedule = mlrose.GeomDecay(init_temp=10000, decay=0.9)
        init_state = np.array(list(range(len(economy_pkgs))))

        economy_state = mlrose.simulated_annealing(
            economy_problem,
            schedule=economy_schedule,
            max_attempts=10,
            max_iters=1000,
            init_state=init_state,
            random_state=None,
        )

        #Hill climbing
        # economy_state = mlrose.random_hill_climb(
        #     economy_problem,
        #     max_attempts=20,
        #     max_iters=100,
        #     init_state=init_state,
        #     random_state=None,
        # )



        economy_pkgs = [economy_pkgs[i] for i in economy_state[0]]

        pkgs = priority_pkgs + economy_pkgs

        env.reset()
        for uld in sorted_ULDs:
            for pkg in pkgs:
                pack_to_ULD(pkg, uld)
