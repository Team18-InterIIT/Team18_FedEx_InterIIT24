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
copy_containers = containers.copy()
packages_all = [Package(row) for row in pkg_list]
copy_packages_all = copy.deepcopy(packages_all)

# Define the number of packages (n) based on your problem data
n = len(packages_all)  # or whatever the actual number of packages is

# Fitness Calculation (based on packing stats and penalties)
def cal_fitness(population):
    fitness_list = []
    reordered_packages = []
    ulds = [[] for _ in range(len(population))]
    packages = [[] for _ in range(len(population))]
    for individual in range(len(population)):
        # Reorder the packages based on the solution (random key)
        # print(np.argsort(individual[:n])) -> different arrays => different orders => Problem somewhere below
        # packages_all = copy_packages_all
        packages_all = copy.deepcopy(copy_packages_all)
        reordered_packages.append([copy.deepcopy(packages_all[i]) for i in np.argsort(population[individual][:n])])
        # print(reordered_packages)
        # for pkg in reordered_packages:
        #     pkg = reset_corners

        # containers = copy_containers.copy()
        # containers = [copy_containers[i] for i in np.argsort(individual[len(copy_containers):])]
        reordered_containers = [copy_containers[i] for i in np.random.permutation(len(copy_containers))]
        # reordered_containers = sorted(copy_containers, key=lambda pkg: pkg.volume(), reverse=True)

        # Call DBLF algorithm to pack the packages into ULDs
        ulds[individual], packages[individual] = dblf_packing_algorithm(reordered_packages[individual], reordered_containers)
        
        # print(sorted(packages, key=lambda x: x.id)) -> Same coords and placed packages for all => Problem somewhere above
        # print(packages)

        # Check for unpacked priorities, not needed as price of priority is already inf inside
        # no_priority = False
        # for pkg in packages[individual]:
        #     if pkg.uld_id == 0 and pkg.is_priority:
        #         no_priority = True
        # if no_priority:
        #     fitness_list.append(float("inf"))
        #     continue

        # Sum of costs of unplaced packages
        unplaced_cost = sum(pkg.cost for pkg in packages[individual] if pkg.uld_id == 0)
        
        # print(len(packages))
        # for pkg in packages:
        #     print(pkg.uld_id)

        # Count the number of priority ULDs
        priority_uld_count = sum(1 for uld in ulds[individual] if uld.has_priority)
    
        # Calculate fitness as sum of unplaced cost + K * number of priority ULDs
        fitness_value = unplaced_cost + K * priority_uld_count
        fitness_list.append(fitness_value)

        # # Clearing
        # ulds.clear()
        # packages.clear()
        # reordered_packages.clear()

        # # Deleting
        # del ulds
        # del packages
        # del reordered_packages

        # Deleting the invidual
        # population = np.delete(population, 0, axis=0)

    # print(fitness_list)
    return fitness_list


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
    # print(type(population[0]))
    # population = np.empty(num_individuals, dtype = object)
    # for i in range(num_individuals):
    #     individual = np.random.uniform(low=0.0, high=1.0, size=(2 * n))
    #     # print(len(individual))
    #     population[i] = individual
    # print(len(population), len(population[0]))
    # diff = 0
    # for i, j in zip(population[0], population[1]):    
    #     diff += (i-j)
    # print(diff)

    # This makes it worse, it remains same in all runs
    # population = np.zeros((num_individuals, 2*n))
    # for i, j in zip(range(num_individuals), range(2*n)):
    #     np.random.seed(2*n*i + j)
    #     population[i][j] = np.random.uniform(low = 0.0, high = 1.0)
    
    # Calculate initial fitness for the population
    fitness_list = cal_fitness(population)
    
    # Track the best fitness found so far
    best_fitness = min(fitness_list)

    for gen in range(num_generations):
        # Partition population into elites and non-elites
        elites, non_elites = partition(population, fitness_list, num_elites)
        # population = np.random.uniform(low=0.0, high=1.0, size=(num_individuals, 2 * n))
        
        # # Create offspring through crossover
        # offspring_list = []
        # num_offspring = num_individuals - num_elites - num_mutants
        # for _ in range(num_offspring):
        #     parent1 = random.choice(elites)
        #     parent2 = random.choice(non_elites)
        #     offspring = crossover(parent1, parent2)
        #     offspring_list.append(offspring)

        offspring_list = mating(elites, non_elites, num_individuals, num_elites, num_mutants)
        
        # Generate mutants
        mutants = mutation(num_mutants)
        # print(mutants)
        
        # Create the next generation population
        population = np.concatenate((elites, mutants, offspring_list), axis=0)
        # Recalculate fitness for the new population
        fitness_list = cal_fitness(population)

        # Update best fitness value if a better individual is found
        # for fitness in fitness_list:
        #     if fitness < best_fitness:
        #         best_fitness = fitness

        best_fitness = min(fitness_list)

        # Print progress
        print(f"Generation {gen + 1}/{num_generations}, Best Fitness: {best_fitness}")

    # After the last generation, return the best individual
    best_individual = population[np.argmin(fitness_list)]
    return best_individual

# Run the Genetic Algorithm
best_individual = evolutionary_process(n, num_generations=100, num_individuals=50, num_elites=10, num_mutants=5)

# Use the best individual to pack the packages
reordered_packages = [packages_all[i] for i in np.argsort(best_individual[:n])]
final_ulds, unplaced = dblf_packing_algorithm(reordered_packages, containers)

# Example usage:
# Call this function after running the packing algorithm.
packing_fraction, total_packed_boxes = calculate_packing_stats(final_ulds)

print(f"Packing Fraction: {packing_fraction:.2%}")
print(f"Total Number of Boxes Packed: {total_packed_boxes}")

# Output results
# output_results_unique(final_ulds, packages_all)
visualize_packing(final_ulds)
