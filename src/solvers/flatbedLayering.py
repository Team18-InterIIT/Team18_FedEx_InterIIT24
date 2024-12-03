import csv
import collections
from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point,Package,Dim
import rectpack as rp
from algorithm_interface import PackingAlgorithm
from solvers.layering import make_layers,assign_layers,add_layer,make_layers_fancy,flatbed_pack,fullpack


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
            assigned_pkgs = [0]*len(env.packages+1)
            for pkg in uld.packages:
                assigned_pkgs[pkg.id] = 1
        
        for uld in env.ULDs:
            for pkg in uld.packages:
                assigned_pkgs[pkg.id] = 0
            layers = fullpack(env.packages,uld,assigned_pkgs)

        