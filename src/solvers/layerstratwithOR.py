import csv
import collections
from ortools.linear_solver import pywraplp

ULDs = {
    1: {"dimensions": (224,318,162), "weight_limit": 2500},
    2: {"dimensions": (224,318,162), "weight_limit": 2500},
    3: {"dimensions": (244,318,244), "weight_limit": 2800},
    4: {"dimensions": (244,318,244), "weight_limit": 2800},
    5: {"dimensions": (244,318,285), "weight_limit": 3500},
    6: {"dimensions": (244,318,285), "weight_limit": 3500},
}
packages=[]

filePath='/Users/krishnaiitm/Desktop/datanew3.csv'
with open(filePath, 'r', newline='', encoding='utf-8') as file:
        csv_reader = list(csv.reader(file))
        #k = int(csv_reader[0][0])
        for row in csv_reader:
            if(row):
                if(row[0][0]=="P"):
                      packages.append(row)
     

dimension_frequency = collections.Counter()
for pkg in packages:
    l, b, h = pkg[1:4]
    dimension_frequency[l] += 1
    dimension_frequency[b] += 1
    dimension_frequency[h] += 1

dimension_frequency = sorted(dimension_frequency.items(), key=lambda x: x[1],reverse=True)



def selectboxes_2d(dimension, package):
    selected=[]
    area=0
    for pkg in package:
            l=int(pkg[1])
            b=int(pkg[2])
            h=int(pkg[3])
            m=int(pkg[4])
            
            if(l==dimension):
                if(pkg[6]!='-'):
                    selected.append((pkg[0],b,h,m,int(pkg[6])))
                else:
                    selected.append((pkg[0],b,h,m,200))

                   
                area+=b*h
            elif(b==dimension):
                if(pkg[6]!='-'):
                    selected.append((pkg[0],b,h,m,int(pkg[6])))
                else:
                    selected.append((pkg[0],b,h,m,200))
                area+=l*h
            elif(h==dimension):
                if(pkg[6]!='-'):
                    selected.append((pkg[0],b,h,m,int(pkg[6])))
                else:
                    selected.append((pkg[0],b,h,m,200))
                area+=l*b
            
    return selected

class Layer:
    def __init__(self,pe,packed_list,height,uldno,cost):
        self.packing_eff=pe
        self.packedlist=packed_list
        self.height=height
        self.uldno=uldno
        self.cost=cost


class Rect:
    def __init__(self,id,cost,x=0,y=0, w=0, h=0):
        self.id=id
        self.cost=cost
        self.x = 0  # x-coordinate of the rectangle's top-left corner
        self.y = 0  # y-coordinate of the rectangle's top-left corner
        self.w = w  # width of the rectangle
        self.h = h  # height of the rectangle
        self.wasPacked = False  # flag to track if the rectangle is packed

def pack_rects_in_container(rects, container_width, container_height):
    # Create a grid to represent the container, initialized to False (empty)
    list_of_packed_rects=[]
    Value=0
    container = [[False for _ in range(container_width)] for _ in range(container_height)]
    rects.sort(key=lambda rect: rect.h, reverse=True)
    a=0;
    A=container_height*container_width
    
    for rect in rects:
        if rect.wasPacked:
            continue  # Skip packed rectangles
        else:
            packed = False

            # Try to find an empty spot for the rectangle
            for y in range(container_height - rect.h + 1):
                if rect.wasPacked:
                    break
                for x in range(container_width - rect.w + 1):
                    if rect.wasPacked:
                        break
                    can_fit = True
                    # Check if the rectangle fits in the current position (no overlap)
                    for iy in range(y, y + rect.h):
                        if rect.wasPacked:
                            break
                        for ix in range(x, x + rect.w):
                            if rect.wasPacked:
                                break
                            if container[iy][ix]:  # If any pixel is already occupied
                                can_fit = False
                                break
                        if not can_fit:
                            break

                    # If the rectangle fits, place it in the container
                    if can_fit:
                        # Mark the occupied cells in the container as True
                        for iy in range(y, y + rect.h):
                            for ix in range(x, x + rect.w):
                                container[iy][ix] = True
                        
                        # Set rectangle's packed status and position
                        rect.x = x
                        rect.y = y
                        Value+=rect.cost
                        rect.wasPacked = True  # Mark it as packed
                        packed = True
                        list_of_packed_rects.append(rect)
                        # print(f"Packed rectangle {rect.w}x{rect.h} at position ({x}, {y}) in uld ")
                        break  # No need to check further once packed

        # If the rectangle could not be packed, mark it as not packed
            if not packed:
                # print(f"Rectangle {rect.w}x{rect.h} could not be packed in uld ")
                rect.wasPacked = False
            
            else:
                rect.wasPacked=True
                a+=rect.w*rect.h
    packing_efficiency=a/A
    # print("Area Efficiency ",packing_efficiency,"for dimension ",dimension,"uld ")

    return rects , packing_efficiency, list_of_packed_rects, Value
