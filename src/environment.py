import parser
import itertools
import random
from main import Package, ULD, Dim

# Initialize data
K = parser.get_K()
uld_list = parser.get_uld_list()
pkg_list = parser.get_pkg_list()

# Create ULD and Package objects
containers = [ULD(row) for row in uld_list]
packages = [Package(row) for row in pkg_list]

# EMS: Empty Maximal Spaces
class EMS:
    def __init__(self, x_min, y_min, z_min, x_max, y_max, z_max):
        self.min_coords = (x_min, y_min, z_min)
        self.max_coords = (x_max, y_max, z_max)

    def get_dimensions(self):
        return (
            self.max_coords[0] - self.min_coords[0],
            self.max_coords[1] - self.min_coords[1],
            self.max_coords[2] - self.min_coords[2],
        )

    def __repr__(self):
        return f"EMS: {self.min_coords} -> {self.max_coords}"


# Initialize population
def initialize_population(pop_size, packages, containers):
    population = []
    for _ in range(pop_size):
        bps = random.sample(packages, len(packages))
        cls = random.sample(containers, len(containers))
        population.append((bps, cls))
    return population


# Update EMS for a container after placing a box
def update_ems(container, box, ems, orientation, placement_coords):
    # Remove the used EMS and add new EMSs based on the placement
    x, y, z = placement_coords
    box_dims = orientation

    new_ems_list = []
    for space in ems:
        if not is_overlapping(space, box_dims, placement_coords):
            new_ems_list.append(space)
        else:
            # Generate new EMS regions
            new_ems_list.extend(generate_new_ems(space, box_dims, placement_coords))

    # Eliminate redundant EMS regions
    return eliminate_redundant_ems(new_ems_list)


def is_overlapping(space, box_dims, placement_coords):
    """
    Check if a box placed at `placement_coords` overlaps with the given EMS.
    """
    box_min = placement_coords
    box_max = tuple(placement_coords[i] + box_dims[i] for i in range(3))
    space_min = space.min_coords
    space_max = space.max_coords

    # Check for overlap in all three dimensions
    for i in range(3):
        if box_max[i] <= space_min[i] or box_min[i] >= space_max[i]:
            return False  # No overlap in this dimension

    return True  # Overlap exists


def generate_new_ems(space, box_dims, placement_coords):
    """
    Generate new EMS regions when a box is placed in a space.
    """
    new_ems_list = []
    box_min = placement_coords
    box_max = tuple(placement_coords[i] + box_dims[i] for i in range(3))
    space_min = space.min_coords
    space_max = space.max_coords

    # Generate new EMS to the right of the box
    if box_max[0] < space_max[0]:
        new_ems_list.append(
            EMS(box_max[0], space_min[1], space_min[2], space_max[0], space_max[1], space_max[2])
        )

    # Generate new EMS above the box
    if box_max[1] < space_max[1]:
        new_ems_list.append(
            EMS(space_min[0], box_max[1], space_min[2], space_max[0], space_max[1], space_max[2])
        )

    # Generate new EMS in front of the box
    if box_max[2] < space_max[2]:
        new_ems_list.append(
            EMS(space_min[0], space_min[1], box_max[2], space_max[0], space_max[1], space_max[2])
        )

    return new_ems_list


def eliminate_redundant_ems(ems_list):
    """
    Remove overlapping or fully contained EMS regions.
    """
    valid_ems = []

    for i, ems1 in enumerate(ems_list):
        is_redundant = False
        for j, ems2 in enumerate(ems_list):
            if i != j and is_contained(ems1, ems2):
                is_redundant = True
                break

        if not is_redundant:
            valid_ems.append(ems1)

    return valid_ems


def is_contained(ems1, ems2):
    """
    Check if `ems1` is fully contained within `ems2`.
    """
    for i in range(3):
        if ems1.min_coords[i] < ems2.min_coords[i] or ems1.max_coords[i] > ems2.max_coords[i]:
            return False

    return True

def select_best_placement(bps, ems_list, k_b=5, k_e=5):
    """
    Select the best placement for the next box from the first `k_b` boxes and `k_e` EMS regions.
    """
    best_placement = None
    max_fill_ratio = 0
    min_margin = (float("inf"), float("inf"), float("inf"))

    for i, box in enumerate(bps[:k_b]):
        for j, space in enumerate(ems_list[:k_e]):
            for orientation in itertools.permutations([box.dim.l, box.dim.w, box.dim.h]):
                if can_fit(space, orientation):
                    # Calculate fill ratio and margin
                    box_volume = box.get_volume()
                    space_volume = space.get_dimensions()[0] * space.get_dimensions()[1] * space.get_dimensions()[2]
                    fill_ratio = box_volume / space_volume

                    placement_coords, margin = find_placement_coords(space, orientation)

                    # Update best placement based on fill ratio and margin
                    if (fill_ratio > max_fill_ratio) or (fill_ratio == max_fill_ratio and margin < min_margin):
                        best_placement = (box, space, orientation, placement_coords)
                        max_fill_ratio = fill_ratio
                        min_margin = margin

    return best_placement


