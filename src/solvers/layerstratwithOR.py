import csv
import collections
from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point,Package,Dim
import rectpack as rp
from algorithm_interface import PackingAlgorithm
from solvers.layering import make_layers,assign_layers,add_layer,make_layers_fancy


class LayerPacking(PackingAlgorithm):

    def solve(self, env: Environment):
        
        
        layers,assigned_pkgs = make_layers_fancy(env.packages,  env.ULDs[0].dim.l, env.ULDs[0].dim.w,rejection_threshold = 0.9,k_param=0)
        layers = sorted(layers, key=lambda x: x.packing_eff, reverse=True)
        print(assigned_pkgs)
        for layer in layers:
            print(layer.packing_eff,layer.cost,layer.dim.h)
        

        #Knapsack on heights of layers to maximize the total value of packed items.
        # solver = pywraplp.Solver.CreateSolver("SAT")
        # if solver is None:
        #     print("SCIP solver unavailable.")
        #     return
        # # Variables
        # x = {}
        # for i in range(len(layers)):
        #     for b in range(len(env.ULDs)):
        #         x[i, b] = solver.BoolVar(f"x_{i}_{b}")
        
        # # Constraints.
        # # Each item is assigned to at most one bin.
        # for i in range(len(layers)):
        #     solver.Add(sum(x[i, b] for b in range(len(env.ULDs))) <= 1)

        # # The amount packed in each bin cannot exceed its capacity.
        # for b in range(len(env.ULDs)):
        #     solver.Add(
        #     sum(x[i, b] * layers[i].dim.h for i in range(len(layers)))
        #     <= env.ULDs[b].dim.h
        #     )

        # # Objective.
        # # Maximize total value of packed items.
        # objective = solver.Objective()
        # for i in range(len(layers)):
        #     for b in range(len(env.ULDs)):
        #         objective.SetCoefficient(x[i, b], layers[i].cost)
        # objective.SetMaximization()
        # print(len(layers),len(env.ULDs))
        # print(f"Solving with {solver.SolverVersion()}")
        # print(solver.NumVariables(), "variables")
        # print(solver.NumConstraints(), "constraints")
        # status = solver.Solve()
        # print("status:",status) 
        # mapping = [None]*len(env.ULDs)
        # for i in range(len(layers)):
        #     for b in range(len(env.ULDs)):
        #         if x[i,b].solution_value() > 0:
        #             if(mapping[b] == None):
        #                 mapping[b] = []
        #             mapping[b].append(layers[i])
        mapping = assign_layers(layers,env.ULDs,or_tools = True)
        if(mapping != None):
            for b in range(len(mapping)):
                height = 0
                if(mapping[b] != None):
                    for layer in mapping[b]:
                        add_layer(env,layer,height)
                        height += layer.dim.h
                        print(layer.packing_eff,layer.cost,layer.dim.h)
        else:   
            print("The problem does not have an optimal solution.")
