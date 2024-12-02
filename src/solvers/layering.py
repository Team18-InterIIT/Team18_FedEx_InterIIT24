from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point,Package,Dim
import rectpack as rp
from hyperpack import HyperPack
import hyperpack as hp
import collections
from ortools.linear_solver import pywraplp

class Layer:
    def __init__(self, pe, length, breadth, height, uldno, cost, weight, height_ratio=1, weight_ratio=1, cost_desity=1):
        """
        Initialize a rectangle with given parameters.

        Parameters:
        id (int): The identifier of the rectangle.
        cost (float): The cost associated with the rectangle.
        x (int): The x-coordinate of the rectangle's top-left corner.
        y (int): The y-coordinate of the rectangle's top-left corner.
        w (int): The width of the rectangle.
        h (int): The height of the rectangle.
        """
        self.packing_eff = pe
        self.packedrects : list[Rect] = []
        self.dim : Dim = Dim(length,breadth,height)
        self.uldno = uldno
        self.weight = 0 
        self.cost = 0
        self.area = 0
        self.height_ratio = 1
        self.weight_ratio = 1
        self.cost_density = 1
        self.cost_economy= 0
        self.area_economy = 0

    def __repr__(self):
        return f"Layer({self.uldno})"



    def add_rect(self, rect):
        """
        Add a rectangle to the ULD and update the cost and packing efficiency.

        Parameters:
        rect (Rect): The rectangle to be added to the ULD.
        """
        self.packedrects.append(rect)
        self.cost += rect.cost if rect.cost != float("inf") else 1e9
        self.cost_economy += rect.cost if not rect.is_priority else 0
        self.weight +=rect.weight 
        self.area += rect.w * rect.h
        self.area_economy += rect.w * rect.h if not rect.is_priority else 0 
        self.packing_eff = self.area / (self.dim.l * self.dim.w)

#yesorno is 0 if economy, 1 if priority 
class Rect:
    def __init__(self, id, cost, weight, x=0, y=0, w=0, h=0, yesorno=0):
        self.id = id
        self.is_priority = yesorno
        self.cost = cost
        self.weight = weight
        self.x = 0  # x-coordinate of the rectangle's top-left corner
        self.y = 0  # y-coordinate of the rectangle's top-left corner
        self.w = w  # width of the rectangle
        self.h = h  # height of the rectangle
        self.wasPacked = False  # flag to track if the rectangle is packed


def get_dim_freq(packages, k_param):
    """
    Calculate the frequency of dimensions in the given packages.

    Parameters:
    packages (list): A list of packages, each with dimensions.
    k_param (int): A parameter to adjust the dimension frequency calculation.

    Returns:
    list: A sorted list of tuples containing dimensions and their frequencies.
    """
    dimension_frequency = collections.Counter()
    for pkg in packages:
        for dim in pkg.dim: # made Dim iterable
            for i in range(1,k_param+1):
                dimension_frequency[dim+i] += 1
                # if(dim-i > 0):
                #     dimension_frequency[dim-i] += 1
            dimension_frequency[dim] += 1 
    dimension_frequency = sorted(
        dimension_frequency.items(), key=lambda x: x[1], reverse=True
    )
    return dimension_frequency


def selectrects_2d(dimension, packages, assigned_pkgs):
    rects = []
    for pkg in packages:
        if assigned_pkgs[pkg.id] == 0:
            l, b, h = pkg.dim.l, pkg.dim.w, pkg.dim.h
            # Check if the dimension matches any of the package dimensions
            if l == dimension:
                rects.append(Rect(pkg.id, pkg.cost,pkg.weight, w=b, h=h, yesorno = pkg.is_priority))
            elif h == dimension:
                rects.append(Rect(pkg.id, pkg.cost,pkg.weight, w=l, h=b, yesorno = pkg.is_priority))
            elif b == dimension:
                rects.append(Rect(pkg.id, pkg.cost,pkg.weight, w=l, h=h, yesorno = pkg.is_priority))
    return rects

