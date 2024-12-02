import sys

import parser
from environment import Environment

# The following import statement should be replaced with the correct import statement
from algorithm_interface import PackingAlgorithm as PackingAlgorithm

# For Example:
from solvers.threeDBP_Pivoting import ThreeDBP_Pivoting as PackingAlgorithm

if len(sys.argv) == 2:
    test_file = sys.argv[1]
else:
    test_file = "test/Challenge_FedEx.txt"

parser = parser.Parser(test_file)
K = parser.get_K()
uld_list = parser.get_uld_list()
pkg_list = parser.get_pkg_list()

env = Environment(K, uld_list, pkg_list)

model = PackingAlgorithm()

model.solve(env)
# To read from a solution file, use the following line instead of the above line
# env.read(file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}")

env.summary()
# env.plot()
env.animate()
env.write(
    file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}"
)
