from ortools.linear_solver import pywraplp
from environment import Environment
from entity import Point, Package, Dim
import rectpack as rp
from hyperpack import HyperPack
import hyperpack as hp
import collections
from ortools.linear_solver import pywraplp


class Layer:
    def __init__(self, pe, packed_list, length, breadth, height, uldno, cost):
        self.packing_eff = pe
        self.packedrects: list[Rect] = []
        self.dim: Dim = Dim(length, breadth, height)
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


def get_dim_freq(packages, k_param):
    dimension_frequency = collections.Counter()
    for pkg in packages:
        for dim in pkg.dim:  # made Dim iterable
            for i in range(1, k_param + 1):
                dimension_frequency[dim + i] += 1
                # if(dim-i > 0):
                #     dimension_frequency[dim-i] += 1
            dimension_frequency[dim] += 1
    dimension_frequency = sorted(
        dimension_frequency.items(), key=lambda x: x[1], reverse=True
    )
    return dimension_frequency


def selectrects_2d(dimension, packages, assigned_pkgs, return_assigned=False):
    rects = []
    for pkg in packages:
        if assigned_pkgs[pkg.id] == 0:
            l, b, h = pkg.dim.l, pkg.dim.w, pkg.dim.h
            # Check if the dimension matches any of the package dimensions
            if l == dimension:
                if return_assigned:
                    assigned_pkgs[pkg.id] = 1
                rects.append(Rect(pkg.id, pkg.cost, w=b, h=h))
            elif h == dimension:
                if return_assigned:
                    assigned_pkgs[pkg.id] = 1
                rects.append(Rect(pkg.id, pkg.cost, w=l, h=b))
            elif b == dimension:
                if return_assigned:
                    assigned_pkgs[pkg.id] = 1
                rects.append(Rect(pkg.id, pkg.cost, w=l, h=h))
    if return_assigned:
        return rects, assigned_pkgs
    else:
        return rects


# ===================================================================#
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
    # print(dir(hp))
    container = {"ULD1": {"L": layer.dim.w, "W": layer.dim.l}}

    items = {}
    for rect in selectedrects:
        items[str(rect.id)] = {
            "w": rect.w,  # Width of the rectangle
            "l": rect.h,  # Length (Height) of the rectangle
        }

    problem = hp.HyperPack(containers=container, items=items)
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


# =================================================================#

def all_layers(height,length,breadth,allowed_packages,rejection_threshold = 0.8):
    all_layers = []
    selectedrects_2d = selectrects_2d(height, allowed_packages, [0] * (len(allowed_packages) + 1))  
    layer = bp2d(Layer(0, [],length,breadth, height, -1, 0), selectedrects_2d)   
    all_layers.append(layer)
    for rect in layer.packedrects:
        newrects = selectedrects_2d
        newrects.remove(rect)
        newlayer = bp2d(Layer(0, [],length,breadth, height, -1, 0), newrects)  
        if(layer.packing_eff > rejection_threshold):
            all_layers.append(newlayer) 
    return all_layers


def gensets(lens, n, h, current_set=None, all_sets=None):
    if current_set is None:
        current_set = []
    if all_sets is None:
        all_sets = []

    # Base case: If the current set size is n and sums to h, store the set
    if len(current_set) == n and sum(current_set) == h:
        all_sets.append(list(current_set))
        return all_sets

    # Base case: If the current set exceeds n or cannot sum to h, terminate this branch
    if len(current_set) >= n or sum(current_set) > h:
        return all_sets

    # Recursive case: Explore each number in the list
    for i in range(len(lens)):
        current_set.append(lens[i])  # Choose the number
        gensets(lens, n, h, current_set, all_sets)  # Recursive call
        current_set.pop()  # Backtrack to explore other possibilities

    return all_sets


