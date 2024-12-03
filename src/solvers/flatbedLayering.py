import csv
import collections
from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point,Package,Dim
import rectpack as rp
from algorithm_interface import PackingAlgorithm
from solvers.layering import make_layers,assign_layers,add_layer,make_layers_fancy,flatbed_pack,fullpack,layer_replace


class LayerPacking(PackingAlgorithm):

    def solve(self, env: Environment):
        for uld in env.ULDs:
            print(uld.dim.h)
            layers = fullpack(env.packages,uld,rejection_threshold=0.92)
            print()
            h = 0
            for layer in layers:
                print(layer.packing_eff)
                print(h)
                add_layer(env,layer,h)
                h += layer.dim.h
    def improve(self,env:Environment):
        for uld in env.ULDs:
            assigned_pkgs = [0]*(len(env.packages)+1)
            for pkg in uld.packages:
                assigned_pkgs[pkg.id] = 1
        
        for uld in env.ULDs:
            if(not uld.has_priority):
                for pkg in uld.packages:
                    assigned_pkgs[pkg.id] = 0
                layers = layer_replace(uld,env.packages,assigned_pkgs)
                if(layers != None):
                    print("Accepted better")
                    uld.reset()
                    for layer in layers:
                        add_layer(env,layer,uld.dim.h)
                        uld.dim.h += layer.dim.h
                        for pkg in layer.packages:
                            assigned_pkgs[pkg.id] = 1
        return env

        