# Placement strategy
def best_match_placement(bps, cls):
    """
    Implements the heuristic packing strategy to find the best placement for boxes in containers.
    """
    ems_dict = {c: [EMS(0, 0, 0, c.dim.l, c.dim.w, c.dim.h)] for c in cls}  # EMS per container
    packing_solution = []  # To store the placement solution

    for box in bps:
        box_placed = False

        # Iterate through opened containers
        for container in cls:
            ems_list = ems_dict[container]  # Get the EMS list for the current container

            # Select the best placement using k_b boxes and k_e EMS regions
            best_placement = select_best_placement([box], ems_list)

            if best_placement:
                # Extract placement details
                selected_box, selected_space, orientation, placement_coords = best_placement

                # Place the box in the container
                packing_solution.append((selected_box, container, placement_coords, orientation))

                # Update EMS for the container
                ems_dict[container] = update_ems(container, selected_box, ems_list, orientation, placement_coords)

                # Mark box as placed and exit loop
                box_placed = True
                break

        # If the box cannot be placed in opened containers, return None (no feasible solution)
        if not box_placed:
            return None

    return packing_solution



def can_fit(space, box_dims):
    # Check if the box fits in the EMS
    return all(d <= s for d, s in zip(box_dims, space.get_dimensions()))

# def can_fit(space, box_dims):
#     """
#     Check if the box can fit into the EMS in the given orientation.
#     """
#     space_dims = space.get_dimensions()
#     for i in range(3):
#         if box_dims[i] > space_dims[i]:
#             print(f"Box {box_dims} cannot fit in space {space_dims}.")
#             return False
#     return True



def find_placement_coords(space, box_dims):
    """
    Find the best coordinates for placing the box in the EMS.
    Returns the placement coordinates and the margin for priority.
    """
    space_min = space.min_coords
    space_dims = space.get_dimensions()

    # Calculate the margin
    margin = tuple(space_dims[i] - box_dims[i] for i in range(3))

    return space_min, margin  # Ensure two values are returned



# Fitness function
def fitness_function(chromosome):
    """
    Evaluate the fitness of a chromosome.
    Fitness is determined by the fill ratio, penalties for unplaced boxes, and weight constraints.
    """
    bps, cls = chromosome  # Extract Box Packing Sequence (BPS) and Container Loading Sequence (CLS)

    # Apply heuristic packing strategy to get the packing solution
    packing_solution = best_match_placement(bps, cls)

    if packing_solution is None:
        # If no feasible packing solution, fitness is 0
        return 0

    # Calculate the total packed volume
    packed_volume = sum(box.get_volume() for box, *_ in packing_solution)

    # Calculate the total container volume
    total_container_volume = sum(container.get_volume() for container in cls)

    # Calculate the fill ratio
    fill_ratio = packed_volume / total_container_volume

    # Check for unplaced boxes
    unplaced_boxes = len(bps) - len(packing_solution)

    # Calculate penalties
    penalty_unplaced_boxes = unplaced_boxes * 10  # Arbitrary penalty per unplaced box
    penalty_overweight = 0

    # Check for weight violations in containers
    for container in cls:
        total_weight = sum(box.weight for box, cont, *_ in packing_solution if cont == container)
        if total_weight > container.weight_limit:
            penalty_overweight += (total_weight - container.weight_limit) * 5  # Arbitrary penalty per excess weight

    # Calculate the final fitness
    fitness = fill_ratio - penalty_unplaced_boxes - penalty_overweight
    return max(fitness, 0)  # Ensure fitness is non-negative



# Selection
def select_parents(population, fitness_scores, tournament_size=2, prob_t=0.8):
    """
    Select parents for the next generation using tournament selection.
    """
    parents = []
    for _ in range(len(population)):
        # Randomly select chromosomes for the tournament
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament = [(fitness_scores[i], population[i]) for i in tournament_indices]

        # Sort by fitness (higher is better)
        tournament.sort(key=lambda x: x[0], reverse=True)

        # Select the best with probability `prob_t`, otherwise the second-best
        if random.random() < prob_t:
            parents.append(tournament[0][1])
        else:
            parents.append(tournament[1][1])

    return parents