def fullpack(packages, ULD, rejection_threshold=0.8, nmax=3):
    height = ULD.dim.h
    for n in range(nmax):
        freq_dist = get_dim_freq(packages, 0)
        freq_map = {}
        lens = []
        for freq in freq_dist:
            freq_map[freq[0]] = freq[1]
            lens.append(freq[0])
        sets = gensets(lens, n + 1, height)
        sets = sorted(sets, key=len)
        for s in sets:
            layers = []
            assigned_pkgs = [0] * (len(packages) + 1)
            for l in s:
                selectedrects_2d, assigned_pkgs = selectrects_2d(
                    l, packages, assigned_pkgs=assigned_pkgs, return_assigned=True
                )
                if len(selectedrects_2d) == 0:
                    break
                layer = bp2d(
                    Layer(0, [], ULD.dim.l, ULD.dim.w, l, -1, 0), selectedrects_2d
                )
                layers.append(layer)
            if len(layers) == len(s):
                pe = sum([layer.packing_eff * layer.dim.h for layer in layers]) / height
                if pe > rejection_threshold:
                    for layer in layers:
                        layer.uldno = ULD.id
                    return layers


def flatbed_pack(packages, ULD, rejection_threshold=0.8):
    height = ULD.dim.h
    selectedrects_2d = selectrects_2d(height, packages, [0] * (len(packages) + 1))
    layer = bp2d(Layer(0, [], ULD.dim.l, ULD.dim.w, height, -1, 0), selectedrects_2d)
    if layer.packing_eff > rejection_threshold:
        layer.uldno = ULD.id
        print("1 layer of packing efficiency ", layer.packing_eff)
        return [layer]
    else:
        freq_dist = get_dim_freq(packages, 0)
        freq_map = {}
        for freq in freq_dist:
            freq_map[freq[0]] = freq[1]
        pairsort = dict(
            sorted(
                freq_map.items(),
                key=lambda x: (freq_map.get(x[0], 0) * freq_map.get(height - x[0], 0)),
                reverse=True,  # Use reverse=True for descending order, False for ascending
            )
        )
        for x in pairsort:
            h1 = x
            h2 = height - x
            selectedrects_2d1, assigned_pkgs = selectrects_2d(
                h1, packages, [0] * (len(packages) + 1), return_assigned=True
            )
            selectedrects_2d2 = selectrects_2d(
                h2, packages, assigned_pkgs=assigned_pkgs
            )
            print(freq_map[h1], freq_map[h2])
            print(len(selectedrects_2d1), len(selectedrects_2d2))
            layer1 = bp2d(
                Layer(0, [], ULD.dim.l, ULD.dim.w, h1, -1, 0), selectedrects_2d1
            )
            layer2 = bp2d(
                Layer(0, [], ULD.dim.l, ULD.dim.w, h2, -1, 0), selectedrects_2d2
            )
            if (
                layer1.packing_eff * h1 + layer2.packing_eff * h2
                > rejection_threshold * (h1 + h2)
            ):
                layer1.uldno = ULD.id
                layer2.uldno = ULD.id
                print(
                    "2 layers of packing efficiency ",
                    layer1.packing_eff,
                    layer2.packing_eff,
                )
                return [layer1, layer2]


def make_layers(
    packages, length, breadth, rejection_threshold=0.8, assigned_pkgs=[], margin=0
):
    layers = []
    dimension_frequency = get_dim_freq(packages, margin)
    if len(assigned_pkgs) == 0:
        assigned_pkgs = [0] * (len(packages) + 1)
    for dim in dimension_frequency:
        selectedrects = selectrects_2d(int(dim[0]), packages, assigned_pkgs)
        area = sum([rect.w * rect.h for rect in selectedrects])
        if area >= length * breadth * rejection_threshold:
            layer = bp2d(
                Layer(0, [], length, breadth, int(dim[0]), -1, 0), selectedrects
            )
            if layer.packing_eff > rejection_threshold:
                layers.append(layer)
                for rect in layers[-1].packedrects:
                    assigned_pkgs[rect.id] = 1
    for layer in layers:
        print("LAYER:")
        for rect in layer.packedrects:
            print(rect.id)
    return layers, assigned_pkgs


