import csv
import collections
from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point,Package,Dim
import rectpack as rp

from algorithm_interface import PackingAlgorithm


class LayerPacking(PackingAlgorithm):

    # class layer:
    #     def __init__(self):
    #         self.packages: list[Package] = list()
    #         self.height = 0
    #         self.uldno = 0
    #         self.cost = 0
    #     def __repr__(self):
    #         return f"Layer: {self.packages} Height: {self.height} ULD: {self.uldno} Cost: {self.cost}"
        
    #     def add_package(self, pkg: Package):
    #         self.packages.append(pkg)
    #         self.cost += pkg.cost


    def solve(self, env: Environment):
        # ULDs = {
        #     1: {"dimensions": (224, 318, 162), "weight_limit": 2500},
        #     2: {"dimensions": (224, 318, 162), "weight_limit": 2500},
        #     3: {"dimensions": (244, 318, 244), "weight_limit": 2800},
        #     4: {"dimensions": (244, 318, 244), "weight_limit": 2800},
        #     5: {"dimensions": (244, 318, 285), "weight_limit": 3500},
        #     6: {"dimensions": (244, 318, 285), "weight_limit": 3500},
        # }
        ULDs = env.ULDs
        class Layer:
            def __init__(self, pe, packed_list, length, breadth, height, uldno, cost):
                self.packing_eff = pe
                self.packedrects : list[Rect] = []
                self.dim : Dim = Dim(length,breadth,height)
                self.uldno = uldno
                self.cost = cost if cost != float("inf") else 1e9

            def add_rect(self, rect):
                self.packedrects.append(rect)
                self.cost += rect.cost if rect.cost != float("inf") else 1e9

        class Rect:
            def __init__(self, id, cost, x=0, y=0, w=0, h=0):
                self.id = id
                self.cost = cost
                self.x = 0  # x-coordinate of the rectangle's top-left corner
                self.y = 0  # y-coordinate of the rectangle's top-left corner
                self.w = w  # width of the rectangle
                self.h = h  # height of the rectangle
                self.wasPacked = False  # flag to track if the rectangle is packed        

        def get_dim_freq(packages):
            dimension_frequency = collections.Counter()
            for pkg in packages:
                for dim in pkg.dim: # made Dim iterable
                    dimension_frequency[dim] += 1
            dimension_frequency = sorted(
                dimension_frequency.items(), key=lambda x: x[1], reverse=True
            )
            return dimension_frequency

        def selectrects_2d(dimension, packages, assigned_pkgs):
            rects = []
            for i, pkg in enumerate(packages):
                if assigned_pkgs[i] == 0:
                    l, b, h = pkg.dim.l, pkg.dim.w, pkg.dim.h
                    # Check if the dimension matches any of the package dimensions
                    if l == dimension:
                        rects.append(Rect(pkg.id, pkg.cost, w=b, h=h))
                    if h == dimension:
                        rects.append(Rect(pkg.id, pkg.cost, w=l, h=b))
                    if b == dimension:
                        rects.append(Rect(pkg.id, pkg.cost, w=l, h=h))
            return rects

        def bp2d(layer : Layer, selectedrects):
            packer = rp.newPacker()
            for rect in selectedrects:     
                packer.add_rect(rect.w, rect.h, rect.id)
            packer.add_bin(layer.dim.l, layer.dim.w)
            packer.pack()
            for r in packer.rect_list():
                b, x, y, w, h, rid = r
                for rect in selectedrects:
                    if rect.id == rid:
                        rect.x = x
                        rect.y = y
                        layer.add_rect(rect)
                        rect.wasPacked = True
                        break
            return layer
        
        def make_layers(packages, length,breadth):
            layers = []
            dimension_frequency = get_dim_freq(packages)
            assigned_pkgs = [0] * (len(packages) + 1)
            for dim in dimension_frequency:
                selectedrects = selectrects_2d(int(dim[0]), packages,assigned_pkgs)
                layers.append(bp2d(Layer(0, [], length, breadth, int(dim[0]), 0, 0), selectedrects))
                for rect in layers[-1].packedrects:
                    assigned_pkgs[rect.id] = 1
            return layers

        layers = make_layers(env.packages, ULDs[5].dim.l, ULDs[5].dim.w)
        """
        -----------------------------------------------------------------------------------------------------------------------------
        Google OR Tools
        ------------------------------------------------------------------------------------------------------------------------------
        """

        prefinal_sol = []
        data = {}
        data["weights"] = []
        data["values"] = []
        # data["layers"] = layers

        for layer in layers:
            data["weights"].append(layer.dim.h)
            data["values"].append(layer.cost)

        assert len(data["weights"]) == len(data["values"])
        data["num_items"] = len(data["weights"])
        data["all_items"] = range(data["num_items"])

        data["bin_capacities"] = []
        for i in range(2, 6):
            data["bin_capacities"].append(ULDs[i].dim.h)
        data["num_bins"] = len(data["bin_capacities"])
        data["all_bins"] = range(data["num_bins"])

        solver = pywraplp.Solver.CreateSolver("SCIP")
        if solver is None:
            print("SCIP solver unavailable.")
            return

        # Variables.
        # x[i, b] = 1 if item i is packed in bin b.
        x = {}
        for i in data["all_items"]:
            for b in data["all_bins"]:
                x[i, b] = solver.BoolVar(f"x_{i}_{b}")

        # Constraints.
        # Each item is assigned to at most one bin.
        for i in data["all_items"]:
            solver.Add(sum(x[i, b] for b in data["all_bins"]) <= 1)

        # The amount packed in each bin cannot exceed its capacity.
        for b in data["all_bins"]:
            solver.Add(
                sum(x[i, b] * data["weights"][i] for i in data["all_items"])
                <= data["bin_capacities"][b]
            )

        # Objective.
        # Maximize total value of packed items.
        objective = solver.Objective()
        for i in data["all_items"]:
            for b in data["all_bins"]:
                objective.SetCoefficient(x[i, b], data["values"][i])
        objective.SetMaximization()

        print(f"Solving with {solver.SolverVersion()}")
        status = solver.Solve()

        selectedlayers = []
        if status == pywraplp.Solver.OPTIMAL:
            print(f"Total packed value: {objective.Value()}")
            total_weight = 0
            for b in data["all_bins"]:
                print(f"Bin {b}")
                bin_weight = 0
                bin_value = 0
                for i in data["all_items"]:
                    if x[i, b].solution_value() > 0:
                        selectedlayers.append(i)
                        print(
                            f"Layer {i} sum of heights: {data['weights'][i]} total_cost_p200:"
                            f" {data['values'][i]}",
                        )
                        for rect in data["layers"][i].packedlist:
                            prefinal_sol.append(
                                [
                                    rect.id,
                                    f"U{b+3}",
                                    (rect.x, rect.y, bin_weight),
                                    (
                                        rect.x + rect.w,
                                        rect.y + rect.h,
                                        bin_weight + data["weights"][i],
                                    ),
                                ]
                            )
                        bin_weight += data["weights"][i]
                        bin_value += data["values"][i]
                print(f"Packed bin weight: {bin_weight}")
                print(f"Packed bin value: {bin_value}\n")
                total_weight += bin_weight
            print(f"Total packed weight: {total_weight}")
            print("FINALLY: ", prefinal_sol)

            for row in prefinal_sol:
                pkg_id = int(row[0][2:])
                uld_id = int(row[1][1:])
                pkg = env.packages[pkg_id - 1]
                # pkg.uld_id = uld_id
                p1 = Point(*row[2])
                p2 = Point(*row[3])
                # pkg.corners=(p1,p2)

                uld = env.ULDs[uld_id]
                # uld.packages.append(pkg)
                # uld.has_priority = uld.has_priority or pkg.is_priority
                env.add_package(pkg, uld, (p1, p2))
        else:
            print("The problem does not have an optimal solution.")
