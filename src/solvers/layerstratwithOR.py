import csv
import collections
from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point,Package,Dim
import rectpack as rp
from algorithm_interface import PackingAlgorithm
from solvers.layering import make_layers,assign_layers,add_layer,make_layers_fancy,selectrects_2d,get_dim_freq


class LayerPacking(PackingAlgorithm):

    def solve(self, env: Environment):
        for uld in env.ULDs:
            print(uld.dim.h)
            selectedrects_2d = selectrects_2d(uld.dim.h, env.packages,[0]*(len(env.packages)+1))
            print(len(selectedrects_2d))
            layers,assign_packages = make_layers(selectedrects_2d,uld.dim.l,uld.dim.w,rejection_threshold=0.5)
            print(layers)
            for layer in layers:
                print(layer.packing_eff,layer.cost,layer.dim.h)
         
        add_layer(env,uld,layers[0])
        