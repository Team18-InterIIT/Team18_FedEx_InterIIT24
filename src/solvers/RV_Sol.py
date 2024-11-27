import random
import math
from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment
from  collections import deque

class LPBinPacking(PackingAlgorithm):
    def __init__(self, M=10000, initial_temperature=1000, alpha=0.1, beta=0.1):
        self.M = M  # Big-M constant for constraints
        self.initial_temperature = initial_temperature  # Starting temperature
        self.alpha = alpha  # Heating parameter
        self.beta = beta  # Cooling parameter

    def solve(self, env: Environment):
        """
        Solves the 3D bin-packing problem using simulated annealing.
        """

        n = len(env.packages)
        if not env.ULDs:
          print("No ULDs available in the Environment")
        
        container = env.ULDs[0]
        W, H, D = container.dim.l, container.dim.w, container.dim.h
        
        # Initialize the sequence triple (A, B, C) and R
        def initialize_sequence_triple(n):
            """Initialize random sequence triple (A, B, C, R)"""
            sequence = list(range(n))
            random.shuffle(sequence)
            R = [random.randint(1, 6) for _ in range(n)]  # Generate random values for R, 1 to 6 inclusive
            return sequence, sequence[:], sequence[:], R
        
        def topological_sort_indegree(graph):
            """Topological sorting on a directed acyclic graph (DAG) using in-degrees."""
            in_degree = {node: 0 for node in graph}
            for node in graph:
                for neighbor in graph[node]:
                    in_degree[neighbor] += 1

            queue = deque([node for node in graph if in_degree[node] == 0])
            topo_order = []

            while queue:
                node = queue.popleft()
                topo_order.append(node)

                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

            if len(topo_order) != len(graph):
               print("Graph contains a cycle; topological sorting not possible.")

            return topo_order

        # Constructing the constraint graphs based on the sequence triples
        def construct_constraint_graph(sequence_triple, boxes):
            print("Hello!")
            """Construct the constraint graphs from sequence triples."""
            A, B, C = sequence_triple
            n = len(boxes)
            graph_x = {i: [] for i in range(n)}  # Dependency graph for x-axis
            graph_y = {i: [] for i in range(n)}  # Dependency graph for y-axis
            graph_z = {i: [] for i in range(n)}  # Dependency graph for z-axis

            for i in range(n):
                for j in range(i + 1, n):
                    if i != j:
                        # A_i_j (Left) constraint
                        if A.index(i) < A.index(j) and B.index(j) < B.index(i) and C.index(j) < C.index(i):
                            graph_x[i].append(j)

                        # B_i_j (Below) constraint
                        if A.index(j) < A.index(i) and B.index(j) < B.index(i) and C.index(i) < C.index(j):
                            graph_y[i].append(j)

                        # C_i_j (Behind) constraint
                        if (A.index(j) < A.index(i) and B.index(j) < B.index(i) and C.index(j) < C.index(i)) or \
                           (A.index(i) < A.index(j) and B.index(j) < B.index(i) and C.index(i) < C.index(j)):
                            graph_z[i].append(j)
            
            topo_x = topological_sort_indegree(graph_x)
            topo_y = topological_sort_indegree(graph_y)
            topo_z = topological_sort_indegree(graph_z)
            
            print("OID")
            return topo_x, topo_y, topo_z

        def assign_coordinates(boxes, knapsack, R):
            """Assign coordinates to boxes using the topological orders."""
            n = len(boxes)
            corners = {}
            
            topo_x, topo_y, topo_z = construct_constraint_graph((A, B, C), boxes)

            # Initialize coordinates for each box
            positions = [[0, 0, 0] for _ in range(n)]  # [x, y, z] positions of the boxes

            # Apply transformations based on R (Box rotations)
            for i in range(len(boxes)):
                print(boxes[i].dim.l, " ",boxes[i].dim.w, " ",boxes[i].dim.h, " ")
                if R[i] == 1:
                    continue  # No change
                elif R[i] == 2:
                    boxes[i].dim.l, boxes[i].dim.w = boxes[i].dim.w, boxes[i].dim.l
                elif R[i] == 3:
                    boxes[i].dim.l, boxes[i].dim.h = boxes[i].dim.h, boxes[i].dim.l
                elif R[i] == 4:
                    boxes[i].dim.w, boxes[i].dim.h = boxes[i].dim.h, boxes[i].dim.w
                elif R[i] == 5:
                    boxes[i].dim.l, boxes[i].dim.w = boxes[i].dim.w, boxes[i].dim.l
                elif R[i] == 6:
                    boxes[i].dim.l, boxes[i].dim.h = boxes[i].dim.h, boxes[i].dim.l
            
            # Assign positions based on topological orders
            for i in B:  # Process boxes in the order defined by B-chain
                max_x = max([positions[j][0] + boxes[j].dim.l for j in range(n) if topo_x.index(i) > topo_x.index(j)], default=0)
                max_y = max([positions[j][1] + boxes[j].dim.w for j in range(n) if topo_y.index(i) > topo_y.index(j)], default=0)
                max_z = max([positions[j][2] + boxes[j].dim.h for j in range(n) if topo_z.index(i) > topo_z.index(j)], default=0)

                # Ensure box `i` fits within the knapsack
                if max_x + boxes[i].dim.l <= knapsack.dim.l and \
                    max_y + boxes[i].dim.w <= knapsack.dim.w and \
                    max_z + boxes[i].dim.h <= knapsack.dim.h:
                        positions[i] = [max_x, max_y, max_z]
                else:
                    print("1")
                # If the box exceeds knapsack, try placing it in the next most optimal position
                    found_valid_position = False
                    for x in range(W - boxes[i].dim.l + 1):
                        for y in range(H - boxes[i].dim.w + 1):
                            for z in range(D - boxes[i].dim.h + 1):
                                # Check if the box at [x, y, z] overlaps with any already placed box
                                if not any(
                                    (positions[j][0] < x + boxes[i].dim.l and
                                    positions[j][0] + boxes[j].dim.l > x and
                                    positions[j][1] < y + boxes[i].dim.w and
                                    positions[j][1] + boxes[j].dim.w > y and
                                    positions[j][2] < z + boxes[i].dim.h and
                                    positions[j][2] + boxes[j].dim.h > z)
                                    for j in range(n)
                                ):
                                    positions[i] = [x, y, z]
                                    found_valid_position = True
                                    break
                            if found_valid_position:
                                break
                        if found_valid_position:
                            break
                    print("1^")
                
                    # If no valid position is found within the knapsack, raise an error or handle the case
                    if not found_valid_position:
                        print(f"Box {i} could not be placed in the knapsack. No valid position found.")
                print("exit")
                corner1 = Point(positions[i][0],positions[i][1],positions[i][2])  # Lower-bottom-left corner
                corner2 = Point(
                    positions[i][0] + boxes[i].dim.l,
                    positions[i][1] + boxes[i].dim.w,
                    positions[i][2] + boxes[i].dim.h,
                )  # Upper-top-right corner

                corners[i] = corner1, corner2
            print("meow")
            return corners


        def generate_neighbourhood(state):
            """
            Generate a list of neighboring solutions by swapping boxes in sequences
            and rotating them.
            """
            A, B, C, R = state  # Current sequences and rotation values
            n = len(A)
            neighbours = []

            # Swap two boxes within the same sequence A, B, or C
            for sequence in [A, B, C]:
                new_sequence = sequence[:]
                i, j = random.sample(range(n), 2)
                new_sequence[i], new_sequence[j] = new_sequence[j], new_sequence[i]  # Swap two boxes
                neighbours.append((new_sequence, B[:], C[:], R[:]))
                neighbours.append((A[:], new_sequence, C[:], R[:]))
                neighbours.append((A[:], B[:], new_sequence, R[:]))

            # Randomly change one rotation in R
            random_index = random.randint(0, n - 1)
            new_R = R[:]
            original_rotation = new_R[random_index]
            new_rotation = random.randint(1, 6)
            while new_rotation == original_rotation:  # Ensure a different rotation
                new_rotation = random.randint(1, 6)
            new_R[random_index] = new_rotation
            neighbours.append((A[:], B[:], C[:], new_R))

            return neighbours


        def simulated_annealing(boxes, knapsack, initial_temperature, alpha, beta):
            """
            Simulated annealing loop to solve the 3D bin-packing problem.
            """
            n = len(boxes)

            # Initialize the state
            A, B, C, R = initialize_sequence_triple(n)
            best_state = (A, B, C, R)
            current_state = (A, B, C, R)

            # Compute initial positions and evaluate cost
            best_positions = assign_coordinates(boxes, knapsack, R)
            for i, box in enumerate(boxes):
                corner1, corner2 = best_positions[i]
                env.add_package(box, knapsack, (corner1, corner2))

            best_volume = env.cost()[0]+env.cost()[1]
            current_volume = best_volume

            # Simulated annealing parameters
            temperature = initial_temperature
            iterations_without_improvement = 0

            while temperature > 0.1 and iterations_without_improvement < 10:
                # Generate neighbors
                neighbours = generate_neighbourhood(current_state)

                # Pick a random neighbor
                neighbour = random.choice(neighbours)
                A_new, B_new, C_new, R_new = neighbour

                # Reset the env for the neighbor
                env.reset()

                # Assign coordinates for the neighbor
                new_positions = assign_coordinates(boxes, knapsack, R_new)
                for i, box in enumerate(boxes):
                    corner1, corner2 = new_positions[i]
                    env.add_package(box, knapsack, (corner1, corner2))

                # Evaluate the neighbor's cost
                neighbour_volume = env.cost()[0]+env.cost()[1]

                # Decide whether to accept the neighbor
                found_better = False
                if neighbour_volume > current_volume:
                    found_better = True
                else:
                    # Accept a worse solution with some probability
                    delta = (current_volume - neighbour_volume) / current_volume
                    if random.random() < math.exp(-delta / temperature):
                        found_better = True

                if found_better:
                    current_state = neighbour
                    current_volume = neighbour_volume
                    iterations_without_improvement = 0  # Reset the counter

                    # Update the best state if the neighbor is better
                    if neighbour_volume > best_volume:
                        best_state = neighbour
                        best_volume = neighbour_volume
                else:
                    iterations_without_improvement += 1

                # Decrease temperature
                temperature = temperature / (1 + beta * temperature)

            # Return the best configuration found
            return best_state

        A, B, C, R = initialize_sequence_triple(n)
        # Call Simulated Annealing on the current state
        box = env.packages
        final_positions = simulated_annealing(box, container, self.initial_temperature, self.alpha, self.beta)
        
        # Return the final state
        return final_positions