def make_layers_fancy(packages, length, breadth, rejection_threshold=0.8, k_param=0):
    all_layers = []
    layers, assigned_pkgs = make_layers(packages, length, breadth, rejection_threshold)
    all_layers.extend(layers)
    margin = 0
    while k_param > 0:
        margin += 1
        layers, assigned_pkgs = make_layers(
            packages, length, breadth, rejection_threshold, assigned_pkgs, margin
        )
        all_layers.extend(layers)
        k_param -= 1
    return all_layers, assigned_pkgs
    nonpacked = []
    for i, pkg in enumerate(packages):
        if assigned_pkgs[i] == 0:
            nonpacked.append(pkg)
    new_layers = []
    new_map = get_dim_freq(nonpacked, 3)
    for dim in new_map:
        selectedrects = selectrects_2d(int(dim[0]), nonpacked, assigned_pkgs)
        new_layers.append(
            bp2d(Layer(0, [], length, breadth, int(dim[0]), 0, 0), selectedrects)
        )
        if new_layers[-1].packing_eff > 0.9:
            for rect in new_layers[-1].packedrects:
                assigned_pkgs[rect.id] = 1
        else:
            new_layers.pop()

    for layer in layers:
        print("LAYER:")
        for rect in layer.packedrects:
            print(rect.id)
    return layers


def assign_layers(layers, ULDs, or_tools=False):
    if or_tools:
        solver = pywraplp.Solver.CreateSolver("SAT")
        if solver is None:
            print("SCIP solver unavailable.")
            return
        # Variables
        x = {}
        for i in range(len(layers)):
            for b in range(len(ULDs)):
                x[i, b] = solver.BoolVar(f"x_{i}_{b}")

        # Constraints.
        # Each item is assigned to at most one bin.
        for i in range(len(layers)):
            solver.Add(sum(x[i, b] for b in range(len(ULDs))) <= 1)

        # The amount packed in each bin cannot exceed its capacity.
        for b in range(len(ULDs)):
            solver.Add(
                sum(x[i, b] * layers[i].dim.h for i in range(len(layers)))
                <= ULDs[b].dim.h
            )

        # Objective.
        # Maximize total value of packed items.
        objective = solver.Objective()
        for i in range(len(layers)):
            for b in range(len(ULDs)):
                objective.SetCoefficient(x[i, b], layers[i].cost)
        objective.SetMaximization()
        print(len(layers), len(ULDs))
        print(f"Solving with {solver.SolverVersion()}")
        print(solver.NumVariables(), "variables")
        print(solver.NumConstraints(), "constraints")
        status = solver.Solve()
        mapping = [None] * len(ULDs)
        print("status:", status)
        if not status:
            for i in range(len(layers)):
                for b in range(len(ULDs)):
                    if x[i, b].solution_value() > 0:
                        if mapping[b] == None:
                            mapping[b] = []
                        layers[i].uldno = b
                        mapping[b].append(layers[i])
                        break
            return mapping
        else:
            return None


def add_layer(env, assigned_layer, height):
    for rect in assigned_layer.packedrects:
        # Find the package from environment using rect.id
        for pkg in env.packages:
            if pkg.id == rect.id:
                # Create placement points
                p1 = Point(rect.x, rect.y, height)
                h = sum(dim for dim in pkg.dim) - rect.w - rect.h
                if assigned_layer.dim.h != h:
                    print("Height mismatch")
                    print(
                        [dim for dim in pkg.dim], rect.w, rect.h, assigned_layer.dim.h
                    )
                    print(assigned_layer.dim.h, h)
                p2 = Point(rect.x + rect.w, rect.y + rect.h, height + h)
                # Add package to environment with corresponding ULD
                added = env.add_package(pkg, env.ULDs[assigned_layer.uldno], (p1, p2))
                if not added:
                    print("Error placing package")
                break
    return env
