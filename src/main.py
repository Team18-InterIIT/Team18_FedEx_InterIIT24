import sys

import parser
from environment import Environment

# The following import statement should be replaced with the correct import statement
from algorithm_interface import PackingAlgorithm as PackingAlgorithm

# For Example:
from solvers.hybrid import Hybrid as PackingAlgorithm

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

model.solve(env, search="normal", layering=True)
# To read from a solution file, use the following line instead of the above line
# env.read(file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}")

env.summary()
env.plot(stress_plot=False)
# env.animate()
# env.simulate()
env.write(
    file_path=f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}"
)

# uncomment the below line to pickle the environment
# env.save(str(PackingAlgorithm.__name__))
