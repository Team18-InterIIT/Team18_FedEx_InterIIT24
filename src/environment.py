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
# def initialize_population(pop_size, packages, containers):
#     population = []
#     for _ in range(pop_size):
#         bps = random.sample(packages, len(packages))
#         cls = random.sample(containers, len(containers))
#         population.append((bps, cls))
#     return population


# Initialize population
def initialize_population(pop_size, packages, containers):
    population = []
    # Create a structured chromosome by sorting packages
    # Sort by volume (or another criterion) in descending order
    sorted_packages = sorted(packages, key=lambda pkg: pkg.get_volume(), reverse=True)

    # Add a chromosome with sorted packages
    population.append((sorted_packages, random.sample(containers, len(containers))))

    # Add remaining chromosomes randomly
    for _ in range(pop_size - 1):
        bps = random.sample(packages, len(packages))  # Randomly shuffle packages
        cls = random.sample(containers, len(containers))  # Randomly shuffle containers
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
            EMS(
                box_max[0],
                space_min[1],
                space_min[2],
                space_max[0],
                space_max[1],
                space_max[2],
            )
        )

    # Generate new EMS above the box
    if box_max[1] < space_max[1]:
        new_ems_list.append(
            EMS(
                space_min[0],
                box_max[1],
                space_min[2],
                space_max[0],
                space_max[1],
                space_max[2],
            )
        )

    # Generate new EMS in front of the box
    if box_max[2] < space_max[2]:
        new_ems_list.append(
            EMS(
                space_min[0],
                space_min[1],
                box_max[2],
                space_max[0],
                space_max[1],
                space_max[2],
            )
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
        if (
            ems1.min_coords[i] < ems2.min_coords[i]
            or ems1.max_coords[i] > ems2.max_coords[i]
        ):
            return False

    return True


# def select_best_placement(bps, ems_list, k_b=3, k_e=3):
#     """
#     Select the best placement for the next box from the first `k_b` boxes and `k_e` EMS regions.
#     """
#     best_placement = None
#     max_fill_ratio = 0
#     min_margin = (float("inf"), float("inf"), float("inf"))

#     for i, box in enumerate(bps[:k_b]):
#         for j, space in enumerate(ems_list[:k_e]):
#             for orientation in itertools.permutations([box.dim.l, box.dim.w, box.dim.h]):
#                 if can_fit(space, orientation):
#                     # Calculate fill ratio and margin
#                     box_volume = box.get_volume()
#                     space_volume = space.get_dimensions()[0] * space.get_dimensions()[1] * space.get_dimensions()[2]
#                     fill_ratio = box_volume / space_volume

#                     placement_coords, margin = find_placement_coords(space, orientation)

#                     # Update best placement based on fill ratio and margin
#                     if (fill_ratio > max_fill_ratio) or (fill_ratio == max_fill_ratio and margin < min_margin):
#                         best_placement = (box, space, orientation, placement_coords)
#                         max_fill_ratio = fill_ratio
#                         min_margin = margin

#     return best_placement


def select_best_placement(bps, ems_list, k_b=3, k_e=3):
    """
    Select the best placement for the next box from the first `k_b` boxes and `k_e` EMS regions.
    """
    if not bps or not ems_list:
        # print("No boxes or EMS regions to evaluate.")
        return None

    k_b = 3
    k_e = 3

    best_placement = None
    max_fill_ratio = 0
    min_margin = (float("inf"), float("inf"), float("inf"))

    for i, box in enumerate(bps[:k_b]):
        for j, space in enumerate(ems_list[:k_e]):
            for orientation in set(
                itertools.permutations([box.dim.l, box.dim.w, box.dim.h])
            ):
                if not can_fit(space, orientation):
                    continue

                # Calculate fill ratio and margin
                box_volume = box.get_volume()
                space_volume = (
                    space.get_dimensions()[0]
                    * space.get_dimensions()[1]
                    * space.get_dimensions()[2]
                )
                fill_ratio = box_volume / space_volume

                placement_coords, margin = find_placement_coords(space, orientation)
                if placement_coords is None or margin is None:
                    continue  # Skip invalid placement

                if not isinstance(margin, tuple) or len(margin) != 3:
                    continue  # Skip invalid margin

                # Update best placement based on fill ratio and margin
                if (fill_ratio > max_fill_ratio) or (
                    fill_ratio == max_fill_ratio and margin < min_margin
                ):
                    best_placement = (box, space, orientation, placement_coords)
                    max_fill_ratio = fill_ratio
                    min_margin = margin

    return best_placement


# Placement strategy
# def best_match_placement(bps, cls):
#     """
#     Implements the heuristic packing strategy to find the best placement for boxes in containers.
#     """
#     ems_dict = {c: [EMS(0, 0, 0, c.dim.l, c.dim.w, c.dim.h)] for c in cls}  # EMS per container
#     packing_solution = []  # To store the placement solution

#     for box in bps:
#         box_placed = False

#         # Iterate through opened containers
#         for container in cls:
#             ems_list = ems_dict[container]  # Get the EMS list for the current container

#             # Select the best placement using k_b boxes and k_e EMS regions
#             best_placement = select_best_placement([box], ems_list)

#             if best_placement:
#                 # Extract placement details
#                 selected_box, selected_space, orientation, placement_coords = best_placement

#                 # Place the box in the container
#                 packing_solution.append((selected_box, container, placement_coords, orientation))

#                 # Update EMS for the container
#                 ems_dict[container] = update_ems(container, selected_box, ems_list, orientation, placement_coords)

#                 # Mark box as placed and exit loop
#                 box_placed = True
#                 break

#         # If the box cannot be placed in opened containers, return None (no feasible solution)
#         if not box_placed:
#             return None

#     return packing_solution


def best_match_placement(bps, cls):
    """
    Implements the heuristic packing strategy to fit as many packages as possible.
    Returns both placed and unplaced packages.
    """
    ems_dict = {c: [EMS(0, 0, 0, c.dim.l, c.dim.w, c.dim.h)] for c in cls}
    packing_solution = []
    unplaced_packages = []

    for box in bps:
        box_placed = False

        for container in cls:
            ems_list = ems_dict[container]
            best_placement = select_best_placement([box], ems_list, container)

            if best_placement:
                selected_box, selected_space, orientation, placement_coords = (
                    best_placement
                )
                packing_solution.append(
                    (selected_box, container, placement_coords, orientation)
                )
                ems_dict[container] = update_ems(
                    container, selected_box, ems_list, orientation, placement_coords
                )
                box_placed = True
                break

        if not box_placed:
            unplaced_packages.append(box)

    return packing_solution, unplaced_packages


def can_fit(space, box_dims):
    # Check if the box fits in the EMS
    return all(d <= s for d, s in zip(box_dims, space.get_dimensions()))


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


# def fitness_function(chromosome):
#     """
#     Evaluate fitness based on the number of priority ULDs, volume utilization,
#     and penalties for unplaced boxes.
#     """
#     bps, cls = chromosome
#     packing_solution = best_match_placement(bps, cls)

#     if packing_solution is None:
#         # No valid packing solution for this chromosome
#         return float("-inf")  # Completely invalidate this chromosome

#     # Calculate packed volume
#     packed_volume = sum(box.get_volume() for box, *_ in packing_solution)
#     total_container_volume = sum(container.get_volume() for container in cls)
#     fill_ratio = packed_volume / total_container_volume

#     # Calculate penalties for unplaced boxes
#     unplaced_boxes = len(bps) - len(packing_solution)
#     penalty_unplaced_boxes = unplaced_boxes * 5  # Adjust penalty weight as needed

#     # Calculate number of priority ULDs
#     priority_ULDs = set()
#     for box, container, *_ in packing_solution:
#         if box.is_priority:
#             priority_ULDs.add(container)

#     penalty_priority_ULDs = len(priority_ULDs) * 20  # Assign a high penalty for each priority ULD

#     # Calculate fitness
#     fitness = fill_ratio - penalty_unplaced_boxes - penalty_priority_ULDs
#     return fitness


def fitness_function(chromosome):
    """
    Evaluate fitness based on the sum of costs of unplaced economy packages and priority ULDs.
    If any priority package is left unplaced, the fitness is set to -inf.
    """
    # from parser import get_K  # Import the function to get K from parser
    K = parser.get_K()  # Get the value of K

    bps, cls = chromosome
    packing_solution, unplaced_packages = best_match_placement(bps, cls)

    # Check if any priority package is unplaced
    if any(box.is_priority for box in unplaced_packages):
        return float(
            "-inf"
        )  # Invalidate the solution if a priority package is unplaced

    # Calculate penalties for unplaced economy packages based on their cost
    unplaced_economy_cost = sum(
        box.cost for box in unplaced_packages if not box.is_priority
    )
    penalty_unplaced_economy = unplaced_economy_cost  # Direct penalty based on cost

    # Calculate number of priority ULDs
    priority_ULDs = set()
    for box, container, *_ in packing_solution:
        if box.is_priority:
            priority_ULDs.add(container)

    penalty_priority_ULDs = len(priority_ULDs) * K  # Penalty per priority ULD using K

    # Fitness calculation
    fitness = -penalty_unplaced_economy - penalty_priority_ULDs
    return fitness


# Selection
def select_parents(population, fitness_scores, tournament_size=2, prob_t=0.85):
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
# def genetic_algorithm(pop_size, generations, mutation_rate=0.01, elitism_count=10):
#     """
#     Genetic Algorithm with Elitism to preserve the best solution across generations.
#     """
#     # Step 1: Initialize population
#     population = initialize_population(pop_size, packages, containers)

#     # Track the best solution
#     best_fitness = 0
#     best_solution = None

#     for generation in range(generations):
#         # Step 2: Evaluate fitness
#         fitness_scores = [fitness_function(chromosome) for chromosome in population]

#         # Find the best solution in the current generation
#         current_best_index = fitness_scores.index(max(fitness_scores))
#         current_best_fitness = fitness_scores[current_best_index]
#         current_best_solution = population[current_best_index]

#         # Update global best if a new best solution is found
#         if current_best_fitness > best_fitness:
#             best_fitness = current_best_fitness
#             best_solution = current_best_solution

#         print(f"Generation {generation + 1}: Best Fitness = {best_fitness}")

#         # Step 3: Selection
#         parents = select_parents(population, fitness_scores)

#         # Step 4: Crossover
#         next_generation = []
#         for i in range(0, len(parents), 2):
#             parent1 = parents[i]
#             parent2 = parents[i + 1 if i + 1 < len(parents) else 0]
#             child1 = crossover(parent1, parent2)
#             child2 = crossover(parent2, parent1)
#             next_generation.extend([child1, child2])

#         # Step 5: Mutation
#         next_generation = [mutate(chromosome, mutation_rate) for chromosome in next_generation]

#         # Step 6: Apply Elitism
#         next_generation = sorted(next_generation, key=lambda chromo: fitness_function(chromo), reverse=True)
#         if elitism_count > 0:
#             elites = sorted(population, key=lambda chromo: fitness_function(chromo), reverse=True)[:elitism_count]
#             next_generation[-elitism_count:] = elites

#         # Replace old population with the new one
#         population = next_generation[:pop_size]

#     # Step 7: Return the best solution found
#     return best_solution


def genetic_algorithm(pop_size, generations, mutation_rate=0.1, elitism_count=1):
    """
    Genetic Algorithm with a simplified fitness function.
    """
    # Initialize population
    population = initialize_population(pop_size, packages, containers)

    # Track the best solution
    best_solution = population[0]
    best_fitness = fitness_function(best_solution)

    for generation in range(generations):
        # Evaluate fitness for the population
        fitness_scores = [fitness_function(chromosome) for chromosome in population]

        # Find the best chromosome in the current generation
        current_best_index = fitness_scores.index(max(fitness_scores))
        current_best_fitness = fitness_scores[current_best_index]
        current_best_solution = population[current_best_index]

        # Update the global best solution
        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_solution = current_best_solution

        print(f"Generation {generation + 1}: Best Fitness = {best_fitness}")

        # Selection, crossover, mutation, and elitism logic
        parents = select_parents(population, fitness_scores)
        next_generation = []
        for i in range(0, len(parents), 2):
            parent1 = parents[i]
            parent2 = parents[i + 1 if i + 1 < len(parents) else 0]
            child1 = crossover(parent1, parent2)
            child2 = crossover(parent2, parent1)
            next_generation.extend([child1, child2])

        next_generation = [
            mutate(chromosome, mutation_rate) for chromosome in next_generation
        ]
        elites = sorted(
            population, key=lambda chromo: fitness_function(chromo), reverse=True
        )[:elitism_count]
        next_generation[-elitism_count:] = elites
        population = next_generation[:pop_size]

    return best_solution


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


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def plot_packing_solution_subplots(packing_solution, containers):
    """
    Visualize the packing solution in 3D using subplots for all containers.
    Priority packages are colored red, and economy packages are colored blue.
    """
    num_containers = len(containers)
    cols = min(3, num_containers)  # Up to 3 columns
    rows = (num_containers + cols - 1) // cols  # Calculate rows needed

    fig = plt.figure(figsize=(5 * cols, 5 * rows))

    for idx, container in enumerate(containers):
        # Create a subplot for each container
        ax = fig.add_subplot(rows, cols, idx + 1, projection="3d")

        # Set container dimensions
        container_dims = (container.dim.l, container.dim.w, container.dim.h)
        ax.set_xlim([0, container_dims[0]])
        ax.set_ylim([0, container_dims[1]])
        ax.set_zlim([0, container_dims[2]])
        ax.set_xlabel("Length")
        ax.set_ylabel("Width")
        ax.set_zlabel("Height")
        ax.set_title(f"Container {container.id}")
        # print(len(packing_solution[0]))
        # Plot each box in the container
        for box, cont, coords, orientation in packing_solution:
            if cont != container:
                continue  # Skip boxes not placed in this container

            # Determine color based on priority
            color = "red" if box.is_priority else "blue"

            # Box corners
            x0, y0, z0 = coords
            x1 = x0 + orientation[0]
            y1 = y0 + orientation[1]
            z1 = z0 + orientation[2]

            # Define the vertices of the box
            vertices = [
                [x0, y0, z0],
                [x1, y0, z0],
                [x1, y1, z0],
                [x0, y1, z0],  # Bottom face
                [x0, y0, z1],
                [x1, y0, z1],
                [x1, y1, z1],
                [x0, y1, z1],  # Top face
            ]

            # Define the 6 faces of the box
            faces = [
                [vertices[0], vertices[1], vertices[5], vertices[4]],  # Front face
                [vertices[1], vertices[2], vertices[6], vertices[5]],  # Right face
                [vertices[2], vertices[3], vertices[7], vertices[6]],  # Back face
                [vertices[3], vertices[0], vertices[4], vertices[7]],  # Left face
                [vertices[0], vertices[1], vertices[2], vertices[3]],  # Bottom face
                [vertices[4], vertices[5], vertices[6], vertices[7]],  # Top face
            ]

            # Create a 3D polygon for the box
            ax.add_collection3d(
                Poly3DCollection(
                    faces,
                    facecolors=color,
                    edgecolors="black",
                    linewidths=0.5,
                    alpha=0.7,
                )
            )

            # Annotate the box with its ID
            ax.text(
                x0 + orientation[0] / 2,
                y0 + orientation[1] / 2,
                z0 + orientation[2] / 2,
                f"{box.id}",
                color="white",
                ha="center",
                va="center",
                fontsize=10,
            )

    # Adjust layout to avoid overlap
    plt.tight_layout()
    plt.show()


# Set an initial default solution
best_solution = initialize_population(1, packages, containers)[
    0
]  # First random chromosome
best_fitness = 0


# Run the GA
best_solution = genetic_algorithm(
    pop_size=50, generations=15 * len(pkg_list), mutation_rate=0.01
)

# Generate packing solution for the best chromosome
bps, cls = best_solution
packing_solution = best_match_placement(bps, cls)[0]

# Calculate and print packing fraction
if packing_solution:
    packed_volume = sum(box.get_volume() for box, _, _, _ in packing_solution)
    total_container_volume = sum(container.get_volume() for container in containers)
    packing_fraction = (
        packed_volume / total_container_volume if total_container_volume > 0 else 0
    )
    print(f"Packing Fraction: {packing_fraction:.2%}")

if packing_solution is not None:
    plot_packing_solution_subplots(packing_solution, containers)
else:
    print("No feasible packing solution found.")

# Output the solution to a file
output_placement_to_file(packing_solution, bps, output_file="placement_output.txt")
print("Placement solution written to 'placement_output.txt'")