#===================================================================#
# def bp2d(layer : Layer, selectedrects):
#     packer = rp.newPacker()
#     for rect in selectedrects:     
#         packer.add_rect(rect.w, rect.h, rect.id)
#     packer.add_bin(layer.dim.l, layer.dim.w)
#     packer.pack()
#     for r in packer.rect_list():
#         b, x, y, w, h, rid = r
#         h_max=0
#         for rect in selectedrects:
#             if rect.id == rid:
#                 rect.x = x
#                 rect.y = y
#                 rect.w = w
#                 rect.h = h
#                 layer.add_rect(rect)
#                 rect.wasPacked = True
#                 break 
#     return layer


def bp2d(layer: Layer, selectedrects):
    # print(layer.dim.l, layer.dim.w)
    container={
        "ULD1": {
            "L": layer.dim.w,
            "W": layer.dim.l
        }
    }

    items = {}
    for rect in selectedrects:
        # print(rect.w,rect.h)
        items[str(rect.id)] = {
            "w": rect.w,  # Width of the rectangle
            "l": rect.h   # Length (Height) of the rectangle
        }

    problem=hp.HyperPack(
        containers=container, items=items
    )
    print("Start hyperpack(local search)")
    problem.local_search()
    # problem.hypersearch()

    for container_id, items in problem.solution.items():
        # # Create a new Layer for each container (you may adjust the dimensions or properties)
        # layer = Layer(pe=0, packed_list=[], length=100, breadth=100, height=10, uldno=0, cost=0)
        
        for item_id, item_data in items.items():
            x, y, w, l = item_data  # Extract Xo, Yo, width, length
            
            # Find the corresponding Rect object by id
            for rect in selectedrects:
                if rect.id == int(item_id):
                    # If item was rotated (w, l might be swapped), handle that here
                    rect.x = x
                    rect.y = y
                    rect.w = w
                    rect.h = l  # Assuming that w and l are swapped in some cases
                    layer.add_rect(rect)
                    rect.wasPacked = True
                    break

    return layer



#=================================================================#
#rejection_threshold is for 2D packing efficiency 
#weight_ratio_th is the threshold or rejecting very heavy layers 
# it is x => weight of layer/ weight capacity of ULD <= x* height of layer/ height of ULD 
# similarly cost rejection ratio cost_th
# it is y => cost of layer/ volume of layer >= y* avg_cost (constant) 
def make_layers(packages,length,breadth,rejection_threshold = 0.8,
weight_ratio_th = 0.95
, cost_th = 0.9, assigned_pkgs =[],margin = 0,
uld_height=0, uld_weight=0):
    # print(uld_height)
    layers = []
    dimension_frequency = get_dim_freq(packages,margin)
    if(len(assigned_pkgs) == 0):
        assigned_pkgs = [0]*((max(pkg.id for pkg in packages))+1)
    for dim in dimension_frequency:
        selectedrects = selectrects_2d(int(dim[0]), packages,assigned_pkgs)
        area = sum([rect.w*rect.h for rect in selectedrects])
        layer_cost = sum([rect.cost for rect in selectedrects])
        
        avg_cost_const = 0.00021
        layer_vol = length * breadth * int(dim[0]) 
        height_ratio = int(dim[0])/uld_height
        # if(layer_cost >= cost_th*avg_cost_const* layer_vol and 
        #    self.area >= length*breadth*rejection_threshold
        #    and ):
        if(area >= length*breadth*rejection_threshold):
            # print(length, breadth)
            layer = bp2d(Layer(0, length, breadth, int(dim[0]), -1, 0, 0), selectedrects)
            layer.height_ratio = height_ratio
            layer.weight_ratio = layer.weight/uld_weight
            layer.cost_density = layer.cost_economy/(layer.area_economy*int(dim[0]))
            if(layer.packing_eff > rejection_threshold
               and layer.cost_density >= cost_th*avg_cost_const
               and layer.weight_ratio <= weight_ratio_th*layer.height_ratio):
                layers.append(layer)
                for rect in layers[-1].packedrects:
                    assigned_pkgs[rect.id] = 1
                # print(layer.cost_economy, layer.area_economy*int(dim[0]))
    for layer in layers:
        # print("LAYER:")
        for rect in layer.packedrects:
            print(rect.id)
    return layers,assigned_pkgs

