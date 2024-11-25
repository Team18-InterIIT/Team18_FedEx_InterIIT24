from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment

from ortools.linear_solver import pywraplp

class ORSolver(PackingAlgorithm):
    def solve(self, env: Environment):
        print("hi")
        data = {}
        data["volumes"] = []
        data["values"] = []
        
        for package in env.packages:
            volume = package.volume()
            data["volumes"].append(volume)

            if package.is_priority:
                data["values"].append(100)
            else:
                data["values"].append(1)
        
        assert len(data["volumes"]) == len(data["values"])
        data["num_items"] = len(data["volumes"])
        data["all_items"] = range(data["num_items"])

        data["bin_capacities"] = []

        for uld in env.ULDs:
            data["bin_capacities"].append(uld.volume())
        
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
            solver.Add(sum(x[i,b] for b in data["all_bins"]) <= 1)

        for b in data["all_bins"]:
            solver.Add(
                sum(x[i, b] * data["volumes"][i] for i in data["all_items"])
                <= data["bin_capacities"][b]
            )
        
        # Maximize total value of packed items.
        objective = solver.Objective()
        for i in data["all_items"]:
            for b in data["all_bins"]:
                objective.SetCoefficient(x[i, b], data["values"][i])
        objective.SetMaximization()
        status = solver.Solve()
       

        with open("model.lp", "w") as f:
            f.write(solver.ExportModelAsLpFormat(False))

            
        if status == pywraplp.Solver.OPTIMAL:
            print(f"Total packed value: {objective.Value()}")
            total_weight = 0
            for b in data["all_bins"]:
                print(f"Bin {b}")
                bin_weight = 0
                bin_value = 0
                for i in data["all_items"]:
                    if x[i, b].solution_value() > 0:
                        print(
                            f"Item {i} weight: {data['volumes'][i]} value:"
                            f" {data['values'][i]}"
                        )
                        bin_weight += data["volumes"][i]
                        bin_value += data["values"][i]
                print(f"Packed bin weight: {bin_weight}")
                print(f"Packed bin value: {bin_value}\n")
                total_weight += bin_weight
            print(f"Total packed weight: {total_weight}")
        else:
            print("The problem does not have an optimal solution.")


        print("hi")