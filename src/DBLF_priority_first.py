import parser
import itertools
import random
from entity import Package, ULD, Dim

# # Initialize data
# K = parser.get_K()
# uld_list = parser.get_uld_list()
# pkg_list = parser.get_pkg_list()

# # Create ULD and Package objects
# containers_all = [ULD(row) for row in uld_list]
# packages_all_okay = [Package(row) for row in pkg_list]
# packages_priority_all = [Package(pkg) for pkg in pkg_list if pkg[5] == "Priority"]
# packages_economy_all = [Package(pkg) for pkg in pkg_list if pkg[5] != "Priority"]


def dblf_packing_algorithm(packages, ulds):
    # Initialize position sets for each ULD
    position_sets = {uld.id: [(0, 0, 0)] for uld in ulds}
    # packages_priority = [Package(pkg) for pkg in pkg_list if pkg[5] == "Priority"]
    # packages_economy = [Package(pkg) for pkg in pkg_list if pkg[5] != "Priority"]
    packages_priority = [pkg for pkg in packages if pkg.is_priority]
    packages_economy = [pkg for pkg in packages if not pkg.is_priority]

    # print(packages_economy)
    # packages_economy = []
    # packages_priority = []
    # for pkg in packages:
    #     if pkg.is_priority: packages_priority.append(pkg)
    #     else: packages_economy.append(pkg)
    # packages = packages_all.copy()

    # Sort packages by volume (or another criterion)
    # packages_prioity_sorted = sorted(
    #     packages_priority, key=lambda pkg: pkg.volume(), reverse=True
    # )
    # packages_economy_sorted = sorted(
    #     packages_economy, key=lambda pkg: pkg.cost, reverse=True
    # )
    # packages_order = packages_prioity_sorted + packages_economy_sorted

    # ulds = sorted(ulds, key=lambda pkg: pkg.volume(), reverse=True)
    packages_order  = packages_priority + packages_economy
    # print(packages_order) => Has coordinates, so problem is with this

    # print(packages_priority[0].corners, packages_order[0].corners)
    # print(packages[0].corners)

    for package in packages_order:
        packed = False
        for uld in ulds:
            for position in position_sets[uld.id]:
                if can_place(package, position, uld):
                    # Pack the package
                    package.uld_id = uld.id
                    package.corners = (
                        position,
                        (
                            position[0] + package.dim.l,
                            position[1] + package.dim.w,
                            position[2] + package.dim.h,
                        ),
                    )
                    uld.packages.append(package)
                    uld.weight += package.weight
                    if package.is_priority: uld.has_priority = True

                    # Update the position set
                    position_sets[uld.id] = update_positions(
                        position_sets[uld.id], package, position, uld
                    )
                    packed = True
                    break
            if packed:
                break
        # if not packed:
        #     print(f"Package {package.id} could not be packed.")

    # Clearing the lists
    # position_sets.clear()
    # packages_priority.clear()
    # packages_economy.clear()

    # Deleting the lists
    # del position_sets
    # del packages_priority
    # del packages_economy

    # print(ulds)
    return ulds, packages_order


def can_place(package, position, uld):
    """Check if the package can be placed at the given position in the ULD."""
    x, y, z = position
    if (
        x + package.dim.l > uld.dim.l
        or y + package.dim.w > uld.dim.w
        or z + package.dim.h > uld.dim.h
    ):
        return False

    if uld.weight + package.weight > uld.weight_limit:
        return False

    for placed_pkg in uld.packages:
        if is_overlapping(
            package,
            (x, y, z, x + package.dim.l, y + package.dim.w, z + package.dim.h),
            placed_pkg.corners,
        ):
            return False

    return True


def is_overlapping(package, new_coords, existing_coords):
    """Check if the new package placement overlaps with an existing package."""
    nx1, ny1, nz1, nx2, ny2, nz2 = new_coords
    ex1, ey1, ez1, ex2, ey2, ez2 = existing_coords[0] + existing_coords[1]

    return not (
        nx2 <= ex1 or nx1 >= ex2 or ny2 <= ey1 or ny1 >= ey2 or nz2 <= ez1 or nz1 >= ez2
    )


def update_positions(position_set, package, position, uld):
    """Update the position set after placing a package."""
    x, y, z = position
    l, w, h = package.dim.l, package.dim.w, package.dim.h

    new_positions = [
        (x + l, y, z),  # Right
        (x, y + w, z),  # Forward
        (x, y, z + h),  # Upward
    ]

    # Keep positions inside the ULD boundaries
    return [
        pos
        for pos in position_set + new_positions
        if pos[0] < uld.dim.l and pos[1] < uld.dim.w and pos[2] < uld.dim.h
    ]


# def output_results_unique(ulds, packages, output_file="results.txt"):
#     """
#     Outputs the results of the packing, ensuring each package is printed only once.
#     1. The first line contains total packed volume, total packed weight, and the total number of packed boxes.
#     2. Subsequent lines provide details for each package.

#     :param ulds: List of ULDs after packing.
#     :param packages: List of all packages.
#     :param output_file: Output file for writing the results.
#     """

