import parser
from entity import Package, ULD, Point
from environment import Environment

# The following import statement should be replaced with the correct import statement
from algorithm_interface import PackingAlgorithm as PackingAlgorithm
# For Example:
# from solvers.threeDBP_Pivoting import ThreeDBP_Pivoting as PackingAlgorithm

K = parser.get_K()
uld_list = parser.get_uld_list()
pkg_list = parser.get_pkg_list()

# Create ULD and Package objects
containers = [ULD(row) for row in uld_list]
packages = [Package(row) for row in pkg_list]

# env = Environment(K, uld_list, pkg_list)

# model = PackingAlgorithm()
# model.solve(env)

# env.plot()
# env.summary()

# from DBLF_priority_first import *

# # Step 2: Define algorithm parameters
# num_generations = 1000    # Number of generations
# num_individuals = 50      # Number of individuals in the population
# num_elites = 10           # Number of elites retained
# num_mutants = 5           # Number of mutants created per generation

# # Step 3: Run BRKGA algorithm
# best_solution = brkga(packages, containers, num_generations, num_individuals, num_elites, num_mutants)

# # Step 4: Decode the best solution (BPS and VBO)
# n = len(packages)
# decoded_best_solution = decode_random_key(best_solution, n, packages)

# # Step 5: Pack the best solution into ULDs using DBLF
# packed_ulds = dblf_packing_algorithm(decoded_best_solution, containers)

# # Step 6: Output results
# for uld in packed_ulds:
#     print(f"ULD {uld.id} packed with {len(uld.packages)} packages. Total weight: {uld.weight}/{uld.weight_limit}.")
#     for package in uld.packages:
#         print(f"  Package {package.id} placed at coordinates {package.coords}.")

# visualize_packing(containers)