def make_layers_fancy(packages, length,breadth,rejection_threshold = 0.9,k_param = 0, uldheight =0 ,uldweight=0, weight_th =1, cost_th =1 ):
    all_layers = []
    # print(uldheight)
    layers,assigned_pkgs = make_layers(packages,length,breadth,rejection_threshold,uld_height=uldheight,uld_weight=uldweight, weight_ratio_th=weight_th, cost_th=cost_th)
    all_layers.extend(layers)
    margin = 0
    while(k_param > 0):
        margin +=1 
        layers, assigned_pkgs = make_layers(packages,length,breadth,rejection_threshold,assigned_pkgs,margin,uld_height=uldheight,uld_weight=uldweight, weight_ratio_th=weight_th, cost_th=cost_th)
        all_layers.extend(layers)
        k_param -= 1  
    return all_layers,assigned_pkgs


# def assign_layers(layers,ULDs,or_tools = False):
#     if(or_tools):   
#         solver = pywraplp.Solver.CreateSolver("SAT")
#         if solver is None:
#             print("SCIP solver unavailable.")
#             return
#         # Variables
#         x = {}
#         for i in range(len(layers)):
#             for b in range(len(ULDs)):
#                 x[i, b] = solver.BoolVar(f"x_{i}_{b}")
        
#         # Constraints.
#         # Each item is assigned to at most one bin.
#         for i in range(len(layers)):
#             solver.Add(sum(x[i, b] for b in range(len(ULDs))) <= 1)

#         # The amount packed in each bin cannot exceed its capacity.
#         for b in range(len(ULDs)):
#             solver.Add(
#             sum(x[i, b] * layers[i].dim.h for i in range(len(layers)))
#             <= ULDs[b].dim.h
#             )

#         # Objective.
#         # Maximize total value of packed items.
#         objective = solver.Objective()
#         for i in range(len(layers)):
#             for b in range(len(ULDs)):
#                 objective.SetCoefficient(x[i, b], layers[i].cost)
#         objective.SetMaximization()
#         print(len(layers),len(ULDs))
#         print(f"Solving with {solver.SolverVersion()}")
#         print(solver.NumVariables(), "variables")
#         print(solver.NumConstraints(), "constraints")
#         status = solver.Solve()
#         mapping = [None]*len(ULDs)
#         print("status:",status) 
#         if(not status):
#             for i in range(len(layers)):
#                 for b in range(len(ULDs)):
#                     if x[i,b].solution_value() > 0:
#                         if(mapping[b] == None):
#                             mapping[b] = []
#                         layers[i].uldno = b
#                         mapping[b].append(layers[i])
#                         break
#             return mapping
#         else:
#             return None


def add_layer(env,assigned_layer,height):
    for rect in assigned_layer.packedrects:
        # Find the package from environment using rect.id
        for pkg in env.packages:
            if pkg.id == rect.id:
                # Create placement points
                p1 = Point(rect.x, rect.y, height)
                h = sum(dim for dim in pkg.dim) - rect.w - rect.h
                if(assigned_layer.dim.h != h):
                    print("Height mismatch")
                    print([dim for dim in pkg.dim],rect.w,rect.h,assigned_layer.dim.h)
                    print(assigned_layer.dim.h,h)
                p2 = Point(rect.x + rect.w,rect.y + rect.h, height+ h)
                # Add package to environment with corresponding ULD
                added = env.add_package(pkg, env.ULDs[assigned_layer.uldno], (p1, p2))
                # if(not added):
                #     print("Error placing package")
                break
    return env