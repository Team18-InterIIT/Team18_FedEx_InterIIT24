from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment

from ortools.linear_solver import pywraplp

class ORSolver(PackingAlgorithm):
    def solve(self, env: Environment):
        # first i will pack priority packages in as less 
        # ULDs as possible

        # percentage extra volume to give each ULD
        extra_vol = 0
        


        data = {}
        data["volumes"] = []
        data["weights"] = []
        data["pkg_id"] = []
        
        for package in env.packages:
            if package.is_priority:
                volume = package.volume()
                data["volumes"].append(volume)
                data["weights"].append(package.weight)
                data["pkg_id"].append(package.id)
            
        
        data["num_items"] = len(data["volumes"])
        data["all_items"] = range(data["num_items"])

        data["bin_capacities"] = []
        data["weight_capacities"] = []

        for uld in env.ULDs:
            factor = 1+extra_vol/100
            vol = int(uld.volume()*factor)
            data["bin_capacities"].append(vol)
            data["weight_capacities"].append(uld.weight_limit)
        
        data["num_bins"] = len(data["bin_capacities"])
        data["all_bins"] = range(data["num_bins"])

        solver = pywraplp.Solver.CreateSolver("SCIP")

        if solver is None:
            print("SCIP solver unavailable.")
            return
    
        #adding variables
        x = {}
        for i in data["all_items"]:
            for b in data["all_bins"]:
                x[i, b] = solver.BoolVar(f"x_{i}_{b}")
        
        for i in data["all_items"]:
            solver.Add(sum(x[i,b] for b in data["all_bins"]) == 1)

        

        y = {}
        for j in data["all_bins"]:
            y[j] = solver.IntVar(0,1, "y[%i]"%j)

        for b in data["all_bins"]:
            solver.Add(
                sum(x[i, b] * data["volumes"][i] for i in data["all_items"])
                <= y[b]*data["bin_capacities"][b]
            )
            solver.Add(
                sum(x[i,b]*data["weights"][i] for i in data["all_items"])
                <= y[b]*data["weight_capacities"][b]
            )
        

        
        # Maximize total value of packed items.
        solver.Minimize(solver.Sum([y[j] for j in data["all_bins"]]))


        status = solver.Solve()

        bin_weights_filled = [0]*(data["num_bins"])
        bin_volumes_filled = [0]*(data["num_bins"])

        #packed priority packages
        if status == pywraplp.Solver.OPTIMAL:
            for b in data["all_bins"]:
                print(f"Bin {b}")
                bin_weight = 0
                bin_volume = 0
                for i in data["all_items"]:
                    if x[i, b].solution_value() > 0:
                        print(
                            f"Item {i} volume: {data['volumes'][i]} weight:"
                            f" {data['weights'][i]}"
                        )
                        bin_weight += data["weights"][i]
                        bin_volume += data["volumes"][i]
                print(f"Packed bin volume: {bin_weight}")
                bin_weights_filled[b] = bin_weight
                bin_volumes_filled[b] = bin_volume
        else:
            print("The problem does not have an optimal solution.")
        print(bin_weights_filled)
        print(bin_volumes_filled)

        print("-----------------------------------------------------")
        print("packing economy packages")
        #packing economy packages
        data_2 = {}
        data_2["volumes"] = []
        data_2["weights"] = []
        data_2["costs"] = []
        data_2["pkg_id"] = []

        for package in env.packages:
            if not package.is_priority:
                volume = package.volume()
                data_2["volumes"].append(volume)
                data_2["weights"].append(package.weight)
                data_2["costs"].append(package.cost)
                data_2["pkg_id"].append(package.id)

        data_2["num_items"] = len(data["volumes"])
        data_2["all_items"] = range(data["num_items"])

        data_2["bin_volumes"] = []
        data_2["bin_weights"] = []

        for i, uld in enumerate(env.ULDs):

            factor = 1+extra_vol/100
            vol = int(uld.volume()*factor)
            volume_left = vol - bin_volumes_filled[i]
            data_2["bin_volumes"].append(volume_left)
            weight_left = uld.weight_limit - bin_weights_filled[i]
            data_2["bin_weights"].append(weight_left)
        
        data_2["num_bins"] = len(data_2["bin_volumes"])
        data_2["all_bins"] = range(data_2["num_bins"])

        solver2 = pywraplp.Solver.CreateSolver("SCIP")

        if solver2 is None:
            print("Fail :(")
            return
        
        x_2 = {}
        for i in data_2["all_items"]:
            for b in data_2["all_bins"]:
                x_2[i,b] = solver2.BoolVar(f"x_{i}_{b}")
        
        for i in data_2["all_items"]:
            solver2.Add(sum(x_2[i,b] for b in data_2["all_bins"]) <= 1)



        for b in data_2["all_bins"]:
            solver2.Add(
                sum(x_2[i, b] * data_2["volumes"][i] for i in data_2["all_items"])
                <= data_2["bin_volumes"][b]
            )
            solver2.Add(
                sum(x_2[i,b]*data_2["weights"][i] for i in data_2["all_items"])
                <= data_2["bin_weights"][b]
            )

        objective = solver2.Objective()
        for i in data_2["all_items"]:
            for b in data_2["all_bins"]:
                objective.SetCoefficient(x_2[i, b], data_2["costs"][i])
        objective.SetMaximization()

        status=solver2.Solve()
        N_priority_packages = data["num_items"]


        f = open("data.txt", "w")
        if status == pywraplp.Solver.OPTIMAL:
            for b in data_2["all_bins"]:
                print(f"Bin {b}")
                f.write(f"Bin {b}\n")
                for i in data["all_items"]:
                    if x[i, b].solution_value()>0:
                        print(
                            f"Item {data['pkg_id'][i]} volume: {data['volumes'][i]} weight: "
                            f" {data['weights'][i]}"
                        )
                        f.write(
                            f"Item {data['pkg_id'][i]} volume: {data['volumes'][i]} weight: {data['weights'][i]}\n"
                        )
                for i in data_2["all_items"]:
                    if x_2[i, b].solution_value()>0:
                        print(
                            f"Item {data_2['pkg_id'][i]} volume: {data_2['volumes'][i]} weight: "
                            f" {data_2['weights'][i]}"
                        )
                        f.write(
                            f"Item {data_2['pkg_id'][i]} volume: {data_2['volumes'][i]} weight: {data_2['weights'][i]}\n"
                        )
        f.close()

