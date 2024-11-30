import sys
import importlib
import parser
from environment import Environment

# Ensure we have both test file and solver name arguments
if len(sys.argv) != 3:
    sys.exit(1)

test_file = sys.argv[1]
solver_module_name = sys.argv[2]

# Dynamically import the solver module
try:
    solver_module = importlib.import_module(solver_module_name)
    print(solver_module)
    PackingAlgorithm = solver_module.Algorithm
except ModuleNotFoundError:
    print(f"Error: Solver module '{solver_module_name}' not found.")
    sys.exit(1)

# Parse the test file
parser = parser.Parser(test_file)
K = parser.get_K()
uld_list = parser.get_uld_list()
pkg_list = parser.get_pkg_list()

env = Environment(K, uld_list, pkg_list)

# Instantiate the algorithm and solve the problem
model = PackingAlgorithm()
model.solve(env)

# Save the results to a solution file
print("Printing Summary")
env.summary()
# env.plot()
# env.animate()
env.write(
    file_path=f"solutions/{solver_module_name}/{test_file.split('/')[-1]}"
)
