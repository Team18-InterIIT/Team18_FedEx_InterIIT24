import parser
from entity import Package, ULD, Dim
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

from solvers import genetic
env = Environment(K, uld_list, pkg_list)

# genetic.solve(env)

# Set an initial default solution
best_solution = genetic.initialize_population(1, packages, containers)[0]  # First random chromosome
best_fitness = 0

# Run the GA
best_solution = genetic.genetic_algorithm(K, containers, packages, pop_size=50, generations= int(10 * len(pkg_list)), mutation_rate=0.01)

# Generate packing solution for the best chromosome
bps, cls = best_solution
packing_solution, unplaced_packages = genetic.best_match_placement(bps, cls)

fitness_function_result = genetic.fitness_function((bps, cls), K)

# Output the solution to a file
genetic.print_solution_statistics(
    packing_solution,
    unplaced_packages,
    containers,
    packages,  # All packages
    fitness_function_result,
    bps,
    output_file="solution_output.txt"
)

# Calculate and print packing fraction
if packing_solution:
    packed_volume = sum(box.volume() for box, _, _, _ in packing_solution)
    total_container_volume = sum(container.volume() for container in containers)
    packing_fraction = packed_volume / total_container_volume if total_container_volume > 0 else 0
    print(f"Packing Fraction: {packing_fraction:.2%}")

if packing_solution is not None:
    genetic.plot_packing_solution_subplots(packing_solution, containers)
else:
    print("No feasible packing solution found.")

# genetic.output_placement_to_file(packing_solution, bps, output_file="placement_output.txt")
# print("Placement solution written to 'placement_output.txt'")
# env.plot()
# env.summary()