#     with open(output_file, "w") as file:
#         # Calculate totals
#         total_packed_volume = sum(
#             pkg.volume() for uld in ulds for pkg in uld.packages
#         )
#         total_packed_weight = sum(uld.weight for uld in ulds)
#         total_packed_boxes = sum(len(uld.packages) for uld in ulds)
#         total_packed_priority_boxes = sum(
#             1 for uld in ulds for package in uld.packages if package.is_priority
#         )
#         # Track placed packages
#         placed_packages = [pkg for uld in ulds for pkg in uld.packages]
#         # Calculate unplaced boxes
#         unplaced_boxes = [
#             pkg
#             for pkg in packages_economy_all
#             if pkg.id not in [p.id for p in placed_packages]
#         ]
#         # Step 1: Calculate the number of containers with at least one priority package
#         k = sum(1 for uld in ulds if any(pkg.is_priority for pkg in uld.packages))

#         # Step 2: Sum the cost of unplaced non-priority boxes
#         unplaced_non_priority_cost = sum(
#             pkg.cost for pkg in unplaced_boxes if not pkg.is_priority
#         )

#         # Step 3: Calculate total cost
#         total_cost = 5000 * k + unplaced_non_priority_cost
#         # Write the first line
#         file.write(
#             f"{total_cost},{total_packed_weight},{total_packed_boxes},{total_packed_priority_boxes} \n"
#         )

#         # Write details for each package
#         for pkg in packages_all_okay:
#             if pkg.uld_id == 0:
#                 # Unplaced package
#                 file.write(f"P-{pkg.id},NONE,-1,-1,-1,-1,-1,-1\n")
#             else:
#                 # Placed package
#                 x0, y0, z0 = pkg.corners[0]
#                 x1, y1, z1 = pkg.corners[1]
#                 file.write(f"P-{pkg.id},U-{pkg.uld_id},{x0},{y0},{z0},{x1},{y1},{z1}\n")

#     print(f"Results written to {output_file}")


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def visualize_packing(containers):
    """
    Visualize the packing of boxes into ULD containers using 3D plots.
    Each subplot corresponds to one ULD container.
    """
    num_containers = len(containers)
    cols = min(3, num_containers)  # Up to 3 columns
    rows = (num_containers + cols - 1) // cols  # Calculate rows needed

    fig = plt.figure(figsize=(5 * cols, 5 * rows))

    for idx, uld in enumerate(containers):
        ax = fig.add_subplot(rows, cols, idx + 1, projection="3d")

        # Set container dimensions
        ax.set_xlim([0, uld.dim.l])
        ax.set_ylim([0, uld.dim.w])
        ax.set_zlim([0, uld.dim.h])
        ax.set_xlabel("Length")
        ax.set_ylabel("Width")
        ax.set_zlabel("Height")
        ax.set_title(f"ULD {uld.id}")

        # Plot each package in the container
        for package in uld.packages:
            x0, y0, z0 = package.corners[0]
            x1, y1, z1 = package.corners[1]

            # Define vertices of the box
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
                [vertices[0], vertices[1], vertices[5], vertices[4]],  # Front
                [vertices[1], vertices[2], vertices[6], vertices[5]],  # Right
                [vertices[2], vertices[3], vertices[7], vertices[6]],  # Back
                [vertices[3], vertices[0], vertices[4], vertices[7]],  # Left
                [vertices[0], vertices[1], vertices[2], vertices[3]],  # Bottom
                [vertices[4], vertices[5], vertices[6], vertices[7]],  # Top
            ]

            # Choose color based on priority
            color = "red" if package.is_priority else "blue"

            # Add the box to the plot
            ax.add_collection3d(
                Poly3DCollection(faces, facecolors=color, edgecolors="black", alpha=0.7)
            )

            # Annotate the box with its ID
            ax.text(
                x0 + (x1 - x0) / 2,
                y0 + (y1 - y0) / 2,
                z0 + (z1 - z0) / 2,
                f"{package.id}",
                color="red",
                ha="center",
                va="center",
            )

    plt.tight_layout()
    plt.show()


def calculate_packing_stats(containers):
    """
    Calculate the packing fraction and the number of boxes packed.
    Args:
        containers (list): List of ULD objects after packing.
    Returns:
        packing_fraction (float): Ratio of packed volume to total container volume.
        total_packed_boxes (int): Total number of boxes packed across all containers.
    """
    total_packed_volume = 0
    total_container_volume = 0
    total_packed_boxes = 0

    for container in containers:
        # Add container volume
        total_container_volume += container.volume()

        # Add volumes of packed boxes and count them
        for package in container.packages:
            total_packed_volume += package.volume()
            total_packed_boxes += 1

    # Calculate packing fraction
    packing_fraction = (
        total_packed_volume / total_container_volume
        if total_container_volume > 0
        else 0
    )

    return packing_fraction, total_packed_boxes

# # Run the DBLF Algorithm
# result_uld, result_packages = dblf_packing_algorithm(packages_all_okay, containers_all)

# # # Assuming `result_uld` is the list of ULDs after packing
# output_results_unique(result_uld, result_packages)


# # Assuming `result_uld` is the list of ULDs after packing and `total_packed_volume` is calculated
# total_packed_boxes = sum(len(uld.packages) for uld in result_uld)
# total_packed_volume = sum(
#     pkg.volume() for uld in result_uld for pkg in uld.packages
# )

# # Example usage:
# # Call this function after running the packing algorithm.
# packing_fraction, total_packed_boxes = calculate_packing_stats(result_uld)

# print(f"Packing Fraction: {packing_fraction:.2%}")
# print(f"Total Number of Boxes Packed: {total_packed_boxes}")


# # # calculate_packing_stats(result_uld)
# visualize_packing(result_uld)  # plotting the package



