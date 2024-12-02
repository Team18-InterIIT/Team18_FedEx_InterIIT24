import csv
import collections
from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point, Package, Dim
import rectpack as rp
from algorithm_interface import PackingAlgorithm
from solvers.layering import make_layers, add_layer, make_layers_fancy


class LayerPacking(PackingAlgorithm):

    def solve(self, env: Environment):

        layers = make_layers_fancy(
            env.packages,
            env.ULDs[0].dim.l,
            env.ULDs[0].dim.w,
            rejection_threshold=0.9,
            k_param=0,
        )
        layers = sorted(layers, key=lambda x: x.packing_eff, reverse=True)

        # print("Start OR")
        # mapping = assign_layers(layers, env.ULDs, or_tools=True)

        mapping = [[] for _ in range(len(env.ULDs))]
        for layer_no in range(len(layers)):
            uld_no = layer_no % len(env.ULDs)
            mapping[uld_no].append(layers[layer_no])
            layers[layer_no].uldno = uld_no

        print(mapping)

        if mapping != None:
            for uld in range(len(mapping)):
                height = 0
                for layer_no in mapping[uld]:
                    if height + layer_no.dim.h <= env.ULDs[uld].dim.h:
                        add_layer(env, layer_no, height)
                    else:
                        print(f"ULD {uld} is full")
                        print()
                        break
                    height += layer_no.dim.h
                    print(layer_no.packing_eff, layer_no.cost, layer_no.dim.h)
        else:
            print("The problem does not have an optimal solution.")
