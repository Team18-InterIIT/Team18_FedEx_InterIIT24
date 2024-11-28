
import collections
from ortools.linear_solver import pywraplp
from entity import Point,Package,Dim
import rectpack as rp

def selectrects_2d(dimension, package):
    rects = []
    for pkg in packages:
        (l,b,h) = (pkg.dim.l,pkg.dim.w,pkg.dim.h)
        if(l == dimension):
            rects.append(Rect(pkg.id, pkg.cost, w=b, h=h))
        if(h == dimension):
            rects.append(Rect(pkg.id, pkg.cost, w=l, h=b))  
        if(b == dimension):
            rects.append(Rect(pkg.id, pkg.cost, w=l, h=h))
    return rects

class Layer:
    def __init__(self, pe, packed_list, length, breadth, height, uldno, cost):
        self.packing_eff = pe
        self.packedrects : list[Rect] = []
        self.dim : Dim = Dim(length,breadth,height)
        self.uldno = uldno
        self.cost = cost
    def add_rect(self, rect):
        self.packedrects.append(rect)
        self.cost += rect.cost


class Rect:
    def __init__(self, id, cost, x=0, y=0, w=0, h=0):
        self.id = id
        self.cost = cost
        self.x = 0  # x-coordinate of the rectangle's top-left corner
        self.y = 0  # y-coordinate of the rectangle's top-left corner
        self.w = w  # width of the rectangle
        self.h = h  # height of the rectangle
        self.wasPacked = False  # flag to track if the rectangle is packed        





def bp2d(layer : Layer,selectedrects):
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

packages = []
packages.append(Package(["83","50","78","62","88","Economy","87"]))
packages.append(Package(["17","99","73","50","30","Economy","80"]))
packages.append(Package(["5","75","43","50","85","Economy","61"]))
packages.append(Package(["287","60","50","81","135","Economy","60"])) 
packages.append(Package(["24","44","44","50","22","Economy","63"]))
selectedrects = selectrects_2d(50,packages)
layer = Layer(0.0,[],244,318,50,0,0)
packedl = bp2d(layer,selectedrects)