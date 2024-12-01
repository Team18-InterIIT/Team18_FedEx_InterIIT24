import numpy as np
import random
import copy
import parser
from entity import ULD, Package, Point
from DBLF_priority_first import dblf_packing_algorithm, calculate_packing_stats, visualize_packing #, output_results_unique

# Initialize data
K = parser.get_K()
uld_list = parser.get_uld_list()
pkg_list = parser.get_pkg_list()

# Create ULD and Package objects
containers = [ULD(row) for row in uld_list]
# copy_containers = copy.deepcopy(containers)
packages_all = [Package(row) for row in pkg_list]
# copy_packages_all = copy.deepcopy(packages_all)

# Define the number of packages (n) based on your problem data
n = len(pkg_list)  # or whatever the actual number of packages is

def reset(containers, packages):
    for pkg in packages:
        pkg.__init__(pkg_list[pkg.id-1])
    for uld in containers:
        uld.__init__(uld_list[uld.id-1])
    return containers, packages

# Fitness Calculation (based on packing stats and penalties)
def cal_fitness(individual, containers, packages_all, reset_corner, perturbation_rate=0.1):
    # Reorder the containers based on a random permutation
    # containers = [ULD(row) for row in uld_list]
    # reordered_containers = [copy.deepcopy(copy_containers[i]) for i in np.random.permutation(len(copy_containers))]

    # containers, packages_all = reset(containers, packages_all)
    # for pkg in packages_all:
    #     pkg.uld_id = 0
    #     pkg.corners = reset_corner
    # for uld in containers:
    #     uld.has_priority = False
    #     uld.weight = 0
    #     uld.packages = list()

    containers, packages_all = reset(containers, packages_all)

    # reordered_containers = [containers[i] for i in np.random.permutation(len(containers))] 
    reordered_containers = sorted(containers, key=lambda pkg: pkg.volume(), reverse=True)
    # Create packages again (or use the global copy of the packages)
    # packages_all = [Package(row) for row in pkg_list]

    # Reorder the packages based on the random key from individual[:n]
    # reordered_packages = [packages_all[i] for i in np.argsort(individual[:n])]

    reordered_packages = perturb_order(packages_all, perturbation_rate)

    # Call DBLF algorithm to pack the packages into ULDs
    ulds, packages = dblf_packing_algorithm(reordered_packages, reordered_containers)

    # Sum of costs of unplaced packages
    unplaced_cost = sum(pkg.cost for pkg in packages if pkg.uld_id == 0)

    # Count the number of priority ULDs
    priority_uld_count = sum(1 for uld in ulds if uld.has_priority)

    # Calculate fitness as sum of unplaced cost + K * number of priority ULDs
    fitness_value = unplaced_cost + K * priority_uld_count

    # print(packages)
    return fitness_value

def perturb_order(packages, perturbation_rate=0.1):
    # packages is a list of sorted packages in descending order of volume
    n = len(packages)
    num_swaps = int(perturbation_rate * n)  # Determine how many swaps to make

    # Perform random swaps in the sorted list
    for _ in range(num_swaps):
        i, j = random.sample(range(n), 2)  # Randomly select two distinct indices
        packages[i], packages[j] = packages[j], packages[i]  # Swap them

    return packages


# Elite and Non-Elite Partitioning
def partition(population, fitness_list, num_elites):
    sorted_indexs = np.argsort(fitness_list)
    return population[sorted_indexs[:num_elites]], population[sorted_indexs[num_elites:]]

# Crossover Function
def crossover(elite, non_elite):
    offspring = [0] * (2 * n)  # offspring has 2*n genes (for 2*n-length random keys)
    for i in range(2 * n):
        if np.random.uniform(low=0.0, high=1.0) < 0.7:  # eliteCProb = 0.7
            offspring[i] = elite[i]
        else:
            offspring[i] = non_elite[i]
    return offspring

def mating(elites, non_elites, num_individuals, num_elites, num_mutants):
    offspring_list = []
    num_offspring = num_individuals - num_elites - num_mutants
    for i in range(num_offspring):
        # biased selection for parents: 1 elite & 1 non_elite
        offspring = crossover(random.choice(elites), random.choice(non_elites))
        offspring_list.append(offspring)
    return offspring_list

