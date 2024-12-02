import csv
import collections
from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point, Package, Dim
import rectpack as rp
from algorithm_interface import PackingAlgorithm
from solvers.layering import make_layers, add_layer, make_layers_fancy, fullpack


# class LayerPacking(PackingAlgorithm):

#     def solve(self, env: Environment):

#         layers,assigned_pkgs = make_layers_fancy(
#             env.packages,
#             env.ULDs[0].dim.l,
#             env.ULDs[0].dim.w,
#             rejection_threshold=0.93,
#             weight_th=1.05,
#             cost_th=1.2,
#             k_param=0,
#             uldheight=env.ULDs[0].dim.h,
#             uldweight=env.ULDs[0].weight_limit
#         )
#         layers = sorted(layers, key=lambda x: x.packing_eff, reverse=True)

#         # print("Start OR")
#         # mapping = assign_layers(layers, env.ULDs, or_tools=True)

#         mapping = [[] for _ in range(len(env.ULDs))]
#         for layer_no in range(len(layers)):
#             uld_no = layer_no % len(env.ULDs)
#             mapping[uld_no].append(layers[layer_no])
#             layers[layer_no].uldno = uld_no

#         print(mapping)

#         if mapping != None:
#             for uld in range(len(mapping)):
#                 height = 0
#                 for layer_no in mapping[uld]:
#                     if height + layer_no.dim.h <= env.ULDs[uld].dim.h:
#                         add_layer(env, layer_no, height)
#                     else:
#                         print(f"ULD {uld} is full")
#                         print()
#                         break
#                     height += layer_no.dim.h
#                     print(layer_no.packing_eff, layer_no.cost, layer_no.dim.h)
#                     print("height ratio: ", layer_no.height_ratio, "weight_ratio: ", layer_no.weight_ratio, "cost_density: ", layer_no.cost_density)
#         else:
#             print("The problem does not have an optimal solution.")
class LayerPacking(PackingAlgorithm):

    def solve(self, env: Environment):
        for uld in env.ULDs:
            print(uld.dim.h)
           
            layers = fullpack(packages=env.packages, ULD=uld, rejection_threshold=0.9,
             weight_ratio_th=1.5,
             cost_th = 0.7,
             assigned_pkgs = [],
             margin= 0,
             uld_height = uld.dim.h,
             uld_weight = uld.weight_limit,
             nmax=2)
            print()
            h = 0
            for layer in layers:
                add_layer(env,layer,h)
                h += layer.dim.h
                print("h:",h)
            print(env.ULDs[0].weight)
