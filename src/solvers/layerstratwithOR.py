import csv
import collections
from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point,Package,Dim
import rectpack as rp
from algorithm_interface import PackingAlgorithm
import uuid


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
        class Layer:
            def __init__(self, pe, packed_list, length, breadth, height, uldno, cost):
                self.packing_eff = pe
                self.packedrects : list[Rect] = []
                self.dim : Dim = Dim(length,breadth,height)
                self.uldno = uldno
                self.cost = cost if cost != float("inf") else 1e9
                self.area = 0

            def add_rect(self, rect):
                self.packedrects.append(rect)
                self.cost += rect.cost if rect.cost != float("inf") else 1e9
                self.area += rect.w * rect.h
                self.packing_eff = self.area / (self.dim.l * self.dim.w)

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
                    elif h == dimension:
                        rects.append(Rect(pkg.id, pkg.cost, w=l, h=b))
                    elif b == dimension:
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
                        rect.w = w
                        rect.h = h
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
        
        layers = [l for l in make_layers(env.packages, env.ULDs[0].dim.l, env.ULDs[0].dim.w) if l.packing_eff > 0.82]
        layers = sorted(layers, key=lambda x: x.packing_eff, reverse=True)
        for layer in layers:
            print(layer.packing_eff,layer.cost,layer.dim.h)
        #for layer in layers:
        #     print(len(layer.packedrects),layer.dim.h,layer.packing_eff,layer.cost)
        #     for rect in layer.packedrects:
        #         print(rect.id,rect.x,rect.y,rect.w,rect.h)
        # print(len(layers))
        """
        -----------------------------------------------------------------------------------------------------------------------------
        Google OR Tools
        ------------------------------------------------------------------------------------------------------------------------------
        """
        prefinal_sol = []

        solver = pywraplp.Solver.CreateSolver("SAT")
        if solver is None:
            print("SCIP solver unavailable.")
            return
        # Variables
        x = {}
        for i in range(len(layers)):
            for b in range(len(env.ULDs)):
                x[i, b] = solver.BoolVar(f"x_{i}_{b}")
        
        # Constraints.
        # Each item is assigned to at most one bin.
        for i in range(len(layers)):
            solver.Add(sum(x[i, b] for b in range(len(env.ULDs))) <= 1)

        # The amount packed in each bin cannot exceed its capacity.
        for b in range(len(env.ULDs)):
            solver.Add(
            sum(x[i, b] * layers[i].dim.h for i in range(len(layers)))
            <= env.ULDs[b].dim.h
            )

        # Objective.
        # Maximize total value of packed items.
        objective = solver.Objective()
        for i in range(len(layers)):
            for b in range(len(env.ULDs)):
                objective.SetCoefficient(x[i, b], layers[i].cost)
        objective.SetMaximization()
        print(len(layers),len(env.ULDs))
        print(f"Solving with {solver.SolverVersion()}")
        print(solver.NumVariables(), "variables")
        print(solver.NumConstraints(), "constraints")
        status = solver.Solve()


        def add_layer(env,layer,ULD_num):
            for rect in layer.packedrects:
                # Find the package from environment using rect.id
                for pkg in env.packages:
                    if pkg.id == rect.id:
                        # Create placement points
                        p1 = Point(rect.x, rect.y, bin_weight)
                        p2 = Point(rect.x + rect.w,rect.y + rect.h, bin_weight + layers[i].dim.h)
                        # Add package to environment with corresponding ULD
                        env.add_package(pkg, env.ULDs[ULD_num], (p1, p2))
                        break
            return env
        if status == pywraplp.Solver.OPTIMAL:
            total_weight = 0
            for b in range(len(env.ULDs)):
                bin_weight = 0
                for i in range(len(layers)):
                    if x[i,b].solution_value() > 0:
                        env = add_layer(env,layers[i], b)
                        bin_weight += layers[i].dim.h
                        print("Packing effieciency",layers[i].packing_eff)
        else:
            print("The problem does not have an optimal solution.")