# Crossover
def crossover(parent1, parent2):
    """
    Perform Partially Matched Crossover (PMX) on BPS and CLS.
    """
    bps1, cls1 = parent1
    bps2, cls2 = parent2

    # Crossover for BPS
    child_bps = pmx_crossover(bps1, bps2)

    # Crossover for CLS
    child_cls = pmx_crossover(cls1, cls2)

    return (child_bps, child_cls)


def pmx_crossover(seq1, seq2):
    """
    Perform PMX crossover on two sequences (e.g., BPS or CLS).
    """
    size = len(seq1)
    child = [-1] * size

    # Select two random crossover points
    point1, point2 = sorted(random.sample(range(size), 2))

    # Copy the segment between the points from the first parent
    child[point1:point2] = seq1[point1:point2]

    # Resolve conflicts using the second parent
    for i in range(point1, point2):
        if seq2[i] not in child:
            # Find a position to insert the element from the second parent
            pos = i
            while child[pos] != -1:
                pos = seq2.index(seq1[pos])
            child[pos] = seq2[i]

    # Fill the remaining positions with elements from the second parent
    for i in range(size):
        if child[i] == -1:
            child[i] = seq2[i]

    return child



# Mutation
def mutate(chromosome, mutation_rate=0.1):
    """
    Apply mutation to the chromosome (BPS and CLS) with a given probability.
    """
    bps, cls = chromosome

    # Mutate BPS
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(bps)), 2)
        bps[i], bps[j] = bps[j], bps[i]

    # Mutate CLS
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(cls)), 2)
        cls[i], cls[j] = cls[j], cls[i]

    return (bps, cls)



# Genetic Algorithm
def genetic_algorithm(pop_size, generations, mutation_rate=0.1):
    """
    Run the Genetic Algorithm to optimize the packing solution.
    """
    # Step 1: Initialize population
    population = initialize_population(pop_size, packages, containers)

    for generation in range(generations):
        # Step 2: Evaluate fitness
        fitness_scores = [fitness_function(chromosome) for chromosome in population]

        # Step 3: Selection
        parents = select_parents(population, fitness_scores)

        # Step 4: Crossover
        next_generation = []
        for i in range(0, len(parents), 2):
            parent1 = parents[i]
            parent2 = parents[i + 1 if i + 1 < len(parents) else 0]
            child1 = crossover(parent1, parent2)
            child2 = crossover(parent2, parent1)
            next_generation.extend([child1, child2])

        # Step 5: Mutation
        next_generation = [mutate(chromosome, mutation_rate) for chromosome in next_generation]

        # Step 6: Replace old population with the new one
        population = next_generation[:pop_size]

        # Debug: Print the best fitness in the current generation
        max_fitness = max(fitness_scores)
        print(f"Generation {generation + 1}: Best Fitness = {max_fitness}")

    # Step 7: Return the best solution
    fitness_scores = [fitness_function(chromosome) for chromosome in population]
    best_index = fitness_scores.index(max(fitness_scores))
    return population[best_index]

def output_placement_to_file(packing_solution, bps, output_file="placement_output.txt"):
    """
    Write the packing solution to a file in the specified format.
    
    Format:
    Package-ID,ULD-ID,x0,y0,z0,x1,y1,z1
    If a package is not placed, ULD-ID is 'NONE', and coordinates are -1,-1,-1,-1,-1,-1.
    """

    if packing_solution is None:
        print("Error: No feasible packing solution found.")
        with open(output_file, "w") as file:
            for box in bps:
                file.write(f"{box.id},NONE,-1,-1,-1,-1,-1,-1\n")
    else:
        with open(output_file, "w") as file:
            placed_packages = {box.id for box, *_ in packing_solution}

        # Write details for placed packages
        for box, container, coords, orientation in packing_solution:
            x0, y0, z0 = coords
            x1 = x0 + orientation[0]
            y1 = y0 + orientation[1]
            z1 = z0 + orientation[2]
            file.write(f"{box.id},{container.id},{x0},{y0},{z0},{x1},{y1},{z1}\n")

        # Write details for unplaced packages
        for box in bps:
            if box.id not in placed_packages:
                file.write(f"{box.id},NONE,-1,-1,-1,-1,-1,-1\n")


# Run the GA
best_solution = genetic_algorithm(pop_size=50, generations=100, mutation_rate=0.1)

# Generate packing solution for the best chromosome
bps, cls = best_solution
packing_solution = best_match_placement(bps, cls)

# Output the solution to a file
output_placement_to_file(packing_solution, bps, output_file="placement_output.txt")
print("Placement solution written to 'placement_output.txt'")