# Define some rectangles


# Define the container size


# Pack the rectangles in the container
def make_layers(remainingpackages,uldno):
    layer_info=[]
    if not remainingpackages:
        return layer_info
    
    container_width = ULDs[uldno]['dimensions'][0]
    container_height = ULDs[uldno]['dimensions'][1]
    for dim in dimension_frequency:
        selected = selectboxes_2d(int(dim[0]),remainingpackages)
        # print(selected , int(dim))
        
        rectangles=[]
        for pkg in selected:
            rectangles.append(Rect(id=pkg[0],cost=pkg[4],w=int(pkg[1]),h=int(pkg[2])))

        packed_rects, pe,listpacked,Cost = pack_rects_in_container(rectangles, container_width, container_height)
        
        for pack in listpacked:
            remainingpackages=[y for y in remainingpackages if y[0] != pack]
        layer_info.append(Layer(pe, listpacked,int(dim[0]),uldno,Cost))
        print("| ",end='')
    
    layer_info.sort(key=lambda x: x.packing_eff,reverse=True)
    print("______________________________________________________________")
    

    return layer_info
    '''Structure of layer_info
    layer_info = [packing_eff,
                 ['P-1','P-13' ......] (list of the ids of the packets),
                 height,
                 ULD-Number,
                 Cost of the whole Layer.

    ]'''

    
layers = make_layers(packages,6)
container_width = ULDs[6]['dimensions'][0]
container_height = ULDs[6]['dimensions'][1]
'''
-----------------------------------------------------------------------------------------------------------------------------
Google OR Tools
------------------------------------------------------------------------------------------------------------------------------
'''

def main():
    prefinal_sol = []
    data={}
    data["weights"] = []
    data["values"] = []
    data['layers']=layers

    for layer in layers:
        data['weights'].append(layer.height)
        data["values"].append(layer.cost)

    assert len(data["weights"]) == len(data["values"])
    data["num_items"] = len(data["weights"])
    data["all_items"] = range(data["num_items"])

    data["bin_capacities"]=[]
    for i in range(3,7):
        data["bin_capacities"].append(ULDs[i]["dimensions"][2])
    data["num_bins"] = len(data["bin_capacities"])
    data["all_bins"] = range(data["num_bins"])


    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        print("SCIP solver unavailable.")
        return

    # Variables.
    # x[i, b] = 1 if item i is packed in bin b.
    x = {}
    for i in data["all_items"]:
        for b in data["all_bins"]:
            x[i, b] = solver.BoolVar(f"x_{i}_{b}")

    # Constraints.
    # Each item is assigned to at most one bin.
    for i in data["all_items"]:
        solver.Add(sum(x[i, b] for b in data["all_bins"]) <= 1)

    # The amount packed in each bin cannot exceed its capacity.
    for b in data["all_bins"]:
        solver.Add(
            sum(x[i, b] * data["weights"][i] for i in data["all_items"])
            <= data["bin_capacities"][b]
        )

    # Objective.
    # Maximize total value of packed items.
    objective = solver.Objective()
    for i in data["all_items"]:
        for b in data["all_bins"]:
            objective.SetCoefficient(x[i, b], data["values"][i])
    objective.SetMaximization()

    print(f"Solving with {solver.SolverVersion()}")
    status = solver.Solve()

    selectedlayers = []
    if status == pywraplp.Solver.OPTIMAL:
        print(f"Total packed value: {objective.Value()}")
        total_weight = 0
        for b in data["all_bins"]:
            print(f"Bin {b}")
            bin_weight = 0
            bin_value = 0
            for i in data["all_items"]:
                if x[i, b].solution_value() > 0:
                    selectedlayers.append(i)
                    bin_weight
                    print(
                        f"Layer {i} sum of heights: {data['weights'][i]} total_cost_p200:"
                        f" {data['values'][i]}",
                        
                    )
                    for rect in data['layers'][i].packedlist:
                        prefinal_sol.append([rect.id,f'ULD-{b+3}',(rect.x,rect.y,bin_weight),(rect.x+rect.w,rect.y+rect.h,bin_weight+data["weights"][i])])
                    bin_weight += data["weights"][i]
                    bin_value += data["values"][i]
            print(f"Packed bin weight: {bin_weight}")
            print(f"Packed bin value: {bin_value}\n")
            total_weight += bin_weight
        print(f"Total packed weight: {total_weight}")
        print("FINALLY: ",prefinal_sol)
    else:
        print("The problem does not have an optimal solution.")
    


if __name__ == "__main__":
    main()

