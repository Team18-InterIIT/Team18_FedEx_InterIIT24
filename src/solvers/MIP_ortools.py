from ortools.linear_solver import pywraplp
from algorithm_interface import PackingAlgorithm
from entity import Point
from typing import Dict, List
from itertools import permutations

class ORToolsBinPacking(PackingAlgorithm):
    def __init__(self, M=100000):
        self.M = M  # Big-M constant for constraints

    def create_variable_dict(
        self,
        solver: pywraplp.Solver,
        name: str,
        indices: List,
        is_binary: bool = False,
        is_continuous: bool = False,
    ) -> Dict:
        """Helper function to create variables with consistent naming"""
        variables = {}
        for idx in indices:
            if isinstance(idx, tuple):
                var_name = f"{name}_{'_'.join(str(i) for i in idx)}"
            else:
                var_name = f"{name}_{idx}"

            if is_binary:
                variables[idx] = solver.IntVar(0, 1, var_name)
            elif is_continuous:
                variables[idx] = solver.NumVar(0, solver.infinity(), var_name)

        return variables

    def solve(self, environment):
        """
        Solves the 3D bin-packing problem using OR-Tools MIP solver.
        Data is directly fetched from the `environment`.
        """
        n = len(environment.packages)  # Number of packages
        if not environment.ULDs:
            raise ValueError("No ULDs available in the environment")

        # Assuming a single ULD for simplicity
        container = environment.ULDs[0]
        W, H, D = container.dim.l, container.dim.w, container.dim.h

        # Extract package dimensions and values
        self.box_dimensions = [
            (pkg.dim.l, pkg.dim.w, pkg.dim.h) for pkg in environment.packages
        ]
        self.inf = 1e9
        self.box_values = [
            pkg.cost if pkg.cost != float("inf") else self.inf
            for pkg in environment.packages
        ]

        # Create solver
        solver = pywraplp.Solver.CreateSolver("SCIP")
        if not solver:
            raise ValueError("Could not create solver")

        # Create variable indices
        box_indices = [(i, o) for i in range(n) for o in range(6)]
        # Updated pair indices to include orientations for both boxes
        pair_indices = [
            ((i, oi), (j, oj)) for i in range(n) for oi in range(6)
            for j in range(n) for oj in range(6) if i != j
        ]

        # Create variables
        # Continuous variables for positions
        x = self.create_variable_dict(solver, "xi", box_indices, is_continuous=True)
        y = self.create_variable_dict(solver, "yi", box_indices, is_continuous=True)
        z = self.create_variable_dict(solver, "zi", box_indices, is_continuous=True)

        # Binary variables for relative positions
        rij = self.create_variable_dict(solver, "rij", pair_indices, is_binary=True)
        lij = self.create_variable_dict(solver, "lij", pair_indices, is_binary=True)
        bij = self.create_variable_dict(solver, "bij", pair_indices, is_binary=True)
        fij = self.create_variable_dict(solver, "fij", pair_indices, is_binary=True)
        uij = self.create_variable_dict(solver, "uij", pair_indices, is_binary=True)
        oij = self.create_variable_dict(solver, "oij", pair_indices, is_binary=True)

        # Box selection and auxiliary variables
        si = self.create_variable_dict(solver, "si", box_indices, is_binary=True)

        print("Variables initialised")
        # constraints

        # Iterate over boxes
        for i in range(n):
            # Get all permutations of dimensions for the current box
            k = -1
            for wi, hi, di in permutations(self.box_dimensions[i]):
                # wi, hi, di now represent one orientation of the box
                k += 1
                for j in range(n):
                    if i != j:
                        for l in range(6):
                            # In OR-Tools, we use == instead of += for adding constraints
                            solver.Add(
                                rij[(i, k), (j, l)]
                                + lij[(i, k), (j, l)]
                                + bij[(i, k), (j, l)]
                                + fij[(i, k), (j, l)]
                                + uij[(i, k), (j, l)]
                                + oij[(i, k), (j, l)]
                                == si[(i, k)] + si[(j, l)] - 1,
                                f"Non-overlap_relation_{i}_{j}",
                            )

                for j in range(n):
                    if i != j:
                        l = -1
                        for wj, hj, dj in permutations(self.box_dimensions[j]):
                            l += 1
                            solver.Add(
                                x[i, k] - x[j, l] + W * lij[(i, k), (j, l)] <= W - wi + self.M * (2 - si[(i, k)] - si[(j, l)]),
                            )
                            solver.Add(
                                x[j, l] - x[i, k] + W * rij[(i, k), (j, l)] <= W - wj + self.M * (2 - si[(i, k)] - si[(j, l)]),
                            )
                            solver.Add(
                                y[i, k] - y[j, l] + H * uij[(i, k), (j, l)] <= H - hi + self.M * (2 - si[(i, k)] - si[(j, l)]),
                            )
                            solver.Add(
                                y[j, l] - y[i, k] + H * fij[(i, k), (j, l)] <= H - hj + self.M * (2 - si[(i, k)] - si[(j, l)]),
                            )
                            solver.Add(
                                z[i, k] - z[j, l] + D * oij[(i, k), (j, l)] <= D - di + self.M * (2 - si[(i, k)] - si[(j, l)]),
                            )
                            solver.Add(
                                z[j, l] - z[i, k] + D * bij[(i, k), (j, l)] <= D - dj + self.M * (2 - si[(i, k)] - si[(j, l)]),
                            )
                        solver.Add(x[i, k] >= 0)
                        solver.Add(y[i, k] >= 0)
                        solver.Add(z[i, k] >= 0)
                        solver.Add(x[i, k] + wi <= W)
                        solver.Add(y[i, k] + hi <= H)
                        solver.Add(z[i, k] + di <= D)

        # Set 18: Binary constraints for rij,lij,bij,fij,uij
        for j in range(n):
            if i != j:
                for k in range(6):
                    for l in range(6):
                        for var, name in [
                            (rij[(i, k), (j, l)], "rij"),
                            (lij[(i, k), (j, l)], "lij"),
                            (bij[(i, k), (j, l)], "bij"),
                            (fij[(i, k), (j, l)], "fij"),
                            (uij[(i, k), (j, l)], "uij"),
                            (oij[(i, k), (j, l)], "oij"),
                        ]:
                            solver.Add(var >= 0, f"binary_{name}_lower_{i}_{j}")
                            solver.Add(var <= 1, f"binary_{name}_upper_{i}_{j}")
        
        for k in range(6):

            # Set 21: Binary constraints for si and Cs variables
            solver.Add(si[(i, k)] >= 0, f"binary_si_lower_{i}")
            solver.Add(si[(i, k)] <= 1, f"binary_si_upper_{i}")

            # Set 22: Non-negativity constraints for coordinates
            solver.Add(x[(i, k)] >= 0, f"nonnegative_x_{i}")
            solver.Add(y[(i, k)] >= 0, f"nonnegative_y_{i}")
            solver.Add(z[(i, k)] >= 0, f"nonnegative_z_{i}")
        
        solver.Add(sum(si[(i, k)] for k in range(6)) <= 1, f"single_box_{i}")

        print("All constraints added")
        print("Number of variables =", solver.NumVariables())
        print("Number of constraints =", solver.NumConstraints())

        solver.Maximize(sum(self.box_values[i] * si[(i, k)] for i in range(n) for k in range(6)))
        status = solver.Solve()
        if status == pywraplp.Solver.OPTIMAL:
            print("Solution:")
            print("Objective value =", solver.Objective().Value())
            for i in range(n):
                print(f"Box {i}: {si[i].solution_value()}")
                if si[i].solution_value() > 0.5:
                    pkg = environment.packages[i]
                    coords = (
                        Point(
                            x[i].solution_value(),
                            y[i].solution_value(),
                            z[i].solution_value(),
                        ),
                        Point(
                            x[i].solution_value() + self.box_dimensions[i][0],
                            y[i].solution_value() + self.box_dimensions[i][1],
                            z[i].solution_value() + self.box_dimensions[i][2],
                        ),
                    )
                    environment.add_package(pkg, container, coords)
                    print(f"Box {i} packed at {coords}")
            packed_value = sum(
                self.box_values[i] for i in range(n) if si[i].solution_value() > 0.5
            )
            used_volume = sum(
                self.box_dimensions[i][0]
                * self.box_dimensions[i][1]
                * self.box_dimensions[i][2]
                for i in range(n)
                if si[i].solution_value() > 0.5
            )
            total_volume = W * H * D
            print(f"Total packed value: {packed_value}")
            print(
                f"Used volume: {used_volume} / {total_volume} ({(used_volume / total_volume) * 100:.2f}%)"
            )
            print("--------------------")

        else:
            print("The problem does not have an optimal solution.")