# Mutation Function
def mutation(num_mutants):
    return np.random.uniform(low=0.0, high=1.0, size=(num_mutants, 2 * n))

# Main Evolutionary Process
def evolutionary_process(n, num_generations, num_individuals, num_elites, num_mutants):
    # Initialize population: each individual is a 2*n random vector
    population = np.random.uniform(low=0.0, high=1.0, size=(num_individuals, 2 * n))
    
    packages_all = [Package(row) for row in pkg_list]
    containers = [ULD(row) for row in uld_list]

    packages_priority = [pkg for pkg in packages_all if pkg.is_priority]
    packages_economy = [pkg for pkg in packages_all if not pkg.is_priority]

    packages_prioity_sorted = sorted(
        packages_priority, key=lambda pkg: pkg.volume(), reverse=True
    )
    packages_economy_sorted = sorted(
        packages_economy, key=lambda pkg: pkg.cost, reverse=True
    )

    packages_all = packages_prioity_sorted + packages_economy_sorted

    reset_corner = Point(-1, -1, -1)

    # packages_all = sorted(
    #     packages_all, key=lambda pkg: pkg.volume(), reverse=True
    # )

    # Calculate initial fitness for the population
    fitness_list = []
    for indiv in population:
        fitness_list.append(cal_fitness(population, containers, packages_all, reset_corner, 0))
    
    # Track the best fitness found so far
    # best_fitness = min(fitness_list)
    # Update best fitness value if a better individual is found
    best_fitness = 2*K*len(containers)
    for fitness in fitness_list:
        if fitness < best_fitness:
            best_fitness = fitness

    for gen in range(num_generations):
        # Partition population into elites and non-elites
        elites, non_elites = partition(population, fitness_list, num_elites)

        offspring_list = mating(elites, non_elites, num_individuals, num_elites, num_mutants)
        
        # Generate mutants
        mutants = mutation(num_mutants)
        
        # Create the next generation population
        population = np.concatenate((elites, mutants, offspring_list), axis=0)
        # Recalculate fitness for the new population
        fitness_list = []
        for indiv in population:
            fitness_list.append(cal_fitness(indiv, containers, packages_all, reset_corner, 0.2))

        # Update best fitness value if a better individual is found
        for fitness in fitness_list:
            if fitness < best_fitness:
                best_fitness = fitness

        # best_fitness = min(fitness_list)

        # Print progress
        print(f"Generation {gen + 1}/{num_generations}, Best Fitness: {best_fitness}")

    # After the last generation, return the best individual
    best_individual = population[np.argmin(fitness_list)]

    # Use the best individual to pack the packages
    reordered_packages = [packages_all[i] for i in np.argsort(best_individual[:n])]
    final_ulds, unplaced = dblf_packing_algorithm(reordered_packages, containers)    

    # Call this function after running the packing algorithm.
    packing_fraction, total_packed_boxes = calculate_packing_stats(final_ulds)

    print(f"Packing Fraction: {packing_fraction:.2%}")
    print(f"Total Number of Boxes Packed: {total_packed_boxes}")

    visualize_packing(final_ulds)


# # Run the Genetic Algorithm
# best_individual = evolutionary_process(n, num_generations=100, num_individuals=50, num_elites=10, num_mutants=5)

# # Use the best individual to pack the packages
# reordered_packages = [packages_all[i] for i in np.argsort(best_individual[:n])]
# final_ulds, unplaced = dblf_packing_algorithm(reordered_packages, containers)

# # Example usage:
# # Call this function after running the packing algorithm.
# packing_fraction, total_packed_boxes = calculate_packing_stats(final_ulds)

# print(f"Packing Fraction: {packing_fraction:.2%}")
# print(f"Total Number of Boxes Packed: {total_packed_boxes}")

# # Output results
# # output_results_unique(final_ulds, packages_all)
# visualize_packing(final_ulds)

n = len(pkg_list)
num_generations = 50
num_individuals = 30
num_elites = int(0.04 * num_individuals)
num_mutants = int(0.4 * num_individuals)

evolutionary_process(n, num_generations, num_individuals, num_elites, num_mutants)