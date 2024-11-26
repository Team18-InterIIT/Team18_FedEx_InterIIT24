from ortools.linear_solver import pywraplp
from algorithm_interface import PackingAlgorithm
from entity import Point
from typing import Dict, List


class ORToolsBinPacking(PackingAlgorithm):
    def __init__(self, M=10000):
        self.M = M  # Big-M constant for constraints
        self.set1 = True
        self.set2 = False
        self.set3 = True

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
        box_indices = range(n)
        pair_indices = [(i, j) for i in range(n) for j in range(n) if i != j]

        # Create variables
        # Continuous variables for positions
        x = self.create_variable_dict(solver, "x", box_indices, is_continuous=True)
        y = self.create_variable_dict(solver, "y", box_indices, is_continuous=True)
        z = self.create_variable_dict(solver, "z", box_indices, is_continuous=True)

        # Binary variables for orientation
        Xwi = self.create_variable_dict(solver, "Xwi", box_indices, is_binary=True)
        Zwi = self.create_variable_dict(solver, "Zwi", box_indices, is_binary=True)
        Yhi = self.create_variable_dict(solver, "Yhi", box_indices, is_binary=True)
        Zdi = self.create_variable_dict(solver, "Zdi", box_indices, is_binary=True)

        # Binary variables for relative positions
        rij = self.create_variable_dict(solver, "rij", pair_indices, is_binary=True)
        lij = self.create_variable_dict(solver, "lij", pair_indices, is_binary=True)
        bij = self.create_variable_dict(solver, "bij", pair_indices, is_binary=True)
        fij = self.create_variable_dict(solver, "fij", pair_indices, is_binary=True)
        uij = self.create_variable_dict(solver, "uij", pair_indices, is_binary=True)
        oij = self.create_variable_dict(solver, "oij", pair_indices, is_binary=True)

        # Binary variables for support constraints
        yaij = self.create_variable_dict(solver, "yaij", pair_indices, is_binary=True)
        xaij = self.create_variable_dict(solver, "xaij", pair_indices, is_binary=True)
        ybij = self.create_variable_dict(solver, "ybij", pair_indices, is_binary=True)
        xbij = self.create_variable_dict(solver, "xbij", pair_indices, is_binary=True)
        ycij = self.create_variable_dict(solver, "ycij", pair_indices, is_binary=True)
        xc = self.create_variable_dict(solver, "xcij", pair_indices, is_binary=True)
        yd = self.create_variable_dict(solver, "ydij", pair_indices, is_binary=True)
        xd = self.create_variable_dict(solver, "xdij", pair_indices, is_binary=True)

        # Additional support variables
        za = self.create_variable_dict(solver, "zaij", pair_indices, is_binary=True)
        zb = self.create_variable_dict(solver, "zbij", pair_indices, is_binary=True)
        zc = self.create_variable_dict(solver, "zcij", pair_indices, is_binary=True)
        zd = self.create_variable_dict(solver, "zdij", pair_indices, is_binary=True)

        # Support constraint variables
        Cs1 = self.create_variable_dict(solver, "Cs1", pair_indices, is_binary=True)
        Cs2 = self.create_variable_dict(solver, "Cs2", pair_indices, is_binary=True)
        Cs3 = self.create_variable_dict(solver, "Cs3", pair_indices, is_binary=True)
        Cs4 = self.create_variable_dict(solver, "Cs4", pair_indices, is_binary=True)

        # Box selection and auxiliary variables
        si = self.create_variable_dict(solver, "si", box_indices, is_binary=True)
        x_prime = self.create_variable_dict(
            solver, "x_prime", box_indices, is_continuous=True
        )
        z_prime = self.create_variable_dict(
            solver, "z_prime", box_indices, is_continuous=True
        )

        print("Variables initialised")
        # constraints
        if self.set1:
            for i in range(n):
                wi, hi, di = self.box_dimensions[i]

                for j in range(n):
                    if i != j:
                        # In OR-Tools, we use == instead of += for adding constraints
                        solver.Add(
                            rij[(i, j)]
                            + lij[(i, j)]
                            + bij[(i, j)]
                            + fij[(i, j)]
                            + uij[(i, j)]
                            + oij[(i, j)]
                            == si[i] + si[j] - 1,
                            f"Non-overlap_relation_{i}_{j}",
                        )
                for j in range(n):
                    if i != j:
                        wj, hj, dj = self.box_dimensions[j]
                        solver.Add(
                            x[i] - x[j] + W * lij[(i, j)] <= W - wi,
                        )
                        solver.Add(
                            x[j] - x[i] + W * rij[(i, j)] <= W - wj,
                        )
                        solver.Add(
                            y[i] - y[j] + H * uij[(i, j)] <= H - hi,
                        )
                        solver.Add(
                            y[j] - y[i] + H * oij[(i, j)] <= H - hj,
                        )
                        solver.Add(
                            z[i] - z[j] + D * bij[(i, j)] <= D - di,
                        )
                        solver.Add(
                            z[j] - z[i] + D * fij[(i, j)] <= D - dj,
                        )
                solver.Add(x[i] >= 0)
                solver.Add(y[i] >= 0)
                solver.Add(z[i] >= 0)
                solver.Add(x[i] + wi <= W)
                solver.Add(y[i] + hi <= H)
                solver.Add(z[i] + di <= D)

                # Set 2: Non-Overlapping Constraints
                for j in range(n):
                    if i != j:
                        wi, hi, di = self.box_dimensions[i]
                        wj, hj, dj = self.box_dimensions[j]

                        # (2a) Left placement in x-coordinate
                        solver.Add(
                            x[i]
                            + wi * Xwi[i]
                            + hi * (Zwi[i] - Yhi[i] + Zdi[i])
                            + di * (1 - Xwi[i] - Zwi[i] + Yhi[i] - Zdi[i])
                            <= x[j] + self.M * (1 - lij[(i, j)]),
                            f"x_overlap_left_{i}_{j}",
                        )

                        # (2b) Right placement in x-coordinate
                        solver.Add(
                            x[j]
                            + wj * Xwi[j]
                            + hj * (Zwi[j] - Yhi[j] + Zdi[j])
                            + dj * (1 - Xwi[j] - Zwi[j] + Yhi[j] - Zdi[j])
                            <= x[i] + self.M * (1 - rij[(i, j)]),
                            f"x_overlap_right_{i}_{j}",
                        )

                        # (2c) Below placement in z-coordinate
                        solver.Add(
                            z[i]
                            + di * Zdi[i]
                            + hi * (1 - Zwi[i] - Zdi[i])
                            + wi * Zwi[i]
                            <= z[j] + self.M * (1 - bij[(i, j)]),
                            f"z_overlap_below_{i}_{j}",
                        )

                        # (2d) Above placement in z-coordinate
                        solver.Add(
                            z[j]
                            + dj * Zdi[j]
                            + hj * (1 - Zwi[j] - Zdi[j])
                            + wj * Zwi[j]
                            <= z[i] + self.M * (1 - fij[(i, j)]),
                            f"z_overlap_above_{i}_{j}",
                        )

                        # (2e) Behind placement in y-coordinate
                        solver.Add(
                            y[i]
                            + hi * Yhi[i]
                            + wi * (1 - Xwi[i] - Zwi[i])
                            + di * (Xwi[i] + Zwi[i] - Yhi[i])
                            <= y[j] + self.M * (1 - uij[(i, j)]),
                            f"y_overlap_behind_{i}_{j}",
                        )

                        # (2f) In-front placement in y-coordinate
                        solver.Add(
                            y[j]
                            + hj * Yhi[j]
                            + wj * (1 - Xwi[j] - Zwi[j])
                            + dj * (Xwi[j] + Zwi[j] - Yhi[j])
                            <= y[i] + self.M * (1 - oij[(i, j)]),
                            f"y_overlap_infront_{i}_{j}",
                        )

                # Set 3: Placing Boxes Within Bin Dimensions
                # (3a) Box dimensions fit within width
                solver.Add(
                    x[i]
                    + wi * Xwi[i]
                    + hi * (Zwi[i] - Yhi[i] + Zdi[i])
                    + di * (1 - Xwi[i] - Zwi[i] + Yhi[i] - Zdi[i])
                    <= W,
                    f"box_within_width_{i}",
                )

                # (3b) Box dimensions fit within height
                solver.Add(
                    y[i]
                    + hi * Yhi[i]
                    + wi * (1 - Xwi[i] - Zwi[i])
                    + di * (Xwi[i] + Zwi[i] - Yhi[i])
                    <= H,
                    f"box_within_height_{i}",
                )

                # (3c) Box dimensions fit within depth
                solver.Add(
                    z[i] + di * Zdi[i] + hi * (1 - Zwi[i] - Zdi[i]) + wi * Zwi[i] <= D,
                    f"box_within_depth_{i}",
                )

                # Set 4: Orientation Constraints
                # (4a) Width not parallel to both X and Z axes
                solver.Add(Xwi[i] + Zwi[i] <= 1, f"orientation_width_XZ_{i}")

                # (4b) Width and depth not both parallel to Z axis
                solver.Add(Zwi[i] + Zdi[i] <= 1, f"orientation_width_depth_Z_{i}")

                # (4c) Height not parallel to both Z and Y axes
                solver.Add(
                    Zwi[i] - Yhi[i] + Zdi[i] >= 0, f"orientation_height_ZY_lb_{i}"
                )
                solver.Add(
                    Zwi[i] - Yhi[i] + Zdi[i] <= 1, f"orientation_height_ZY_ub_{i}"
                )

                # (4d) Width, height, and depth not parallel to two axes
                solver.Add(
                    1 - Xwi[i] - Zwi[i] + Yhi[i] - Zdi[i] >= 0,
                    f"orientation_width_height_depth_lb_{i}",
                )
                solver.Add(
                    1 - Xwi[i] - Zwi[i] + Yhi[i] - Zdi[i] <= 1,
                    f"orientation_width_height_depth_ub_{i}",
                )

                # (4e) Further orientation control
                solver.Add(Xwi[i] + Zwi[i] - Yhi[i] >= 0, f"orientation_control_lb_{i}")
                solver.Add(Xwi[i] + Zwi[i] - Yhi[i] <= 1, f"orientation_control_ub_{i}")

            if self.set2:
                # Sets 7-9: Stability Constraints
                for j in range(n):
                    if i != j:
                        # Set 7: zaij Definition
                        # (7a)
                        solver.Add(
                            x[j] - x[i] <= self.M * yaij[(i, j)],
                            f"stability_7a_yaij_{i}_{j}",
                        )
                        solver.Add(
                            x[j] - x[i] >= self.M * (yaij[(i, j)] - 1),
                            f"stability_7a_yaij_rev_{i}_{j}",
                        )

                        # (7b)
                        solver.Add(
                            x[i] + 0.5 - x[j] <= self.M * xaij[(i, j)],
                            f"stability_7b_xaij_{i}_{j}",
                        )
                        solver.Add(
                            x[i] + 0.5 - x[j] >= self.M * (xaij[(i, j)] - 1),
                            f"stability_7b_xaij_rev_{i}_{j}",
                        )

                        # (7c)
                        solver.Add(
                            (yaij[(i, j)] + xaij[(i, j)] - 1) / 2 <= za[(i, j)],
                            f"stability_7c_zaij_lb_{i}_{j}",
                        )
                        solver.Add(
                            za[(i, j)] <= (yaij[(i, j)] + xaij[(i, j)]) / 2,
                            f"stability_7c_zaij_ub_{i}_{j}",
                        )

                        # Set 8: zbij Definition
                        # (8a)
                        solver.Add(
                            z[j] - z[i] <= self.M * ybij[(i, j)],
                            f"stability_8a_ybij_{i}_{j}",
                        )
                        solver.Add(
                            z[j] - z[i] >= self.M * (ybij[(i, j)] - 1),
                            f"stability_8a_ybij_rev_{i}_{j}",
                        )

                        # (8b)
                        solver.Add(
                            z[i] + 0.5 - z[j] <= self.M * xbij[(i, j)],
                            f"stability_8b_xbij_{i}_{j}",
                        )
                        solver.Add(
                            z[i] + 0.5 - z[j] >= self.M * (xbij[(i, j)] - 1),
                            f"stability_8b_xbij_rev_{i}_{j}",
                        )

                        # (8c)
                        solver.Add(
                            (ybij[(i, j)] + xbij[(i, j)] - 1) / 2 <= zb[(i, j)],
                            f"stability_8c_zbij_lb_{i}_{j}",
                        )
                        solver.Add(
                            zb[(i, j)] <= (ybij[(i, j)] + xbij[(i, j)]) / 2,
                            f"stability_8c_zbij_ub_{i}_{j}",
                        )

                        # Set 9: zcij Definition
                        # (9a)
                        solver.Add(
                            x_prime[j] - x[i] <= self.M * ycij[(i, j)],
                            f"stability_9a_ycij_{i}_{j}",
                        )
                        solver.Add(
                            x_prime[j] - x[i] >= self.M * (ycij[(i, j)] - 1),
                            f"stability_9a_ycij_rev_{i}_{j}",
                        )

                        # (9b)
                        solver.Add(
                            x_prime[i] - x_prime[j] <= self.M * xc[(i, j)],
                            f"stability_9b_xcij_{i}_{j}",
                        )
                        solver.Add(
                            x_prime[i] - x_prime[j] >= self.M * (xc[(i, j)] - 1),
                            f"stability_9b_xcij_rev_{i}_{j}",
                        )

                        # (9c)
                        solver.Add(
                            (ycij[(i, j)] + xc[(i, j)] - 1) / 2 <= zc[(i, j)],
                            f"stability_9c_zcij_lb_{i}_{j}",
                        )
                        solver.Add(
                            zc[(i, j)] <= (ycij[(i, j)] + xc[(i, j)]) / 2,
                            f"stability_9c_zcij_ub_{i}_{j}",
                        )
                # Set 10: zdij Definition (Based on z'-Coordinate)
                for j in range(n):
                    if i != j:
                        # (10a)
                        solver.Add(
                            z_prime[j] - z[i] <= self.M * yd[(i, j)],
                            f"stability_10a_ydij_{i}_{j}",
                        )
                        solver.Add(
                            z_prime[j] - z[i] >= self.M * (yd[(i, j)] - 1),
                            f"stability_10a_ydij_rev_{i}_{j}",
                        )

                        # (10b)
                        solver.Add(
                            z_prime[i] - z_prime[j] <= self.M * xd[(i, j)],
                            f"stability_10b_xdij_{i}_{j}",
                        )
                        solver.Add(
                            z_prime[i] - z_prime[j] >= self.M * (xd[(i, j)] - 1),
                            f"stability_10b_xdij_rev_{i}_{j}",
                        )

                        # (10c)
                        solver.Add(
                            (yd[(i, j)] + xd[(i, j)] - 1) / 2 <= zd[(i, j)],
                            f"stability_10c_zdij_lb_{i}_{j}",
                        )
                        solver.Add(
                            zd[(i, j)] <= (yd[(i, j)] + xd[(i, j)]) / 2,
                            f"stability_10c_zdij_ub_{i}_{j}",
                        )
                # Set 11-14: Cs1,Cs2,Cs3,Cs4 Coordinate Equality
                for j in range(n):
                    if i != j:
                        # (11)
                        solver.Add(
                            (za[(i, j)] + zb[(i, j)] - 1) / 2 <= Cs1[(i, j)],
                            f"coordinate_equality_11_lower_{i}_{j}",
                        )
                        solver.Add(
                            Cs1[(i, j)] <= (za[(i, j)] + zb[(i, j)]) / 2,
                            f"coordinate_equality_11_upper_{i}_{j}",
                        )

                        # (12)
                        solver.Add(
                            (za[(i, j)] + zd[(i, j)] - 1) / 2 <= Cs2[(i, j)],
                            f"coordinate_equality_12_lower_{i}_{j}",
                        )
                        solver.Add(
                            Cs2[(i, j)] <= (za[(i, j)] + zd[(i, j)]) / 2,
                            f"coordinate_equality_12_upper_{i}_{j}",
                        )

                        # (13)
                        solver.Add(
                            (zc[(i, j)] + zb[(i, j)] - 1) / 2 <= Cs3[(i, j)],
                            f"coordinate_equality_13_lower_{i}_{j}",
                        )
                        solver.Add(
                            Cs3[(i, j)] <= (zc[(i, j)] + zb[(i, j)]) / 2,
                            f"coordinate_equality_13_upper_{i}_{j}",
                        )

                        # (14)
                        solver.Add(
                            (zc[(i, j)] + zd[(i, j)] - 1) / 2 <= Cs4[(i, j)],
                            f"coordinate_equality_14_lower_{i}_{j}",
                        )
                        solver.Add(
                            Cs4[(i, j)] <= (zc[(i, j)] + zd[(i, j)]) / 2,
                            f"coordinate_equality_14_upper_{i}_{j}",
                        )

                # Set 15: Sum of Cs1,Cs2,Cs3,Cs4 Equals uij+oij
                for j in range(n):
                    if i != j:
                        solver.Add(
                            Cs1[(i, j)] + Cs2[(i, j)] + Cs3[(i, j)] + Cs4[(i, j)]
                            == uij[(i, j)] + oij[(i, j)],
                            f"sum_coordinates_15_{i}_{j}",
                        )

                # Set 16–17: Definitions of xi′ and zi′
                # (16) Definition of x'_i
                solver.Add(
                    x_prime[i]
                    == x[i]
                    + wi * Xwi[i]
                    + hi * (Zwi[i] - Yhi[i] + Zdi[i])
                    + di * (1 - Xwi[i] - Zwi[i] + Yhi[i] - Zdi[i]),
                    f"define_x_prime_16_{i}",
                )

                # (17) Definition of z'_i
                solver.Add(
                    z_prime[i]
                    == z[i] + di * Zdi[i] + hi * (1 - Zwi[i] - Zdi[i]) + wi * Zwi[i],
                    f"define_z_prime_17_{i}",
                )
            if self.set3:
                # Set 18: Binary constraints for rij,lij,bij,fij,uij
                for j in range(n):
                    if i != j:
                        for var, name in [
                            (rij[(i, j)], "rij"),
                            (lij[(i, j)], "lij"),
                            (bij[(i, j)], "bij"),
                            (fij[(i, j)], "fij"),
                            (uij[(i, j)], "uij"),
                        ]:
                            solver.Add(var >= 0, f"binary_{name}_lower_{i}_{j}")
                            solver.Add(var <= 1, f"binary_{name}_upper_{i}_{j}")

                # Set 19: Binary constraints for Xwi,Zwi,Zdi,Yhi
                for var, name in [
                    (Xwi[i], "Xwi"),
                    (Zwi[i], "Zwi"),
                    (Zdi[i], "Zdi"),
                    (Yhi[i], "Yhi"),
                ]:
                    solver.Add(var >= 0, f"binary_{name}_lower_{i}")
                    solver.Add(var <= 1, f"binary_{name}_upper_{i}")

                # Set 20: Binary constraints for stability variables
                for j in range(n):
                    if i != j:
                        for var, name in [
                            (xaij[(i, j)], "xaij"),
                            (xbij[(i, j)], "xbij"),
                            (xc[(i, j)], "xcij"),
                            (xd[(i, j)], "xdij"),
                            (yaij[(i, j)], "yaij"),
                            (ybij[(i, j)], "ybij"),
                            (ycij[(i, j)], "ycij"),
                            (yd[(i, j)], "ydij"),
                            (za[(i, j)], "zaij"),
                            (zb[(i, j)], "zbij"),
                            (zc[(i, j)], "zcij"),
                            (zd[(i, j)], "zdij"),
                        ]:
                            solver.Add(var >= 0, f"binary_{name}_lower_{i}_{j}")
                            solver.Add(var <= 1, f"binary_{name}_upper_{i}_{j}")

                # Set 21: Binary constraints for si and Cs variables
                solver.Add(si[i] >= 0, f"binary_si_lower_{i}")
                solver.Add(si[i] <= 1, f"binary_si_upper_{i}")

                for j in range(n):
                    if i != j:
                        for var, name in [
                            (Cs1[(i, j)], "Cs1"),
                            (Cs2[(i, j)], "Cs2"),
                            (Cs3[(i, j)], "Cs3"),
                            (Cs4[(i, j)], "Cs4"),
                        ]:
                            solver.Add(var >= 0, f"binary_{name}_lower_{i}_{j}")
                            solver.Add(var <= 1, f"binary_{name}_upper_{i}_{j}")

                # Set 22: Non-negativity constraints for coordinates
                solver.Add(x[i] >= 0, f"nonnegative_x_{i}")
                solver.Add(y[i] >= 0, f"nonnegative_y_{i}")
                solver.Add(z[i] >= 0, f"nonnegative_z_{i}")

        print("All constraints added")
        print("Number of variables =", solver.NumVariables())
        print("Number of constraints =", solver.NumConstraints())

        solver.Maximize(sum(self.box_values[i] * si[i] for i in range(n)))
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
