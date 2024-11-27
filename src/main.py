import parser
from environment import Environment

# The following import statement should be replaced with the correct import statement
from algorithm_interface import PackingAlgorithm as PackingAlgorithm
# For Example:
# from solvers.threeDBP_Pivoting import ThreeDBP_Pivoting as PackingAlgorithm

# K = parser.get_K()
# uld_list = parser.get_uld_list()
# pkg_list = parser.get_pkg_list()

env = Environment(K, uld_list, pkg_list)

model = PackingAlgorithm()
model.solve(env)

env.plot()
env.summary()
