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
        
        
        layers,assigned_pkgs = make_layers_fancy([ pkg for pkg in env.packages if 1],  env.ULDs[0].dim.l, env.ULDs[0].dim.w,rejection_threshold = 0.95,k_param=0)
        layers = sorted(layers, key=lambda x: x.packing_eff, reverse=True)
        print(assigned_pkgs)
        for layer in layers:
            print(layer.packing_eff,layer.cost,layer.dim.h)
        
        print("Start OR")
        mapping = assign_layers(layers,env.ULDs,or_tools = True)

        mapping = [None]*(len(env.ULDs))
        i=0
        for c in layers:
            
            if(mapping[i] == None):
                mapping[i] = []
                mapping[i].append(c)
                c.uldno = i
            i+=1
            i%=len(env.ULDs)

        if(mapping != None):
            for b in range(len(mapping)):
                height = 0
                if(mapping[b] != None):
                    for layer in mapping[b]:
                        add_layer(env,layer,height)
                        print(height,layer.dim.h,env.ULDs[b].dim.h)
                        height += layer.dim.h
                        print(layer.packing_eff,layer.cost,layer.dim.h)
        else:   
            print("The problem does not have an optimal solution.")
